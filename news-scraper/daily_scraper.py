"""
Daily News Scraper -> WhatsApp (Fonnte) / Telegram
=====================================================

Alur kerja:
1. Ambil RSS dari portal berita Indonesia per kategori (dengan failover antar sumber).
2. Pilih 1 berita per kategori: masih segar, relevan (filter kata utuh), belum pernah
   dikirim, dan tidak dobel dengan kategori lain.
3. Ambil isi artikel asli, lalu minta LLM (via 9router di VPS) menulis ulang dengan
   gaya rekan kerja yang membagikan bacaan. Ada pengecekan angka agar LLM tidak
   mengarang fakta. Kalau LLM gagal, otomatis pakai ringkasan ekstraktif.
4. Kirim ke WhatsApp (Fonnte) dan/atau Telegram, lalu catat URL yang sudah terkirim.

Pemakaian:
    python daily_scraper.py               # jalan normal (kirim)
    python daily_scraper.py --dry-run     # cetak pesan saja, tidak kirim
    python daily_scraper.py --no-llm      # paksa mode ekstraktif tanpa LLM
    python daily_scraper.py --check-feeds # cek kesehatan semua RSS feed

Semua konfigurasi dibaca dari environment / file .env di folder yang sama
(lihat .env.example).
"""

import argparse
import calendar
import datetime
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import feedparser
import requests
from bs4 import BeautifulSoup

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
HISTORY_FILE = DATA_DIR / "sent_history.json"
LOCK_FILE = DATA_DIR / "scraper.lock"
WIB = datetime.timezone(datetime.timedelta(hours=7))

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}


