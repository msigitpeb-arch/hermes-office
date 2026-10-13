#!/usr/bin/env python3
"""
Second brain ringan untuk Hermes: catatan Markdown + pencarian SQLite FTS5.
Hanya pakai standard library, tanpa layanan yang terus hidup.

    brain.py add --title "..." [--tags a,b] [--source URL] [--category notes] "isi"
                                   isi bisa teks, @path/file, atau - untuk stdin
    brain.py add-file <file> [--title "..."] [--tags a,b] [--category dokumen]
                                   simpan file asli (.pdf .docx .md .txt .csv) dan indeks isinya
    brain.py ingest <folder|file> [--category ref]   indeks file .md/.txt yang sudah ada (tidak disalin)
    brain.py search "pertanyaan" [--limit 5] [--category x] [--json] [--no-refresh]
                                   sebelum mencari, indeks disegarkan dari folder knowledge/
    brain.py show <doc_id>
    brain.py list [--limit 20] [--category x]
    brain.py forget <doc_id>       hapus dari indeks; catatan buatan `add` ikut dihapus dari disk
    brain.py status

Data: ~/hermes-data/brain/   knowledge/<kategori>/*.md (bisa dibuka di Obsidian), files/ (file asli),
dan brain.db (indeks).
PDF dibaca lewat `pdftotext` (sudo apt install poppler-utils), atau PyMuPDF/pypdf kalau terpasang.
Indeks bisa dibangun ulang kapan saja dari file; file Markdown adalah sumber utamanya.
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(os.environ.get("BRAIN_ROOT", Path.home() / "hermes-data" / "brain"))
KNOWLEDGE = ROOT / "knowledge"
FILES = ROOT / "files"
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
            created TEXT NOT NULL, updated TEXT NOT NULL, file TEXT DEFAULT '');
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
            doc_id UNINDEXED, ord UNINDEXED, section UNINDEXED, title, body,
            tokenize='unicode61 remove_diacritics 2');
        CREATE TABLE IF NOT EXISTS seen (path TEXT PRIMARY KEY, stat TEXT NOT NULL);
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
    """Pecah per paragraf sampai sekitar CHUNK_CHARS. Kembalikan daftar (bagian, isi); bagian = heading terakhir."""
    hasil, buf, heading, bagian_buf = [], "", "", ""

    def simpan():
        nonlocal buf
        if buf.strip():
            hasil.append((bagian_buf, buf.strip()))
        buf = ""

    for blok in re.split(r"\n\s*\n", isi):
        blok = blok.strip()
        if not blok:
            continue
        m = re.match(r"#{1,6}\s+(.*)", blok)
        if m:  # heading baru memulai potongan baru, supaya tiap potongan punya satu letak yang jelas
            simpan()
            heading = m.group(1).strip()
        if buf and len(buf) + len(blok) > CHUNK_CHARS:
            simpan()
        if not buf:
            bagian_buf = heading
        while len(blok) > CHUNK_CHARS * 2:  # paragraf raksasa tanpa jeda
            buf += blok[:CHUNK_CHARS]
            simpan()
            blok, bagian_buf = blok[CHUNK_CHARS:], heading
        buf += blok + "\n\n"
    simpan()
    return hasil


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
    kolom = (judul, meta.get("tags", ""), meta.get("source", ""), category, sha, now(), meta.get("file", ""))
    if lama:
        doc_id = lama["id"]
        c.execute("UPDATE docs SET title=?, tags=?, source=?, category=?, sha=?, updated=?, file=? WHERE id=?",
                  (*kolom, doc_id))
        c.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
    else:
        doc_id = c.execute(
            "INSERT INTO docs (title, tags, source, category, sha, updated, file, path, managed, created) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)", (*kolom, str(path), int(managed), now())).lastrowid
    c.executemany("INSERT INTO chunks (doc_id, ord, section, title, body) VALUES (?,?,?,?,?)",
                  [(doc_id, i, bagian, f"{judul} {meta.get('tags', '')}", ch)
                   for i, (bagian, ch) in enumerate(potong(isi))])
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


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def teks_docx(path):
    """Ambil teks .docx tanpa library: paragraf, heading (jadi #), dan tabel (sel dipisah ' | ')."""
    with zipfile.ZipFile(path) as z:
        root = ElementTree.fromstring(z.read("word/document.xml"))

    def paragraf(p):
        teks = "".join(t.text or "" for t in p.iter(W + "t")).strip()
        gaya = p.find(f"{W}pPr/{W}pStyle")
        m = re.match(r"(?i)(?:heading|judul)\s*(\d)", gaya.get(W + "val", "") if gaya is not None else "")
        return f"{'#' * min(int(m.group(1)), 6)} {teks}" if m and teks else teks

    keluar = []
    for el in root.find(W + "body"):
        if el.tag == W + "p":
            keluar.append(paragraf(el))
        elif el.tag == W + "tbl":
            for baris in el.iter(W + "tr"):
                sel = [" ".join(paragraf(p) for p in tc.iter(W + "p")).strip() for tc in baris.iter(W + "tc")]
                keluar.append(" | ".join(sel))
    return "\n\n".join(k for k in keluar if k)


def teks_pdf(path):
    """Teks PDF per halaman, tiap halaman diberi heading '## Halaman N' supaya letaknya bisa disebut."""
    halaman = None
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True)
        if r.returncode == 0:
            halaman = r.stdout.decode("utf-8", "replace").split("\f")
    if halaman is None:
        try:
            import fitz  # PyMuPDF
            with fitz.open(str(path)) as doc:
                halaman = [h.get_text() for h in doc]
        except ImportError:
            try:
                from pypdf import PdfReader
                halaman = [h.extract_text() or "" for h in PdfReader(str(path)).pages]
            except ImportError:
                sys.exit("ERROR belum ada pembaca PDF. Pasang salah satu: sudo apt install -y poppler-utils")
    isi = [f"## Halaman {i}\n\n{h.strip()}" for i, h in enumerate(halaman, 1) if h.strip()]
    if not isi:
        sys.exit("ERROR PDF ini tidak punya teks (kemungkinan hasil pindai). Perlu OCR dulu sebelum bisa dicari.")
    return "\n\n".join(isi)


