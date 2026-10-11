#!/usr/bin/env python3
"""
Simpan content plan PeopleSync ke CSV dan kirim ke topik Telegram untuk direview.
Hanya pakai standard library.

    save_plan.py add batch.json [--send]          tambah/timpa baris (berdasarkan id)
    save_plan.py status CP-1,CP-2 "Approved" [--note "..."] [--send]
    save_plan.py show [--status "Menunggu review SML"]
    save_plan.py send                             kirim file CSV ke Telegram
    save_plan.py detail CP-1,CP-2                 tampilkan ringkasan konten (skor, hook, catatan) di topik reviewer
    save_plan.py detail --status "Menunggu review SML"
    save_plan.py sheet                            kirim ulang semua baris ke Google Sheets
    save_plan.py ping                             kirim pesan tes ke topik review dan topik reviewer
    save_plan.py notify "teks" | @file.txt       kirim laporan/eskalasi ke topik review
    save_plan.py notify --to reviewer @file.txt   kirim hasil pemeriksaan ke topik reviewer

Konfigurasi: ~/hermes-data/content-plan/config.env
    REVIEW_CHAT_ID=-100...
    REVIEW_THREAD_ID=5          topik Content Planning (laporan akhir + CSV untuk SML)
    REVIEWER_THREAD_ID=9        topik Content Reviewer (hasil pemeriksaan tiap putaran), opsional
    SHEET_WEBHOOK_URL=https://script.google.com/macros/s/.../exec   opsional, lihat references/google-sheet-webhook.gs
    SHEET_TOKEN=...             sama dengan TOKEN di Apps Script
Kalau SHEET_WEBHOOK_URL diisi, setiap `add` dan `status` ikut memperbarui Google Sheets.
Token bot diambil dari TELEGRAM_BOT_TOKEN di ~/.hermes/.env (atau environment).
"""
import argparse
import csv
import datetime
import json
import os
import sys
import time
import uuid
import urllib.request
from pathlib import Path

DATA_DIR = Path.home() / "hermes-data" / "content-plan"
CSV_PATH = DATA_DIR / "peoplesync_content_plan.csv"
CONFIG_PATH = DATA_DIR / "config.env"

FIELDS = [
    "id", "tanggal_tayang", "platform", "format", "pilar", "funnel", "judul_hook",
    "pesan_utama", "outline", "cta", "keyword", "negara_bahasa", "search_intent", "meta_title",
    "meta_description", "slug", "faq", "sumber_klaim", "naskah", "skor_checker", "skor_seo",
    "skor_slop", "skor_ai", "catatan_checker", "revisi_ke", "status", "catatan_sml", "diperbarui",
]


def read_env(path):
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def load_rows():
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_rows(rows):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows.sort(key=lambda r: (r.get("tanggal_tayang", ""), r.get("id", "")))
    tmp = CSV_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:  # BOM agar Excel membaca UTF-8
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    tmp.replace(CSV_PATH)