# ==============================================================================
# KONFIGURASI
# ==============================================================================
def load_env_file(path):
    """Loader .env sederhana (tanpa dependensi). Nilai di environment tetap menang."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


load_env_file(BASE_DIR / ".env")


def env(name, default=""):
    return os.getenv(name, default).strip()


CFG = {
    "llm_base_url": env("LLM_BASE_URL", "http://127.0.0.1:20128/v1").rstrip("/"),
    "llm_api_key": env("LLM_API_KEY"),
    "llm_model": env("LLM_MODEL", "scraping-news"),
    "llm_timeout": int(env("LLM_TIMEOUT", "180")),
    "fonnte_token": env("FONNTE_TOKEN"),
    "wa_target": env("WA_TARGET_NUMBER"),
    "tg_token": env("TELEGRAM_BOT_TOKEN"),
    "tg_chat": env("TELEGRAM_CHAT_ID"),
    "tg_thread": env("TELEGRAM_THREAD_ID"),  # ID topik di grup forum (opsional)
    "audience": env("AUDIENCE", "Rekan-rekan"),
    "send_mode": env("SEND_MODE", "split").lower(),  # split | digest
    "max_age_hours": int(env("MAX_AGE_HOURS", "36")),
    "history_days": int(env("HISTORY_DAYS", "10")),
}

# Kata kunci dicocokkan sebagai KATA UTUH (bukan substring), jadi "ai" tidak
# ikut cocok dengan "pakai"/"ramai", dan frasa umum seperti "air" atau "data"
# sudah diganti versi yang lebih spesifik.
KW_LINGKUNGAN = [
    "lingkungan", "iklim", "perubahan iklim", "emisi", "karbon", "energi terbarukan",
    "ebt", "plts", "plta", "panas bumi", "transisi energi", "ekonomi hijau",
    "sampah", "tpa", "hutan", "deforestasi", "karhutla", "kebakaran hutan",
    "kekeringan", "krisis air", "air bersih", "banjir", "el nino", "la nina",
    "polusi", "pencemaran", "mangrove", "gambut", "net zero", "dekarbonisasi",
]
KW_SIBER = [
    "siber", "keamanan siber", "bssn", "hacker", "peretas", "diretas", "peretasan",
    "kebocoran data", "data bocor", "data pribadi", "pelindungan data", "pdp",
    "malware", "ransomware", "phishing", "dark web", "serangan siber", "bobol",
    "judi online", "penipuan online", "scam", "kerentanan", "cybersecurity",
]
KW_AI = [
    "ai", "kecerdasan artifisial", "kecerdasan buatan", "data center", "pusat data",
    "openai", "chatgpt", "gemini", "claude", "llm", "nvidia", "gpu", "chip",
    "semikonduktor", "komputasi awan", "cloud", "hyperscale", "server",
    "machine learning", "deepseek", "copilot",
]

FEEDS = {
    "Renewable Energy & Lingkungan": [
        {"name": "Mongabay Indonesia", "url": "https://www.mongabay.co.id/feed/"},
        # Catatan: feed ini kanal digital Katadata. Ganti dengan feed kanal
        # energi/ekonomi hijau Katadata kalau URL-nya sudah dipastikan.
        {"name": "Katadata", "url": "https://katadata.co.id/rss/digital", "filter": KW_LINGKUNGAN},
        {"name": "Antara News", "url": "https://www.antaranews.com/rss/terkini.xml", "filter": KW_LINGKUNGAN},
    ],
    "Cyber Security": [
        {"name": "CNN Indonesia", "url": "https://www.cnnindonesia.com/teknologi/rss", "filter": KW_SIBER},
        {"name": "DetikINET", "url": "https://inet.detik.com/rss", "filter": KW_SIBER},
        {"name": "Antara News", "url": "https://www.antaranews.com/rss/tekno.xml", "filter": KW_SIBER},
        {"name": "Sindonews", "url": "https://tekno.sindonews.com/rss", "filter": KW_SIBER},
    ],
    "AI & Data Center": [
        {"name": "CNBC Indonesia", "url": "https://www.cnbcindonesia.com/tech/rss", "filter": KW_AI},
        {"name": "Katadata", "url": "https://katadata.co.id/rss/digital", "filter": KW_AI},
        {"name": "DetikINET", "url": "https://inet.detik.com/rss", "filter": KW_AI},
        {"name": "Republika", "url": "https://www.republika.co.id/rss/inovasi", "filter": KW_AI},
    ],
    "Tech & Inovasi": [
        {"name": "Antara News", "url": "https://www.antaranews.com/rss/tekno.xml"},
        {"name": "DetikINET", "url": "https://inet.detik.com/rss"},
        {"name": "Jagat Review", "url": "https://www.jagatreview.com/feed/"},
        {"name": "Gizmologi", "url": "https://gizmologi.id/feed/"},
        {"name": "Sindonews", "url": "https://tekno.sindonews.com/rss"},
    ],
}

# Frasa pembuka per kategori (dipakai mulai berita kedua di sesi yang sama).
OPENER_KATEGORI = {
    "Renewable Energy & Lingkungan": "Dari isu lingkungan dan energi,",
    "Cyber Security": "Dari sisi keamanan siber,",
    "AI & Data Center": "Soal AI dan data center,",
    "Tech & Inovasi": "Kabar teknologi lainnya,",
}


def log(msg):
    print(f"[{datetime.datetime.now(WIB):%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


# ==============================================================================
# SESI & SALAM
# ==============================================================================
def sesi_sekarang(now=None):
    """Kembalikan info sesi (pagi/siang/sore/malam) berdasarkan jam WIB."""
    now = now or datetime.datetime.now(WIB)
    jam = now.hour
    aud = CFG["audience"]
    if 4 <= jam < 11:
        return {
            "nama": "pagi",
            "salam": f"Selamat pagi, {aud}. Semangat beraktivitas hari ini.",
            "pembuka": "Bacaan pagi ini,",
        }
    if 11 <= jam < 15:
        return {
            "nama": "siang",
            "salam": f"Selamat siang, {aud}. Semoga harinya lancar.",
            "pembuka": "Bacaan siang ini,",
        }
    if 15 <= jam < 19:
        return {
            "nama": "sore",
            "salam": f"Selamat sore, {aud}. Terima kasih atas kerja kerasnya hari ini.",
            "pembuka": "Bacaan sore hari ini,",
        }
    return {
        "nama": "malam",
        "salam": f"Selamat malam, {aud}. Ada beberapa bacaan ringan sebelum istirahat.",
        "pembuka": "Bacaan malam ini,",
    }


# ==============================================================================
# RIWAYAT (ANTI-DUPLIKAT ANTAR SESI)
# ==============================================================================
def normalisasi_url(url):
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def normalisasi_judul(judul):
    return re.sub(r"[^a-z0-9]+", " ", judul.lower()).strip()


def muat_riwayat():
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {"urls": {}, "titles": {}}
    batas = time.time() - CFG["history_days"] * 86400
    for key in ("urls", "titles"):
        data[key] = {k: v for k, v in data.get(key, {}).items() if v >= batas}
    return data


def simpan_riwayat(riwayat, items):
    now = time.time()
    for it in items:
        riwayat["urls"][normalisasi_url(it["link"])] = now
        riwayat["titles"][normalisasi_judul(it["judul"])] = now
    DATA_DIR.mkdir(exist_ok=True)
    tmp = HISTORY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(riwayat, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(HISTORY_FILE)


# ==============================================================================
# RSS & PEMILIHAN BERITA
# ==============================================================================
_feed_cache = {}


def ambil_feed(url):
    if url in _feed_cache:
        return _feed_cache[url]
    try:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=20)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        log(f"[Feed] Gagal ambil {url}: {e}")
        feed = feedparser.parse(b"")
    _feed_cache[url] = feed
    return feed


def kompilasi_kata_kunci(keywords):
    pola = "|".join(re.escape(k) for k in sorted(keywords, key=len, reverse=True))
    return re.compile(rf"(?<![\w-])(?:{pola})(?![\w-])", re.IGNORECASE)


def umur_jam(entry):
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    if not t:
        return None
    return (time.time() - calendar.timegm(t)) / 3600


def bersihkan_html(raw):
    if not raw:
        return ""
    text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    return " ".join(text.replace("�", " ").split())


def pilih_dari_feed(sumber, riwayat, sudah_dipilih):
    """Pilih kandidat terbaik dari satu feed, atau None kalau tidak ada yang layak."""
    feed = ambil_feed(sumber["url"])
    if not feed.entries:
        return None

    regex = kompilasi_kata_kunci(sumber["filter"]) if sumber.get("filter") else None
    terbaik, skor_terbaik = None, 0

    for urutan, entry in enumerate(feed.entries[:30]):
        link = entry.get("link", "")
        judul = bersihkan_html(entry.get("title", ""))
        if not link or not judul:
            continue
        url_n = normalisasi_url(link)
        judul_n = normalisasi_judul(judul)
        if url_n in riwayat["urls"] or judul_n in riwayat["titles"] or url_n in sudah_dipilih:
            continue
        umur = umur_jam(entry)
        if umur is not None and umur > CFG["max_age_hours"]:
            continue

        ringkas = bersihkan_html(entry.get("summary", entry.get("description", "")))
        if regex:
            skor = 3 * len(regex.findall(judul)) + len(regex.findall(ringkas))
            if skor == 0:
                continue
        else:
            skor = 1
        # Sedikit bonus untuk berita yang lebih baru (urutan feed = terbaru dulu).
        skor = skor + max(0, 1 - urutan * 0.05)
        if skor > skor_terbaik:
            terbaik, skor_terbaik = {
                "sumber": sumber["name"],
                "judul": judul,
                "link": link,
                "ringkasan_feed": ringkas,
            }, skor
    return terbaik


def ambil_berita(riwayat):
    hasil = {}
    sudah_dipilih = set()
    for kategori, daftar in FEEDS.items():
        for sumber in daftar:
            item = pilih_dari_feed(sumber, riwayat, sudah_dipilih)
            if item:
                hasil[kategori] = item
                sudah_dipilih.add(normalisasi_url(item["link"]))
                log(f"[Pilih] {kategori} <- {sumber['name']}: {item['judul']}")
                break
            log(f"[Failover] {kategori}: {sumber['name']} tidak ada berita layak, lanjut sumber berikutnya")
        else:
            log(f"[Skip] {kategori}: tidak ada berita baru yang relevan di semua sumber")
    return hasil


# ==============================================================================
# EKSTRAKSI ISI ARTIKEL
# ==============================================================================
SELECTORS = [
    "div.detail-text", "div.detail__body-text", "div.post-content", "div.read__content",
    "div.entry-content", "div.detail-desc", "#detail-desc", "div.article-content",
    "div.article__content", "div.detail-body", "article",
]
SAMPAH_PARAGRAF = (
    "baca juga", "simak", "foto:", "video:", "iklan", "advertisement", "scroll to",
    "lihat juga", "editor:", "pewarta:", "sumber:", "copyright", "artikel ini",
    "dapatkan update", "ikuti kami", "follow",
)
PREFIX_PERS = re.compile(
    r"^(?:[A-Z][A-Za-z.\s]{1,25}\s*\([A-Za-z\s.]{2,15}\)|[A-Z][A-Za-z.\s]{1,25},\s*[A-Za-z0-9.\s]{2,25}\s*-{1,2})"
    r"\s*[-–—]?\s*"
)


def bersihkan_prefix_pers(teks):
    teks = PREFIX_PERS.sub("", teks.strip())
    return teks.lstrip(". ,;:!-–—\t\n")


def ambil_isi_artikel(link):
    """Kembalikan daftar paragraf bersih dari halaman artikel (maks ~8 paragraf)."""
    try:
        resp = requests.get(link, headers=BROWSER_HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.content, "html.parser")
    except Exception as e:
        log(f"[Artikel] Gagal buka {link}: {e}")
        return []

    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "figure", "form"]):
        tag.decompose()

    container = None
    for sel in SELECTORS:
        c = soup.select_one(sel)
        if c and len(c.get_text(" ", strip=True)) > 300:
            container = c
            break
    if container is None:
        # Fallback generik: elemen dengan total teks <p> terbanyak.
        kandidat = {}
        for p in soup.find_all("p"):
            parent = p.parent
            kandidat[parent] = kandidat.get(parent, 0) + len(p.get_text(strip=True))
        if kandidat:
            container = max(kandidat, key=kandidat.get)
    if container is None:
        return []

    paragraf = []
    for p in container.find_all("p"):
        txt = " ".join(p.get_text(" ", strip=True).split())
        if len(txt) < 50 or txt.lower().startswith(SAMPAH_PARAGRAF) or txt.endswith(":"):
            continue
        txt = bersihkan_prefix_pers(txt) if not paragraf else txt
        if txt and txt not in paragraf:
            paragraf.append(txt)
        if len(paragraf) >= 8:
            break
    return paragraf


# ==============================================================================
# PENULISAN ULANG DENGAN LLM (9router)
# ==============================================================================
SYSTEM_PROMPT = """Kamu menulis ringkasan berita untuk grup WhatsApp kantor. Gayanya seperti rekan kerja yang membagikan bacaan menarik: hangat, jelas, tidak menggurui.