def cmd_add_file(args):
    src = Path(args.path).expanduser()
    if not src.is_file():
        sys.exit(f"ERROR file tidak ada: {src}")
    ext = src.suffix.lower()
    if ext == ".docx":
        teks = teks_docx(src)
    elif ext == ".pdf":
        teks = teks_pdf(src)
    elif ext in (".md", ".markdown", ".txt", ".csv"):
        teks = baca_frontmatter(src.read_text(encoding="utf-8", errors="replace"))[1]
    else:
        sys.exit(f"ERROR jenis file {ext or '(tanpa ekstensi)'} belum didukung. Yang bisa: .pdf .docx .md .txt .csv")
    if not teks.strip():
        sys.exit("ERROR tidak ada teks yang bisa diambil dari file ini")
    if RAHASIA.search(teks) and not args.force:
        sys.exit("ERROR isi file tampak memuat API key, token, atau password. Pakai --force kalau ini memang bukan rahasia.")

    judul = args.title or src.stem.replace("_", " ").replace("-", " ").strip()
    kategori = slug(args.category)
    sha_file = hashlib.sha256(src.read_bytes()).hexdigest()
    (FILES / kategori).mkdir(parents=True, exist_ok=True)
    asli = FILES / kategori / f"{slug(judul)}-{sha_file[:8]}{ext}"
    c = db()
    lama = c.execute("SELECT id, title FROM docs WHERE file = ?", (str(asli),)).fetchone()
    if lama:  # file yang sama persis sudah pernah disimpan
        print(f"OK sudah ada sebagai #{lama['id']} '{lama['title']}': {asli}")
        return
    shutil.copy2(src, asli)
    tags = ", ".join(t.strip() for t in (args.tags or "").split(",") if t.strip())
    (KNOWLEDGE / kategori).mkdir(parents=True, exist_ok=True)
    catatan = KNOWLEDGE / kategori / f"{slug(judul)}-{sha_file[:8]}.md"
    isi_file = ("---\n" + f'title: "{judul}"\ndate: {datetime.date.today():%Y-%m-%d}\ntags: [{tags}]\n'
                f"file: {asli}\n---\n\n" + teks.strip() + "\n")
    catatan.write_text(isi_file, encoding="utf-8")
    doc_id, _ = indeks(c, catatan, isi_file, kategori, managed=True,
                       meta_override={"title": judul, "tags": tags, "file": str(asli)})
    c.commit()
    n = c.execute("SELECT COUNT(*) FROM chunks WHERE doc_id = ?", (doc_id,)).fetchone()[0]
    print(f"OK tersimpan #{doc_id} '{judul}': {len(teks.split())} kata, {n} potongan. File asli: {asli}")


