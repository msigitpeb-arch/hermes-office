# Daily Tech News to WhatsApp Scraper — Documentation & History

> Dokumentasi arsitektur, histori konfigurasi, topik kurasi, alur pengiriman WhatsApp otomatis (Personal & Group) via GitHub Actions & Fonnte.

- **Repository GitHub:** [msigitpeb-arch/hermes-office](https://github.com/msigitpeb-arch/hermes-office), folder `news-scraper/` (sebelumnya repo wa-news-scraper)
- **Author:** msigitpeb-arch
- **Status:** Aktif (cron VPS 15:00 & 21:00 WIB, LLM via 9router). GitHub Actions hanya cadangan manual.
- **Terakhir Diperbarui:** 11 Oktober 2026

---

## 1. Arsitektur & Cara Kerja Sistem

```
┌──────────────────────────────────────────────┐
│  Eksternal Cron Trigger (cron-job.org)       │
│  • 15:00 WIB (08:00 UTC)                     │
│  • 21:00 WIB (14:00 UTC)                     │
└──────────────────────┬───────────────────────┘
                       │ (Trigger workflow_dispatch)
                       ▼
┌──────────────────────────────────────────────┐
│  GitHub Actions (Serverless Runner)          │
│  • Checkout repo & setup Python              │
│  • Eksekusi daily_scraper.py                 │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  daily_scraper.py                            │
│  • Scraping RSS Feed (Mongabay, CNN, CNBC,..)│
│  • Filter kata kunci & Fallback Global       │
│  • Formatting Stop-Slop (Natural & Bersih)   │
│  • Proteksi Anti-Ban (Typing + Random Sleep) │
└──────────────────────┬───────────────────────┘
                       │
                       ▼ (HTTP POST /send)
┌──────────────────────────────────────────────┐
│  Fonnte WhatsApp API Gateway                 │
│  • Device WhatsApp Terhubung                 │
└──────────────────────┬───────────────────────┘
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
┌─────────────────────┐     ┌─────────────────────┐
│ Nomor Personal WA   │     │ WhatsApp Group      │
│ (081511385636)      │     │ (NEWS / ...@g.us)   │
└─────────────────────┘     └─────────────────────┘
```

---

## 2. Trigger Eksternal Cron Job & Sapaan Dinamis

Trigger internal GitHub Actions (`schedule:`) **telah dihapus sepenuhnya** agar tidak terjadi tumpang-tindih atau delay antrean. Seluruh eksekusi kini 100% dikendalikan oleh **external cron job** (seperti cron-job.org atau server cron mandiri) yang menembak endpoint GitHub API `workflow_dispatch`.

Script secara otomatis menyesuaikan salam pembuka berdasarkan jam WIB saat cron job dieksekusi:

| Rentang Waktu (WIB) | Sapaan Otomatis |
|---|---|
| **05:00 - 10:59 WIB** | *"Pagi rekan-rekan, ada beberapa update penting seputar industri tech dan lingkungan hari ini:"* |
| **11:00 - 14:59 WIB** | *"Siang rekan-rekan, ada beberapa update penting seputar industri tech dan lingkungan hari ini:"* |
| **15:00 - 18:59 WIB** | *"Sore rekan-rekan, ada beberapa update penting seputar industri tech dan lingkungan hari ini:"* |
| **19:00 - 04:59 WIB** | *"Malam rekan-rekan, ada beberapa update penting seputar industri tech dan lingkungan hari ini:"* |

> **Cara Setup di cron-job.org:** Buat job baru dengan method `POST` ke URL GitHub API:
> `https://api.github.com/repos/msigitpeb-arch/wa-news-scraper/actions/workflows/main.yml/dispatches`
> dengan header `Authorization: Bearer <GITHUB_PAT>` dan body `{"ref": "main"}`.

---

## 3. Kurasi Topik & Prioritas 10 Portal Berita Indonesia

Sistem diprioritaskan penuh pada **10 portal berita nasional terpercaya dari Indonesia** (tanpa media asing) dengan sistem failover antar-kategori:

| No | Portal Berita | Domain | Kategori Utama & Fokus |
|---|---|---|---|
| 1 | **Antara News** | `antaranews.com` | Tech & Inovasi, Keamanan Siber, Isu Lingkungan (Kantor Berita Nasional) |
| 2 | **CNN Indonesia** | `cnnindonesia.com` | Cyber Security & Teknologi |
| 3 | **CNBC Indonesia** | `cnbcindonesia.com` | AI, Komputasi Cloud, & Data Center |
| 4 | **Detikcom (DetikINET)**| `inet.detik.com` | Tren Gadget, Cyber Security, & AI |
| 5 | **Mongabay Indonesia** | `mongabay.co.id` | Renewable Energy, Krisis Air, & Lingkungan Hidup |
| 6 | **Sindonews** | `sindonews.com` | Sains, Hardware, & Perkembangan Teknologi |
| 7 | **Katadata** | `katadata.co.id` | Ekonomi Hijau, Startup, & AI Digital |
| 8 | **Republika (Inovasi)** | `republika.co.id` | Transformasi Digital & Inovasi Sistem |
| 9 | **Jagat Review** | `jagatreview.com` | Review Hardware, Komponen PC, & Gadget |
| 10 | **Gizmologi** | `gizmologi.id` | Tren Perangkat Konsumen & Gadget Mobile |

---

## 4. Gaya Bahasa & Formatting (Stop-Slop 2 Paragraf Compact & Tuntas)

Formatting output disusun mengikuti prinsip **anti-slop padat, humanis, dan tuntas**:
1. **2 Paragraf Compact per Topik:** Setiap item berita menyajikan Judul Tebal diikuti tepat **2 paragraf padat** yang saling melengkapi (Paragraf 1: Fakta inti berita; Paragraf 2: Konteks lanjutan, dampak, atau latar belakang penting) dan diakhiri tautan sumber.
2. **Anti-Gantung (Penyelesaian Kalimat Terpotong):** Jika ringkasan bawaan RSS feed terpotong elipsis (`...`) di tengah jalan (seperti fenomena potongan kata "True Wireless Stereo ..."), sistem otomatis mengambil paragraf pertama dan kedua dari halaman web asli agar seluruh kalimat selesai utuh hingga tanda titik (`.`).
3. **Pembersihan Prefix Pers:** Menghapus tag kota dan media di awal teks secara presisi (misalnya `Jakarta (ANTARA) -` atau `Jakarta, CNN Indonesia --`) tanpa merusak akronim penting seperti `(TWS)`.
4. **Pembatas Bersih:** Menggunakan garis pembatas tipis (`─────────────────────`) dan format link langsung.

---

## 5. Pengiriman Target: Nomor Pribadi & WhatsApp Group

### A. Pengiriman ke WhatsApp Group (JID `@g.us`)
Fonnte mendukung pengiriman langsung ke grup WhatsApp dengan format ID: `<group_id>@g.us`.

* **Syarat:** Nomor WhatsApp yang terhubung di Fonnte (`081511385636`) harus **sudah menjadi anggota (member)** di grup WhatsApp target.
* **Helper Script (`ambil_id_grup.py`):**
  Untuk mengambil Group ID dari WhatsApp, jalankan:
  ```powershell
  python ambil_id_grup.py
  ```
  Script akan memanggil endpoint Fonnte:
  1. `POST https://api.fonnte.com/fetch-group` (sinkronisasi data grup dari device)
  2. `POST https://api.fonnte.com/get-whatsapp-group` (mengambil daftar nama dan ID grup)
* **Hasil Uji:** Berhasil terkirim langsung ke grup **NEWS** (`120363xxxxxx@g.us`).

### B. Konfigurasi `WA_TARGET_NUMBER` di GitHub Secrets
Buka menu repository: `Settings` → `Secrets and variables` → `Actions` → `WA_TARGET_NUMBER`:
* **Hanya ke WhatsApp Group:**
  ```text
  120363xxxxxxxxx@g.us
  ```
* **Multi-Target (Personal + WhatsApp Group):**
  Pisahkan dengan koma tanpa spasi:
  ```text
  081511385636,120363xxxxxxxxx@g.us
  ```

---

## 6. Proteksi Anti-Banned Fonnte & WhatsApp
1. **Typing Simulation (`typing: true`):** Fonnte memicu status *"Sedang mengetik..."* di WhatsApp sebelum pesan terkirim.
2. **Jeda Manusiawi Acak (Random Sleep):** Jeda waktu antara 3 hingga 7 detik sebelum mengeksekusi request HTTP ke gateway.
3. **Frekuensi Aman:** Hanya mengirim 2 kali per hari pada jam-jam wajar.
4. **Konten Dinamis:** Selalu memuat berita baru yang berbeda setiap eksekusi.

---

## 7. Changelog v2 (11 Oktober 2026): Pindah ke VPS + LLM via 9router

1. **Eksekusi pindah ke VPS:** cron lokal 15:00 & 21:00 WIB. Job cron-job.org dimatikan agar tidak dobel. Workflow GitHub tetap ada sebagai cadangan manual dengan `--no-llm`.
2. **Penulisan ulang oleh LLM:** isi artikel diambil lalu ditulis ulang oleh model/combo `scraping-news` di 9router (`http://127.0.0.1:20128/v1`). Gaya: rekan kerja membagikan bacaan, 2–3 paragraf, 70–140 kata, tanpa emoji, tanpa tanda seru, tanpa frasa klise.
3. **Salam baru:** "Selamat pagi/siang/sore/malam, {AUDIENCE}. ..." diikuti pembuka "Bacaan sore hari ini," pada berita pertama. Berita berikutnya dibuka frasa per kategori ("Dari sisi keamanan siber," dst).
4. **Mode kirim:** `split` (default, 1 pesan per berita agar preview link muncul) atau `digest`.
5. **Pengaman fakta:** angka di hasil LLM dicocokkan ke teks sumber. Ada angka asing → LLM diminta ulang sekali → kalau tetap ada, fallback ke ringkasan ekstraktif.
6. **Filter kata kunci kata utuh:** `ai` tidak lagi cocok dengan "pakai"/"ramai". Kata kunci terlalu umum (`air`, `data`, `teknologi`, `digital`, `sistem`, `keamanan`) diganti frasa spesifik (`krisis air`, `kebocoran data`, `keamanan siber`, dll).
7. **Tidak ada lagi fallback ke berita off-topic:** kalau sumber tidak punya berita cocok, langsung failover ke sumber berikutnya, bukan mengambil berita teratas yang tidak relevan.
8. **Anti-duplikat:** riwayat URL & judul 10 hari (`data/sent_history.json`), dedup antar kategori dalam satu sesi, dan batas umur berita 36 jam. Riwayat hanya ditulis kalau pengiriman berhasil.
9. **Channel Telegram opsional** (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
10. **Utilitas:** `--dry-run`, `--no-llm`, `--check-feeds`, lock file agar tidak jalan dobel, konfigurasi via `.env`.

## 8. Pindah ke repo hermes-office (11 Oktober 2026)
Kode dipindah ke `hermes-office/news-scraper/` agar semua otomasi Hermes ada di satu repo. Di VPS, folder kerja jadi `~/hermes-office/news-scraper` (migrasi dengan `migrate_from_wa_repo.sh`). Repo wa-news-scraper tidak dipakai lagi.
