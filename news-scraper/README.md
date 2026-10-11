# Daily News Scraper → WhatsApp / Telegram

Mengirim bacaan berita harian (Lingkungan & Energi, Keamanan Siber, AI & Data Center, Tech) ke WhatsApp (Fonnte) dan/atau Telegram, dua kali sehari: **15:00 WIB** (sore) dan **21:00 WIB** (malam). Berita ditulis ulang oleh LLM lewat 9router dengan gaya rekan kerja yang membagikan bacaan.

Contoh hasil (mode `split`, 1 pesan per berita):

```
Selamat sore, rekan-rekan SML. Terima kasih atas kerja kerasnya hari ini.

Bacaan sore hari ini, kebakaran TPA Jatiwaringin di Tangerang dinyatakan 100 persen padam dan
masuk fase pendinginan. ...

Langkah mitigasi yang bisa kita lakukan ...

Selengkapnya bisa dibaca di sini:
https://...
```

## Cara kerja

1. Ambil RSS per kategori dengan failover antar sumber.
2. Pilih 1 berita per kategori: umur maksimal 36 jam, cocok kata kunci (kata utuh), belum pernah dikirim (riwayat 10 hari di `data/sent_history.json`), dan tidak dobel antar kategori.
3. Ambil isi artikel asli, lalu LLM menulis 2–3 paragraf. Angka di hasil LLM dicek ke teks sumber; kalau ada angka yang tidak ada di sumber, LLM diminta menulis ulang. Kalau tetap gagal atau 9router mati, script otomatis pakai ringkasan ekstraktif.
4. Kirim ke channel yang dikonfigurasi, lalu catat URL ke riwayat (hanya kalau minimal satu channel berhasil).

## Setup di VPS

```bash
cd ~
git clone https://github.com/msigitpeb-arch/hermes-office.git
cd hermes-office/news-scraper
sudo apt install -y python3-venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env
nano .env          # isi LLM_API_KEY, FONNTE_TOKEN, WA_TARGET_NUMBER, dll
chmod 600 .env
```

Tes:

```bash
.venv/bin/python daily_scraper.py --check-feeds   # cek semua RSS
.venv/bin/python daily_scraper.py --dry-run       # lihat hasil tanpa mengirim
.venv/bin/python daily_scraper.py --dry-run --no-llm
```

Jadwal (timezone VPS harus `Asia/Jakarta`, cek dengan `timedatectl`):

```bash
mkdir -p logs
crontab -e
```

Tambahkan:

```
0 15 * * * cd $HOME/hermes-office/news-scraper && .venv/bin/python daily_scraper.py >> logs/cron.log 2>&1
0 21 * * * cd $HOME/hermes-office/news-scraper && .venv/bin/python daily_scraper.py >> logs/cron.log 2>&1
```

Update kode di kemudian hari: `cd ~/hermes-office && git pull`.

## Konfigurasi (`.env`)

| Variabel | Fungsi |
|---|---|
| `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` | Endpoint 9router, key, dan model/combo (default `scraping-news`) |
| `FONNTE_TOKEN`, `WA_TARGET_NUMBER` | WhatsApp via Fonnte. Target bisa nomor, grup `xxx@g.us`, atau gabungan dipisah koma |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Opsional, kirim juga ke Telegram |
| `AUDIENCE` | Disebut di salam, misalnya `rekan-rekan SML` |
| `SEND_MODE` | `split` (1 pesan per berita) atau `digest` (1 pesan gabungan) |
| `MAX_AGE_HOURS` | Batas umur berita (default 36) |

Salam menyesuaikan jam kirim: 04–10 pagi, 11–14 siang, 15–18 sore, selainnya malam.

## Menambah atau mengganti sumber

Edit `FEEDS` di `daily_scraper.py`. Sumber tanpa `filter` mengambil berita terbaru apa saja; sumber dengan `filter` hanya mengambil berita yang judul/ringkasannya cocok kata kunci (kata utuh). Urutan sumber = urutan failover.

## GitHub Actions

`.github/workflows/news-scraper.yml` (di root repo) hanya cadangan manual (`--no-llm`), karena runner GitHub tidak bisa menjangkau 9router di VPS. Butuh secret `FONNTE_TOKEN` dan `WA_TARGET_NUMBER` di repo hermes-office. Matikan job di cron-job.org supaya tidak terkirim dobel dengan cron VPS.

## Helper

`ambil_id_grup.py` untuk mengambil ID grup WhatsApp (`xxx@g.us`) dari Fonnte.