def sinkron(c, target, category=None, lapor=True):
    """Samakan indeks dengan isi folder (atau satu file). Kembalikan hitungan per hasil.

    File yang ukuran dan waktu ubahnya sama seperti terakhir dilihat tidak dibaca ulang, jadi
    pemanggilan berulang murah. category=None: kategori diambil dari nama subfolder pertama.
    """
    files = [target] if target.is_file() else [
        f for f in sorted(target.rglob("*"))
        if f.is_file() and f.suffix.lower() in (".md", ".txt", ".markdown")
        and not (set(f.relative_to(target).parts[:-1]) & SKIP_DIRS)]
    dilihat = dict(c.execute("SELECT path, stat FROM seen").fetchall())
    hitung = {"baru": 0, "diperbarui": 0, "sama": 0, "dilewati": 0, "hilang": 0}
    for f in files:
        st = f.stat()
        stat = f"{st.st_mtime_ns}:{st.st_size}"
        if dilihat.get(str(f)) == stat:
            hitung["sama"] += 1
            continue
        c.execute("INSERT OR REPLACE INTO seen (path, stat) VALUES (?, ?)", (str(f), stat))
        if st.st_size > MAX_FILE_BYTES:
            hitung["dilewati"] += 1
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            hitung["dilewati"] += 1
            continue
        if RAHASIA.search(text):
            if lapor:
                print(f"LEWAT (tampak memuat rahasia): {f}", file=sys.stderr)
            hitung["dilewati"] += 1
            continue
        # Dokumen yang sudah dikenal (misalnya catatan buatan `add`) mempertahankan kategorinya
        lama = c.execute("SELECT category FROM docs WHERE path = ?", (str(f),)).fetchone()
        if lama:
            kategori = lama["category"]
        elif category:
            kategori = category
        else:
            bagian = f.relative_to(target).parts if target.is_dir() else ()
            kategori = slug(bagian[0]) if len(bagian) > 1 else "notes"
        hitung[indeks(c, f, text, kategori, managed=False)[1]] += 1
    if target.is_dir():  # buang dari indeks dokumen yang filenya sudah tidak ada di folder ini
        awalan = str(target) + os.sep
        for r in c.execute("SELECT id, path FROM docs").fetchall():
            if r["path"].startswith(awalan) and not Path(r["path"]).exists():
                c.execute("DELETE FROM chunks WHERE doc_id = ?", (r["id"],))
                c.execute("DELETE FROM docs WHERE id = ?", (r["id"],))
                c.execute("DELETE FROM seen WHERE path = ?", (r["path"],))
                hitung["hilang"] += 1
    c.commit()
    return len(files), hitung


def cmd_ingest(args):
    target = Path(args.path).expanduser().resolve()
    if not target.exists():
        sys.exit(f"ERROR tidak ada: {target}")
    n, h = sinkron(db(), target, args.category)
    print(f"OK {n} file diperiksa: baru {h['baru']}, diperbarui {h['diperbarui']}, "
          f"tidak berubah {h['sama']}, dilewati {h['dilewati']}, dihapus dari indeks {h['hilang']}")