Aturan isi:
- Hanya gunakan fakta yang ada di teks sumber. Jangan menambah angka, nama, tanggal, tempat, atau kutipan yang tidak tertulis di sumber.
- Paragraf 1 (2-3 kalimat): inti berita. Apa yang terjadi, siapa, di mana, kapan, dan angka kunci kalau ada.
- Paragraf 2 (2-3 kalimat): konteks atau dampaknya, terutama untuk Indonesia, dunia kerja, atau industri. Boleh menarik benang merah yang wajar dari isi sumber, tanpa spekulasi.
- Paragraf 3 opsional (1-2 kalimat): langkah praktis yang bisa dilakukan pembaca. Tulis hanya kalau beritanya memang mengarah ke sana (misalnya soal keamanan siber atau lingkungan). Kalau tidak relevan, jangan ditulis.
- Untuk berita produk, fokus ke apa yang baru dan siapa yang diuntungkan. Jangan menulis seperti iklan: lewati detail promo, bonus pembelian, dan cara membeli.
- Panjang total 70 sampai 140 kata.

Aturan bahasa:
- Bahasa Indonesia yang luwes dan rapi sebagai basis.
- Istilah Inggris yang lazim dipakai apa adanya oleh profesional Indonesia JANGAN diterjemahkan, karena terjemahannya terdengar kaku atau malah tidak dikenal. Contoh: malware, malicious, ransomware, phishing, hacker, deepfake, AI, data center, cloud, server, startup, update, upgrade, chip, GPU, dashboard, platform. Tulis "serangan malware", bukan "serangan perangkat lunak berbahaya".
- Kalimat aktif dan langsung. Variasikan panjang kalimat.
- Dilarang: emoji, tanda seru, markdown, tanda bintang, judul, bullet, tanda pisah panjang (—), salam pembuka, link, dan tagar.
- Hindari frasa klise: "di era", "mari kita", "tak dapat dipungkiri", "perlu dicatat", "menariknya", "hal ini menunjukkan", "dalam lanskap", "sangat penting", "krusial", "tidak hanya ... tetapi juga", "pada akhirnya", "secara keseluruhan".
- Jangan menutup dengan kalimat moral atau pertanyaan retoris.