def sync_sheet():
    """Cerminkan seluruh CSV ke Google Sheets. Gagal kirim tidak membatalkan penyimpanan CSV."""
    cfg = tg_config()
    url, token = cfg.get("SHEET_WEBHOOK_URL"), cfg.get("SHEET_TOKEN")
    if not url:
        return
    rows = [{k: r.get(k, "") for k in FIELDS} for r in load_rows()]
    req = urllib.request.Request(
        url,
        data=json.dumps({"token": token, "fields": FIELDS, "rows": rows}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            hasil = json.loads(resp.read())
        if hasil.get("ok"):
            print(f"OK Google Sheets diperbarui (baru: {hasil.get('baru')}, diperbarui: {hasil.get('diperbarui')})")
        else:
            print(f"WARN Google Sheets menolak: {hasil.get('error')}")
    except Exception as e:
        print(f"WARN gagal kirim ke Google Sheets: {e}")


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def cmd_add(path, force=False):
    src = Path(path).expanduser()
    if not src.exists():
        sys.exit(f"ERROR file batch tidak ada: {src}")
    umur_menit = (datetime.datetime.now().timestamp() - src.stat().st_mtime) / 60
    if umur_menit > 30 and not force:
        sys.exit(f"ERROR file batch sudah {umur_menit:.0f} menit, kemungkinan sisa run lama. "
                 "Tulis batch baru, atau pakai --force kalau memang sengaja.")
    batch = json.loads(src.read_text(encoding="utf-8"))
    if isinstance(batch, dict):
        batch = batch.get("items") or batch.get("rows") or [batch]
    rows = {r["id"]: r for r in load_rows()}
    baru, diperbarui, ids = 0, 0, []
    for item in batch:
        if not item.get("id"):
            print(f"SKIP baris tanpa id: {item}", file=sys.stderr)
            continue
        item = {k: ("" if v is None else str(v)) for k, v in item.items()}
        item.setdefault("status", "Menunggu review SML")
        item["diperbarui"] = now()
        if item["id"] in rows:
            diperbarui += 1
        else:
            baru += 1
        rows[item["id"]] = {**rows.get(item["id"], {}), **item}
        ids.append(item["id"])
    save_rows(list(rows.values()))
    print(f"OK {baru + diperbarui} baris disimpan ke {CSV_PATH} (baru: {baru}, diperbarui: {diperbarui}, id: {', '.join(ids)})")
    return ids


def cmd_status(ids, status, note):
    targets = {i.strip() for i in ids.split(",") if i.strip()}
    rows = load_rows()
    found = set()
    for r in rows:
        if r["id"] in targets:
            r["status"] = status
            if note is not None:
                r["catatan_sml"] = note
            r["diperbarui"] = now()
            found.add(r["id"])
    save_rows(rows)
    missing = targets - found
    print(f"OK status '{status}' untuk {len(found)} baris" + (f". Tidak ditemukan: {', '.join(sorted(missing))}" if missing else ""))


def cmd_show(status):
    rows = [r for r in load_rows() if not status or r.get("status") == status]
    for r in rows:
        print(f"{r['id']} | {r['tanggal_tayang']} | {r['platform']} | {r['funnel']} | {r['status']} | {r['judul_hook']}")
    print(f"Total: {len(rows)}")


def send_document(caption):
    cfg = tg_config()
    token, chat = cfg.get("TELEGRAM_BOT_TOKEN"), cfg.get("REVIEW_CHAT_ID")
    if not token or not chat:
        print("WARN TELEGRAM_BOT_TOKEN atau REVIEW_CHAT_ID belum diset, file tidak dikirim")
        return
    if not CSV_PATH.exists():
        print("WARN file CSV belum ada")
        return
    boundary = uuid.uuid4().hex
    fields = {"chat_id": chat, "caption": caption}
    if cfg.get("REVIEW_THREAD_ID"):
        fields["message_thread_id"] = cfg["REVIEW_THREAD_ID"]
    body = b""
    for k, v in fields.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    body += (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"{CSV_PATH.name}\"\r\n"
        "Content-Type: text/csv\r\n\r\n"
    ).encode() + CSV_PATH.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendDocument",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            ok = json.loads(resp.read()).get("ok")
        print("OK file terkirim ke Telegram" if ok else "WARN Telegram menolak kiriman")
    except Exception as e:
        print(f"WARN gagal kirim ke Telegram: {e}")


def tg_config():
    return {**read_env(Path.home() / ".hermes" / ".env"), **read_env(CONFIG_PATH), **os.environ}


def send_text(text, to="review"):
    cfg = tg_config()
    token, chat, thread = cfg.get("TELEGRAM_BOT_TOKEN"), cfg.get("REVIEW_CHAT_ID"), cfg.get("REVIEW_THREAD_ID")
    if to == "reviewer":  # tanpa topik reviewer, hasil pemeriksaan ikut ke topik review
        thread = cfg.get("REVIEWER_THREAD_ID") or thread
    if not token or not chat:
        print("WARN TELEGRAM_BOT_TOKEN atau REVIEW_CHAT_ID belum diset")
        return False
    semua_ok = True
    for bagian in potong(text):
        data = {"chat_id": chat, "text": bagian}
        if thread:
            data["message_thread_id"] = thread
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                ok = json.loads(resp.read()).get("ok")
            print("OK pesan terkirim ke Telegram" if ok else "WARN Telegram menolak kiriman")
            semua_ok = semua_ok and bool(ok)
        except Exception as e:
            print(f"WARN gagal kirim ke Telegram: {e}")
            semua_ok = False
    return semua_ok


def potong(text, batas=3900):
    """Pecah teks panjang di batas baris; Telegram menolak pesan di atas 4096 karakter."""
    while len(text) > batas:
        i = text.rfind("\n", 0, batas)
        if i < batas // 2:
            i = batas
        yield text[:i]
        text = text[i:].lstrip("\n")
    yield text


HARI = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
# Ringkasan saja. Naskah, FAQ, dan field meta dibaca di CSV atau Google Sheets.
RINCIAN = [
    ("Hook", "judul_hook"), ("Pesan utama", "pesan_utama"), ("Keyword", "keyword"), ("CTA", "cta"),
    ("Catatan reviewer", "catatan_checker"), ("Catatan SML", "catatan_sml"),
]


def format_detail(r):
    def isi(k):
        v = (r.get(k) or "").strip()
        return "" if v == "-" else v

    try:
        t = datetime.date.fromisoformat(r.get("tanggal_tayang", ""))
        tgl = f"{HARI[t.weekday()]} {t.day:02d}/{t.month:02d}"
    except ValueError:
        tgl = isi("tanggal_tayang") or "-"
    baris = [
        f"{r['id']} · {tgl} · {isi('platform')} {isi('format')} · {isi('funnel')}",
        f"{isi('status') or '-'} · skor {isi('skor_checker') or '-'} · SEO {isi('skor_seo') or '-'} · "
        f"slop {isi('skor_slop') or '-'} · AI {isi('skor_ai') or '-'} · putaran {isi('revisi_ke') or '-'}",
    ]
    baris += [f"{label}: {isi(k)}" for label, k in RINCIAN if isi(k)]
    return "\n".join(baris)


def send_detail(ids=None, status=None):
    """Satu pesan ringkasan per konten ke topik reviewer."""
    rows = [r for r in load_rows() if (ids is None or r["id"] in ids) and (not status or r.get("status") == status)]
    if not rows:
        print("WARN tidak ada baris yang cocok untuk ditampilkan")
        return
    for r in rows:
        send_text(format_detail(r), to="reviewer")
        time.sleep(1)  # jaga batas kirim Telegram untuk grup
    print(f"OK detail {len(rows)} konten dikirim ke topik reviewer")


def send_ping():
    cfg = tg_config()
    send_text(f"Tes: file review Content Planning akan dikirim ke topik ini (thread {cfg.get('REVIEW_THREAD_ID') or '-'}).")
    if cfg.get("REVIEWER_THREAD_ID"):
        send_text(f"Tes: hasil pemeriksaan reviewer akan dikirim ke topik ini (thread {cfg['REVIEWER_THREAD_ID']}).", to="reviewer")


def caption_ringkas():
    rows = load_rows()
    menunggu = sum(r.get("status") == "Menunggu review SML" for r in rows)
    approved = sum(r.get("status") == "Approved" for r in rows)
    return f"Content plan PeopleSync. Menunggu review: {menunggu}, Approved: {approved}, Total: {len(rows)}"


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("json_file"); a.add_argument("--send", action="store_true")
    a.add_argument("--force", action="store_true")
    s = sub.add_parser("status"); s.add_argument("ids"); s.add_argument("status")
    s.add_argument("--note"); s.add_argument("--send", action="store_true")
    sh = sub.add_parser("show"); sh.add_argument("--status")
    sub.add_parser("send")
    sub.add_parser("sheet")
    d = sub.add_parser("detail"); d.add_argument("ids", nargs="?"); d.add_argument("--status")
    sub.add_parser("ping")
    n = sub.add_parser("notify"); n.add_argument("text", help="teks pesan, atau @path/file.txt")
    n.add_argument("--to", choices=["review", "reviewer"], default="review")
    args = p.parse_args()

    if args.cmd == "notify":
        t = args.text
        if t.startswith("@"):
            t = Path(t[1:]).expanduser().read_text(encoding="utf-8")
        send_text(t, args.to)
        return

    if args.cmd == "detail":
        if not args.ids and not args.status:
            p.error("isi ID (CP-1,CP-2) atau --status")
        send_detail({i.strip() for i in args.ids.split(",") if i.strip()} if args.ids else None, args.status)
        return

    ids_baru = None
    if args.cmd == "add":
        ids_baru = cmd_add(args.json_file, args.force)
    elif args.cmd == "status":
        cmd_status(args.ids, args.status, args.note)
    if args.cmd in ("add", "status", "sheet"):
        if args.cmd == "sheet" and not tg_config().get("SHEET_WEBHOOK_URL"):
            sys.exit("ERROR SHEET_WEBHOOK_URL belum diisi di config.env")
        sync_sheet()
    elif args.cmd == "show":
        cmd_show(args.status)
    if args.cmd == "ping":
        send_ping()
        return
    if args.cmd == "send" or getattr(args, "send", False):
        send_document(caption_ringkas())
    if ids_baru and args.send:
        send_detail(set(ids_baru))


if __name__ == "__main__":
    main()