def kueri_fts(pertanyaan):
    kata = [k for k in re.findall(r"[0-9A-Za-zÀ-ÿ]+", pertanyaan.lower()) if len(k) > 1 and k not in STOPWORDS]
    return " OR ".join(f'"{k}"*' for k in dict.fromkeys(kata))


def cmd_search(args):
    q = kueri_fts(args.query)
    c = db()
    if not args.no_refresh and KNOWLEDGE.is_dir():
        # Halaman yang ditulis langsung ke vault (skill obsidian, llm-wiki, atau Obsidian di PC)
        # tidak lewat script ini, jadi indeks disamakan dulu dengan isi folder.
        sinkron(c, KNOWLEDGE.resolve(), lapor=False)
    rows = []
    if q:
        sql = """SELECT d.id, d.title, d.path, d.source, d.tags, d.category, d.updated, d.file,
                        chunks.body, chunks.section, bm25(chunks, 0.0, 0.0, 0.0, 3.0, 1.0) AS skor
                 FROM chunks JOIN docs d ON d.id = chunks.doc_id
                 WHERE chunks MATCH ? {filter} ORDER BY skor LIMIT ?"""
        params = [q] + ([args.category] if args.category else []) + [args.limit * 4]
        rows = c.execute(sql.format(filter="AND d.category = ?" if args.category else ""), params).fetchall()
    hasil, per_doc = [], {}
    for r in rows:  # batasi potongan per dokumen supaya hasil tidak dikuasai satu dokumen
        if per_doc.get(r["id"], 0) >= args.per_doc:
            continue
        per_doc[r["id"]] = per_doc.get(r["id"], 0) + 1
        hasil.append({"doc_id": r["id"], "judul": r["title"], "bagian": r["section"], "kategori": r["category"],
                      "tags": r["tags"], "sumber": r["source"], "file_asli": r["file"], "path": r["path"],
                      "diperbarui": r["updated"], "skor": round(-r["skor"], 2), "kutipan": r["body"][:900]})
        if len(hasil) >= args.limit:
            break
    if args.json:
        print(json.dumps(hasil, ensure_ascii=False, indent=2))
        return
    if not hasil:
        print("Tidak ada catatan yang cocok.")
        return
    for h in hasil:
        print(f"#{h['doc_id']} {h['judul']}" + (f" > {h['bagian']}" if h["bagian"] else "")
              + f"  [{h['kategori']}] skor {h['skor']}")
        print(f"   {h['file_asli'] or h['path']}" + (f"  | sumber: {h['sumber']}" if h["sumber"] else ""))
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
    if r["managed"]:  # file hasil ingest milik user, tidak pernah disentuh
        for f in (r["path"], r["file"]):
            if f and Path(f).exists():
                Path(f).unlink()
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
    af = sub.add_parser("add-file"); af.add_argument("path"); af.add_argument("--title"); af.add_argument("--tags")
    af.add_argument("--category", default="dokumen"); af.add_argument("--force", action="store_true")
    i = sub.add_parser("ingest"); i.add_argument("path"); i.add_argument("--category", default="ref")
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--limit", type=int, default=5)
    s.add_argument("--category"); s.add_argument("--json", action="store_true")
    s.add_argument("--per-doc", type=int, default=3, help="potongan paling banyak per dokumen")
    s.add_argument("--no-refresh", action="store_true", help="jangan segarkan indeks sebelum mencari")
    sh = sub.add_parser("show"); sh.add_argument("doc_id", type=int)
    ls = sub.add_parser("list"); ls.add_argument("--limit", type=int, default=20); ls.add_argument("--category")
    f = sub.add_parser("forget"); f.add_argument("doc_id", type=int)
    sub.add_parser("status")
    args = p.parse_args()
    {"add": cmd_add, "add-file": cmd_add_file, "ingest": cmd_ingest, "search": cmd_search, "show": cmd_show,
     "list": cmd_list, "forget": cmd_forget, "status": cmd_status}[args.cmd](args)


if __name__ == "__main__":
    main()