Keluarkan hanya paragraf-paragrafnya, dipisah satu baris kosong."""


def panggil_llm(messages):
    if not CFG["llm_api_key"]:
        raise RuntimeError("LLM_API_KEY belum diset")
    resp = requests.post(
        f"{CFG['llm_base_url']}/chat/completions",
        headers={"Authorization": f"Bearer {CFG['llm_api_key']}", "Content-Type": "application/json"},
        json={
            "model": CFG["llm_model"],
            "messages": messages,
            "stream": False,
            "temperature": 0.5,
            "max_tokens": 2500,
        },
        timeout=CFG["llm_timeout"],
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"].get("content") or ""
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    log(f"[LLM] model={data.get('model', '?')}")
    return content


EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]")


def rapikan_output_llm(teks):
    teks = re.sub(r"<think>.*?</think>", "", teks, flags=re.S)
    teks = EMOJI_RE.sub("", teks)
    teks = teks.replace("**", "").replace("*", "").replace("#", "")
    teks = re.sub(r"\s*[—–]\s*", ", ", teks)
    teks = teks.replace("!", ".")
    teks = re.sub(r"https?://\S+", "", teks)
    paragraf = [" ".join(p.split()) for p in re.split(r"\n\s*\n", teks) if p.strip()]
    return "\n\n".join(paragraf)


def angka_tak_berdasar(output, sumber):
    """Angka di output yang tidak muncul di teks sumber (indikasi halusinasi)."""
    def digits(s):
        return {re.sub(r"[.,]", "", m) for m in re.findall(r"\d+(?:[.,]\d+)*", s)}
    sumber_digit = digits(sumber)
    sumber_gabung = re.sub(r"[.,\s]", "", sumber)
    return sorted(n for n in digits(output) - sumber_digit if n not in sumber_gabung)


def tulis_dengan_llm(item, opener):
    sumber_teks = "\n\n".join(item["paragraf"]) or item["ringkasan_feed"]
    sumber_teks = sumber_teks[:4000]
    user_prompt = (
        f"Judul: {item['judul']}\n"
        f"Media: {item['sumber']}\n\n"
        f"Teks sumber:\n{sumber_teks}\n\n"
        f'Mulai paragraf pertama persis dengan frasa: "{opener}"'
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}]
    referensi = f"{item['judul']} {sumber_teks}"

    for percobaan in range(2):
        hasil = rapikan_output_llm(panggil_llm(messages))
        jumlah_kata = len(hasil.split())
        if jumlah_kata < 40:
            raise RuntimeError(f"Output LLM terlalu pendek ({jumlah_kata} kata)")
        asing = angka_tak_berdasar(hasil, referensi)
        if not asing:
            return hasil
        log(f"[LLM] Angka tidak ada di sumber: {asing} (percobaan {percobaan + 1})")
        messages += [
            {"role": "assistant", "content": hasil},
            {"role": "user", "content": (
                f"Angka berikut tidak ada di teks sumber: {', '.join(asing)}. "
                "Tulis ulang tanpa angka yang tidak tertulis di sumber."
            )},
        ]
    raise RuntimeError("Output LLM tetap memuat angka yang tidak ada di sumber")


# ==============================================================================
# FALLBACK EKSTRAKTIF (tanpa LLM)
# ==============================================================================
def potong_kalimat(teks, max_kalimat=2, min_panjang=130):
    teks = re.sub(r"\s*\.{2,}\s*$", "", teks).strip()
    kalimat = [k.strip() for k in re.split(r"(?<=[.!?])\s+", teks) if k.strip()]
    hasil, total = [], 0
    for k in kalimat:
        hasil.append(k)
        total += len(k)
        if total >= min_panjang or len(hasil) >= max_kalimat:
            break
    res = " ".join(hasil)
    if res and res[-1] not in ".!?":
        res += "."
    return res


def is_english_text(text):
    if not text:
        return False
    words = set(re.findall(r"[a-z]+", text.lower()))
    en = len(words & {"the", "and", "for", "with", "from", "about", "this", "that", "are", "was", "were", "of", "is"})
    idn = len(words & {"yang", "di", "dan", "dari", "untuk", "ini", "itu", "pada", "oleh", "ke", "adalah"})
    return en >= 2 or (en >= 1 and idn == 0)


def terjemahkan(teks):
    try:
        res = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "auto", "tl": "id", "dt": "t", "q": teks},
            headers=BROWSER_HEADERS,
            timeout=12,
        )
        if res.status_code == 200:
            return "".join(s[0] for s in res.json()[0] if s and s[0])
    except Exception as e:
        log(f"[Translate] Gagal: {e}")
    return teks


def tulis_ekstraktif(item, opener):
    paragraf = item["paragraf"] or [item["ringkasan_feed"]]
    p1 = potong_kalimat(paragraf[0]) if paragraf and paragraf[0] else ""
    p2 = potong_kalimat(paragraf[1]) if len(paragraf) > 1 else ""
    judul = item["judul"]
    if is_english_text(judul):
        judul = terjemahkan(judul)
    if is_english_text(p1):
        p1 = terjemahkan(p1)
    if p2 and is_english_text(p2):
        p2 = terjemahkan(p2)
    body = f"{opener} {judul.rstrip('.')}. {p1}".strip()
    return f"{body}\n\n{p2}" if p2 else body


# ==============================================================================
# PENYUSUNAN PESAN
# ==============================================================================
URUTAN = ["Renewable Energy & Lingkungan", "Cyber Security", "AI & Data Center", "Tech & Inovasi"]


def susun_item(berita, sesi, pakai_llm):
    """Isi item['narasi'] untuk setiap berita sesuai urutan kategori."""
    siap = []
    for kategori in URUTAN:
        item = berita.get(kategori)
        if not item:
            continue
        opener = sesi["pembuka"] if not siap else OPENER_KATEGORI[kategori]
        item["paragraf"] = ambil_isi_artikel(item["link"])
        narasi = None
        if pakai_llm:
            try:
                narasi = tulis_dengan_llm(item, opener)
            except Exception as e:
                log(f"[LLM] Fallback ekstraktif untuk '{item['judul']}': {e}")
        item["narasi"] = narasi or tulis_ekstraktif(item, opener)
        item["kategori"] = kategori
        siap.append(item)
    return siap


def blok_link(link):
    return f"Selengkapnya bisa dibaca di sini:\n{link}"


def susun_pesan(items, sesi):
    """Kembalikan list pesan. split: 1 pesan per berita; digest: 1 pesan gabungan."""
    if not items:
        return []
    if CFG["send_mode"] == "digest":
        blok = [f"*{it['judul']}*\n{it['narasi']}\n\n{blok_link(it['link'])}" for it in items]
        return [sesi["salam"] + "\n\n" + "\n\n\n".join(blok)]

    pesan = []
    for i, it in enumerate(items):
        isi = f"{it['narasi']}\n\n{blok_link(it['link'])}"
        pesan.append(f"{sesi['salam']}\n\n{isi}" if i == 0 else isi)
    return pesan


# ==============================================================================
# PENGIRIMAN
# ==============================================================================
def kirim_whatsapp(daftar_pesan):
    if not CFG["fonnte_token"] or not CFG["wa_target"]:
        return None
    ok = True
    for i, pesan in enumerate(daftar_pesan):
        jeda = random.randint(4, 8) if i == 0 else random.randint(10, 20)
        time.sleep(jeda)
        try:
            res = requests.post(
                "https://api.fonnte.com/send",
                headers={"Authorization": CFG["fonnte_token"]},
                data={
                    "target": CFG["wa_target"],
                    "message": pesan,
                    "countryCode": "62",
                    "typing": "true",
                    "delay": str(random.randint(2, 5)),
                },
                timeout=30,
            ).json()
            log(f"[WA] Pesan {i + 1}/{len(daftar_pesan)}: {res}")
            ok = ok and res.get("status") is True
        except Exception as e:
            log(f"[WA] Gagal kirim pesan {i + 1}: {e}")
            ok = False
    return ok


def kirim_telegram(daftar_pesan):
    if not CFG["tg_token"] or not CFG["tg_chat"]:
        return None
    ok = True
    for i, pesan in enumerate(daftar_pesan):
        teks = re.sub(r"\*([^*\n]+)\*", r"\1", pesan)  # format bold WA -> teks biasa
        payload = {"chat_id": CFG["tg_chat"], "text": teks}
        if CFG["tg_thread"]:
            payload["message_thread_id"] = int(CFG["tg_thread"])
        try:
            res = requests.post(
                f"https://api.telegram.org/bot{CFG['tg_token']}/sendMessage",
                json=payload,
                timeout=30,
            ).json()
            log(f"[TG] Pesan {i + 1}/{len(daftar_pesan)}: ok={res.get('ok')}")
            ok = ok and bool(res.get("ok"))
        except Exception as e:
            log(f"[TG] Gagal kirim pesan {i + 1}: {e}")
            ok = False
        time.sleep(2)
    return ok


# ==============================================================================
# CEK KESEHATAN FEED
# ==============================================================================
def cek_feeds():
    urls = []
    for daftar in FEEDS.values():
        for s in daftar:
            if s["url"] not in urls:
                urls.append(s["url"])
    for url in urls:
        try:
            resp = requests.get(url, headers=BROWSER_HEADERS, timeout=20)
            feed = feedparser.parse(resp.content)
            umur = [umur_jam(e) for e in feed.entries if umur_jam(e) is not None]
            terbaru = f"{min(umur):.1f} jam lalu" if umur else "tanpa tanggal"
            print(f"{resp.status_code} | {len(feed.entries):>3} item | terbaru {terbaru:>14} | {url}")
        except Exception as e:
            print(f"ERR | {e.__class__.__name__}: {e} | {url}")


# ==============================================================================
# MAIN
# ==============================================================================
def kunci_proses():
    """Cegah dua proses jalan bersamaan (misalnya cron dobel)."""
    DATA_DIR.mkdir(exist_ok=True)
    try:
        import fcntl
    except ImportError:
        return None
    fh = open(LOCK_FILE, "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("Proses lain masih berjalan, keluar.")
        sys.exit(0)
    return fh


def main():
    parser = argparse.ArgumentParser(description="Daily news scraper -> WhatsApp/Telegram")
    parser.add_argument("--dry-run", action="store_true", help="Cetak pesan tanpa mengirim")
    parser.add_argument("--no-llm", action="store_true", help="Pakai ringkasan ekstraktif saja")
    parser.add_argument("--check-feeds", action="store_true", help="Cek kesehatan RSS feed")
    args = parser.parse_args()

    if args.check_feeds:
        cek_feeds()
        return

    _lock = kunci_proses()
    sesi = sesi_sekarang()
    log(f"Mulai sesi {sesi['nama']} (mode={CFG['send_mode']}, llm={'off' if args.no_llm else CFG['llm_model']})")

    riwayat = muat_riwayat()
    berita = ambil_berita(riwayat)
    items = susun_item(berita, sesi, pakai_llm=not args.no_llm)
    daftar_pesan = susun_pesan(items, sesi)

    if not daftar_pesan:
        log("Tidak ada berita baru untuk dikirim.")
        return

    if args.dry_run:
        for i, p in enumerate(daftar_pesan, 1):
            print(f"\n===== PESAN {i}/{len(daftar_pesan)} =====\n{p}")
        return

    hasil_wa = kirim_whatsapp(daftar_pesan)
    hasil_tg = kirim_telegram(daftar_pesan)

    if hasil_wa is None and hasil_tg is None:
        log("Tidak ada channel yang dikonfigurasi (Fonnte/Telegram). Isi pesan:")
        for p in daftar_pesan:
            print(f"\n{p}")
        return

    if hasil_wa or hasil_tg:
        simpan_riwayat(riwayat, items)
        log(f"Selesai. {len(items)} berita tercatat di riwayat.")
    else:
        log("Semua pengiriman gagal, riwayat tidak diperbarui agar bisa dicoba ulang.")
        sys.exit(1)


if __name__ == "__main__":
    main()
