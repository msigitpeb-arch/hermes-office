#!/usr/bin/env python3
"""
Second brain ringan untuk Hermes: catatan Markdown + pencarian SQLite FTS5.
Hanya pakai standard library, tanpa layanan yang terus hidup.

    brain.py add --title "..." [--tags a,b] [--source URL] [--category notes] "isi"
                                   isi bisa teks, @path/file, atau - untuk stdin
    brain.py ingest <folder|file> [--category ref]   indeks file .md/.txt yang sudah ada (tidak disalin)
    brain.py search "pertanyaan" [--limit 5] [--category x] [--json]
    brain.py show <doc_id>
    brain.py list [--limit 20] [--category x]
    brain.py forget <doc_id>       hapus dari indeks; catatan buatan `add` ikut dihapus dari disk
    brain.py status

Data: ~/hermes-data/brain/   knowledge/<kategori>/*.md (bisa dibuka di Obsidian) dan brain.db (indeks).
Indeks bisa dibangun ulang kapan saja dari file; file Markdown adalah sumber utamanya.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(os.environ.get("BRAIN_ROOT", Path.home() / "hermes-data" / "brain"))
KNOWLEDGE = ROOT / "knowledge"
DB_PATH = ROOT / "brain.db"

CHUNK_CHARS = 1200
MAX_FILE_BYTES = 2_000_000
SKIP_DIRS = {".git", ".obsidian", ".trash", "node_modules", "skills"}

STOPWORDS = set("""
yang dan di ke dari untuk dengan pada adalah itu ini atau juga karena agar supaya sebagai oleh akan sudah belum
bisa dapat tidak bukan ada apa siapa kapan dimana mana bagaimana gimana kenapa mengapa berapa saya aku gw gue kamu lu
kita kami mereka dia nya tentang soal saja aja dong sih nih tuh lagi masih sama seperti kalau kalo jika maka
the a an of to in on for and or is are was were be been with by at from as it this that what which who how why when
""".split())

# Pola yang hampir pasti rahasia. Catatan berisi ini ditolak supaya tidak tersimpan sebagai teks biasa.
RAHASIA = re.compile(
    r"sk-[A-Za-z0-9_-]{16,}"
    r"|\b\d{8,10}:[A-Za-z0-9_-]{30,}\b"                      # token bot Telegram
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|(?i:\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*['\"]?[^\s'\"]{8,})"
)


def db():
    ROOT.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript("""
        CREATE TABLE IF NOT EXISTS docs (
            id INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL, title TEXT NOT NULL, tags TEXT DEFAULT '',
            source TEXT DEFAULT '', category TEXT DEFAULT '', sha TEXT NOT NULL, managed INTEGER DEFAULT 0,
            created TEXT NOT NULL, updated TEXT NOT NULL);
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
            doc_id UNINDEXED, ord UNINDEXED, title, body, tokenize='unicode61 remove_diacritics 2');
    """)
    return c


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "catatan"


def baca_frontmatter(text):
    """Kembalikan (meta, isi). Hanya membaca kunci sederhana `kunci: nilai` di blok --- pertama."""
    meta = {}
    if text.startswith("---"):
        akhir = text.find("\n---", 3)
        if akhir != -1:
            for baris in text[3:akhir].splitlines():
                if ":" in baris and not baris.startswith((" ", "\t", "-")):
                    k, v = baris.split(":", 1)
                    meta[k.strip().lower()] = v.strip().strip("\"'[]")
            text = text[akhir + 4:].lstrip("\n")
    return meta, text


def potong(isi):
    """Pecah per paragraf, bawa heading terakhir sebagai konteks, gabung sampai sekitar CHUNK_CHARS."""
    hasil, buf, heading = [], "", ""
    for blok in re.split(r"\n\s*\n", isi):
        blok = blok.strip()
        if not blok:
            continue
        m = re.match(r"#{1,6}\s+(.*)", blok)
        if m:
            heading = m.group(1).strip()
        if buf and len(buf) + len(blok) > CHUNK_CHARS:
            hasil.append(buf)
            buf = f"[{heading}]\n" if heading and not m else ""
        while len(blok) > CHUNK_CHARS * 2:  # paragraf raksasa tanpa jeda
            hasil.append((buf + blok[:CHUNK_CHARS]).strip())
            blok, buf = blok[CHUNK_CHARS:], ""
        buf += blok + "\n\n"
    if buf.strip():
        hasil.append(buf)
    return [h.strip() for h in hasil if h.strip()]


def indeks(c, path, text, category, managed, meta_override=None):
    """Tambah atau perbarui satu dokumen. Kembalikan (doc_id, 'baru' | 'diperbarui' | 'sama')."""
    meta, isi = baca_frontmatter(text)
    meta.update(meta_override or {})
    judul = meta.get("title") or next(
        (m.group(1).strip() for m in [re.search(r"(?m)^#\s+(.+)$", isi)] if m), Path(path).stem)
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    lama = c.execute("SELECT id, sha FROM docs WHERE path = ?", (str(path),)).fetchone()
    if lama and lama["sha"] == sha:
        return lama["id"], "sama"
    kolom = (judul, meta.get("tags", ""), meta.get("source", ""), category, sha, now())
    if lama:
        doc_id = lama["id"]
        c.execute("UPDATE docs SET title=?, tags=?, source=?, category=?, sha=?, updated=? WHERE id=?", (*kolom, doc_id))
        c.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
    else:
        doc_id = c.execute(
            "INSERT INTO docs (title, tags, source, category, sha, updated, path, managed, created) VALUES (?,?,?,?,?,?,?,?,?)",
            (*kolom, str(path), int(managed), now())).lastrowid
    c.executemany("INSERT INTO chunks (doc_id, ord, title, body) VALUES (?,?,?,?)",
                  [(doc_id, i, f"{judul} {meta.get('tags', '')}", ch) for i, ch in enumerate(potong(isi))])
    return doc_id, "diperbarui" if lama else "baru"


def cmd_add(args):
    teks = args.text
    if teks == "-":
        teks = sys.stdin.read()
    elif teks.startswith("@"):
        teks = Path(teks[1:]).expanduser().read_text(encoding="utf-8")
    teks = teks.strip()
    if not teks:
        sys.exit("ERROR isi catatan kosong")
    if RAHASIA.search(teks) and not args.force:
        sys.exit("ERROR isi catatan tampak memuat API key, token, atau password. Buang bagian itu dulu, "
                 "atau pakai --force kalau ini memang bukan rahasia.")
    folder = KNOWLEDGE / slug(args.category)
    folder.mkdir(parents=True, exist_ok=True)
    dasar = f"{datetime.date.today():%Y-%m-%d}-{slug(args.title)}"
    path, n = folder / f"{dasar}.md", 2
    while path.exists():
        path, n = folder / f"{dasar}-{n}.md", n + 1
    tags = ", ".join(t.strip() for t in (args.tags or "").split(",") if t.strip())
    depan = [f'title: "{args.title}"', f"date: {datetime.date.today():%Y-%m-%d}", f"tags: [{tags}]"]
    if args.source:
        depan.append(f"source: {args.source}")
    isi_file = "---\n" + "\n".join(depan) + "\n---\n\n" + teks + "\n"
    path.write_text(isi_file, encoding="utf-8")
    c = db()
    doc_id, _ = indeks(c, path, isi_file, slug(args.category), managed=True,
                       meta_override={"title": args.title, "tags": tags, "source": args.source or ""})
    c.commit()
    print(f"OK tersimpan #{doc_id}: {path}")


def cmd_ingest(args):
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        sys.exit(f"ERROR tidak ada: {target}")
    files = [target] if target.is_file() else [
        p for p in sorted(target.rglob("*"))
        if p.is_file() and p.suffix.lower() in (".md", ".txt", ".markdown")
        and not (set(p.relative_to(target).parts[:-1]) & SKIP_DIRS)]
    c = db()
    hitung = {"baru": 0, "diperbarui": 0, "sama": 0, "dilewati": 0}
    for p in files:
        if p.stat().st_size > MAX_FILE_BYTES:
            hitung["dilewati"] += 1
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            hitung["dilewati"] += 1
            continue
        if RAHASIA.search(text):
            print(f"LEWAT (tampak memuat rahasia): {p}", file=sys.stderr)
            hitung["dilewati"] += 1
            continue
        hitung[indeks(c, p, text, args.category, managed=False)[1]] += 1
    hilang = 0
    if target.is_dir():  # buang dari indeks dokumen yang filenya sudah tidak ada di folder ini
        for r in c.execute("SELECT id, path FROM docs WHERE managed = 0 AND path LIKE ?", (str(target) + os.sep + "%",)).fetchall():
            if not Path(r["path"]).exists():
                c.execute("DELETE FROM chunks WHERE doc_id = ?", (r["id"],))
                c.execute("DELETE FROM docs WHERE id = ?", (r["id"],))
                hilang += 1
    c.commit()
    print(f"OK {len(files)} file diperiksa: baru {hitung['baru']}, diperbarui {hitung['diperbarui']}, "
          f"tidak berubah {hitung['sama']}, dilewati {hitung['dilewati']}, dihapus dari indeks {hilang}")


def kueri_fts(pertanyaan):
    kata = [k for k in re.findall(r"[0-9A-Za-zÀ-ÿ]+", pertanyaan.lower()) if len(k) > 1 and k not in STOPWORDS]
    return " OR ".join(f'"{k}"*' for k in dict.fromkeys(kata))


def cmd_search(args):
    q = kueri_fts(args.query)
    c = db()
    rows = []
    if q:
        sql = """SELECT d.id, d.title, d.path, d.source, d.tags, d.category, d.updated, chunks.body,
                        bm25(chunks, 0.0, 0.0, 3.0, 1.0) AS skor
                 FROM chunks JOIN docs d ON d.id = chunks.doc_id
                 WHERE chunks MATCH ? {filter} ORDER BY skor LIMIT ?"""
        params = [q] + ([args.category] if args.category else []) + [args.limit * 4]
        rows = c.execute(sql.format(filter="AND d.category = ?" if args.category else ""), params).fetchall()
    hasil, per_doc = [], {}
    for r in rows:  # paling banyak dua potongan per dokumen supaya hasil tidak dikuasai satu catatan
        if per_doc.get(r["id"], 0) >= 2:
            continue
        per_doc[r["id"]] = per_doc.get(r["id"], 0) + 1
        hasil.append({"doc_id": r["id"], "judul": r["title"], "kategori": r["category"], "tags": r["tags"],
                      "sumber": r["source"], "path": r["path"], "diperbarui": r["updated"],
                      "skor": round(-r["skor"], 2), "kutipan": r["body"][:900]})
        if len(hasil) >= args.limit:
            break
    if args.json:
        print(json.dumps(hasil, ensure_ascii=False, indent=2))
        return
    if not hasil:
        print("Tidak ada catatan yang cocok.")
        return
    for h in hasil:
        print(f"#{h['doc_id']} {h['judul']}  [{h['kategori']}] skor {h['skor']}")
        print(f"   {h['path']}" + (f"  | sumber: {h['sumber']}" if h["sumber"] else ""))
        print("   " + h["kutipan"][:300].replace("\n", " ") + "\n")


def cmd_show(args):
    r = db().execute("SELECT * FROM docs WHERE id = ?", (args.doc_id,)).fetchone()
    if not r:
        sys.exit(f"ERROR tidak ada dokumen #{args.doc_id}")
    p = Path(r["path"])
    print(f"#{r['id']} {r['title']}\n{r['path']}\n")
    print(p.read_text(encoding="utf-8") if p.exists() else "(file sudah tidak ada di disk; jalankan ingest ulang)")


def cmd_list(args):
    c = db()
    rows = c.execute(
        "SELECT id, title, category, updated FROM docs {f} ORDER BY updated DESC, id DESC LIMIT ?".format(
            f="WHERE category = ?" if args.category else ""),
        ([args.category] if args.category else []) + [args.limit]).fetchall()
    for r in rows:
        print(f"#{r['id']} | {r['updated']} | {r['category']} | {r['title']}")
    print(f"Total ditampilkan: {len(rows)}")


def cmd_forget(args):
    c = db()
    r = c.execute("SELECT * FROM docs WHERE id = ?", (args.doc_id,)).fetchone()
    if not r:
        sys.exit(f"ERROR tidak ada dokumen #{args.doc_id}")
    c.execute("DELETE FROM chunks WHERE doc_id = ?", (r["id"],))
    c.execute("DELETE FROM docs WHERE id = ?", (r["id"],))
    c.commit()
    catatan = ""
    if r["managed"] and Path(r["path"]).exists():  # file hasil ingest milik user, tidak pernah disentuh
        Path(r["path"]).unlink()
        catatan = " dan filenya dihapus"
    print(f"OK #{r['id']} '{r['title']}' dihapus dari indeks{catatan}")


def cmd_status(_):
    c = db()
    docs = c.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    chunks = c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    print(f"Lokasi: {ROOT}")
    print(f"Dokumen: {docs} | potongan: {chunks} | ukuran indeks: {DB_PATH.stat().st_size // 1024} KB")
    for r in c.execute("SELECT category, COUNT(*) n FROM docs GROUP BY category ORDER BY n DESC"):
        print(f"  {r['category'] or '-'}: {r['n']}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("text"); a.add_argument("--title", required=True)
    a.add_argument("--tags"); a.add_argument("--source"); a.add_argument("--category", default="notes")
    a.add_argument("--force", action="store_true")
    i = sub.add_parser("ingest"); i.add_argument("path"); i.add_argument("--category", default="ref")
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--limit", type=int, default=5)
    s.add_argument("--category"); s.add_argument("--json", action="store_true")
    sh = sub.add_parser("show"); sh.add_argument("doc_id", type=int)
    ls = sub.add_parser("list"); ls.add_argument("--limit", type=int, default=20); ls.add_argument("--category")
    f = sub.add_parser("forget"); f.add_argument("doc_id", type=int)
    sub.add_parser("status")
    args = p.parse_args()
    {"add": cmd_add, "ingest": cmd_ingest, "search": cmd_search, "show": cmd_show,
     "list": cmd_list, "forget": cmd_forget, "status": cmd_status}[args.cmd](args)


if __name__ == "__main__":
    main()
