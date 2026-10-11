#!/usr/bin/env python3
"""
Simpan content plan PeopleSync ke CSV dan kirim ke topik Telegram untuk direview.
Hanya pakai standard library.

    save_plan.py add batch.json [--send]          tambah/timpa baris (berdasarkan id)
    save_plan.py status CP-1,CP-2 "Approved" [--note "..."] [--send]
    save_plan.py show [--status "Menunggu review SML"]
    save_plan.py send                             kirim file CSV ke Telegram
    save_plan.py ping                             kirim pesan tes ke topik review (cek thread ID)

Konfigurasi: ~/hermes-data/content-plan/config.env
    REVIEW_CHAT_ID=-100...
    REVIEW_THREAD_ID=5
Token bot diambil dari TELEGRAM_BOT_TOKEN di ~/.hermes/.env (atau environment).
"""
import argparse
import csv
import datetime
import json
import os
import sys
import uuid
import urllib.request
from pathlib import Path

DATA_DIR = Path.home() / "hermes-data" / "content-plan"
CSV_PATH = DATA_DIR / "peoplesync_content_plan.csv"
CONFIG_PATH = DATA_DIR / "config.env"

FIELDS = [
    "id", "tanggal_tayang", "platform", "format", "pilar", "funnel", "judul_hook",
    "pesan_utama", "outline", "cta", "keyword", "sumber_klaim", "skor_checker",
    "catatan_checker", "status", "catatan_sml", "diperbarui",
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


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def cmd_add(path):
    batch = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(batch, dict):
        batch = batch.get("items") or batch.get("rows") or [batch]
    rows = {r["id"]: r for r in load_rows()}
    added = 0
    for item in batch:
        if not item.get("id"):
            print(f"SKIP baris tanpa id: {item}", file=sys.stderr)
            continue
        item = {k: ("" if v is None else str(v)) for k, v in item.items()}
        item.setdefault("status", "Menunggu review SML")
        item["diperbarui"] = now()
        rows[item["id"]] = {**rows.get(item["id"], {}), **item}
        added += 1
    save_rows(list(rows.values()))
    print(f"OK {added} baris disimpan ke {CSV_PATH}")


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


def send_ping():
    cfg = tg_config()
    token, chat, thread = cfg.get("TELEGRAM_BOT_TOKEN"), cfg.get("REVIEW_CHAT_ID"), cfg.get("REVIEW_THREAD_ID")
    if not token or not chat:
        print("WARN TELEGRAM_BOT_TOKEN atau REVIEW_CHAT_ID belum diset")
        return
    data = {"chat_id": chat, "text": f"Tes: file review Content Planning akan dikirim ke topik ini (thread {thread or '-'})."}
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
        print("OK pesan tes terkirim, cek di topik mana pesan itu muncul" if ok else "WARN Telegram menolak kiriman")
    except Exception as e:
        print(f"WARN gagal kirim ke Telegram: {e}")


def caption_ringkas():
    rows = load_rows()
    menunggu = sum(r.get("status") == "Menunggu review SML" for r in rows)
    approved = sum(r.get("status") == "Approved" for r in rows)
    return f"Content plan PeopleSync. Menunggu review: {menunggu}, Approved: {approved}, Total: {len(rows)}"


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("json_file"); a.add_argument("--send", action="store_true")
    s = sub.add_parser("status"); s.add_argument("ids"); s.add_argument("status")
    s.add_argument("--note"); s.add_argument("--send", action="store_true")
    sh = sub.add_parser("show"); sh.add_argument("--status")
    sub.add_parser("send")
    sub.add_parser("ping")
    args = p.parse_args()

    if args.cmd == "add":
        cmd_add(args.json_file)
    elif args.cmd == "status":
        cmd_status(args.ids, args.status, args.note)
    elif args.cmd == "show":
        cmd_show(args.status)
    if args.cmd == "ping":
        send_ping()
        return
    if args.cmd == "send" or getattr(args, "send", False):
        send_document(caption_ringkas())


if __name__ == "__main__":
    main()
