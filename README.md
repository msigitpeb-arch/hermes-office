# Hermes Office

Virtual office untuk Hermes Agent di VPS SML: skill, persona (profile Hermes), script setup, dan news scraper harian.

| Folder | Isi |
|---|---|
| `skills/` | Skill Hermes (content-planning) |
| `team/` | SOUL.md tiap persona |
| `news-scraper/` | Berita harian 15:00 & 21:00 WIB ke Telegram/WhatsApp (dulu repo wa-news-scraper) |

## News scraper

Pindah dari `~/wa-news-scraper` yang sudah jalan:

```bash
cd ~ && git clone https://github.com/msigitpeb-arch/hermes-office.git
bash ~/hermes-office/news-scraper/migrate_from_wa_repo.sh
```

Script membawa `.env` dan riwayat berita, membuat venv, dan mengganti path di crontab. Detail lengkap di `news-scraper/README.md`.

## Skill & tim Hermes

```bash
cd ~/hermes-office
bash install_skills.sh <THREAD_ID_TOPIK_CONTENT_PLANNING> [THREAD_ID_TOPIK_CONTENT_REVIEWER]
bash setup_team.sh
```

Update: `cd ~/hermes-office && git pull`, lalu jalankan ulang kedua script di atas (aman diulang).

## content-planning
Content planner PeopleSync (tema: masalah SaaS dan keuntungan software sekali beli).
Alur: pembuat menyusun draft → pemeriksa (profile content-reviewer, model berbeda) mengoreksi dan memberi skor/approval → baris yang lolos disimpan ke `~/hermes-data/content-plan/peoplesync_content_plan.csv` dengan status "Menunggu review" → file CSV dikirim ke topik Telegram → SML membalas `approve CP-xxx`, `revisi CP-xxx <catatan>`, atau `tolak CP-xxx <alasan>`.

Pakai di Telegram: `/content-planning buat content plan 2 minggu untuk PeopleSync`

Perintahnya tidak kaku. `install_skills.sh` memasang alias `/konten`, `/cp`, `/content-plan`, `/content-planing`, dan `/contentplanning`. Alias tanpa tanda hubung (`/konten`, `/cp`) bisa masuk menu perintah Telegram, yang hanya menerima huruf kecil, angka, dan garis bawah. Pesan biasa tanpa garis miring ("buat content plan seminggu") juga dilayani.

### Approval reviewer
Reviewer meloloskan konten hanya kalau tiga hal ini terpenuhi (detail di `skills/content-planning/references/checker-rubric.md`):

| Gerbang | Lolos kalau | Gagal |
|---|---|---|
| Skor konten | ≥ 80 dan fakta sesuai brief | revisi |
| SEO, GEO, AEO (`skor_seo`) | ≥ 80 | revisi |
| Anti AI slop (`slop_check.py`) | `skor_slop` ≤ 20, dan `skor_ai` < 50 kalau detektor aktif | tulis ulang dari nol |

Hasil pemeriksaan tiap putaran dan ringkasan tiap konten dikirim ke topik Content Reviewer (thread kedua di `install_skills.sh`). Laporan akhir dan CSV dikirim ke thread pertama. Di VPS SML keduanya diarahkan ke topik 03.1 dengan `bash install_skills.sh 59 59`, sehingga topik 03 hanya dipakai untuk memberi perintah.

`slop_check.py` menghitung pola tulisan mesin secara lokal (frasa klise, pola "bukan X, melainkan Y", ritme kalimat seragam, dan sejenisnya). Untuk menambah skor dari situs detektor AI, isi di `~/hermes-data/content-plan/config.env`:

```
AI_DETECTOR=sapling        # atau gptzero
AI_DETECTOR_KEY=<api key>
```

Rubrik memeriksa faktor yang bisa dikendalikan dari sisi konten. Terindeks, ranking, traffic, dan leads baru bisa dibuktikan di Search Console setelah konten tayang.

### Rekam ke Google Sheets
Google Sheets hanya menerima konten yang sudah di-approve SML. Setiap kali `save_plan.py` menyimpan konten atau mengubah status, baris berstatus Approved dikirim ke sana; konten yang masih menunggu review hanya ada di CSV. Baris dicocokkan lewat `id`: yang sudah ada ditimpa, yang baru ditambahkan, tidak ada yang dihapus (baris yang approval-nya dicabut tetap tampil dengan status lamanya). CSV tetap menjadi sumber utama; kalau kiriman ke Sheets gagal, penyimpanan CSV tidak batal.

Pasang sekali:

1. Buka spreadsheet tujuan → Extensions → Apps Script. Tempel isi `skills/content-planning/references/google-sheet-webhook.gs`, lalu ganti `TOKEN` dengan teks acak yang panjang.
2. Deploy → New deployment → Web app. Execute as: **Me**. Who has access: **Anyone**. Salin URL yang berakhiran `/exec`.
3. Di VPS, tambahkan ke `~/hermes-data/content-plan/config.env`:
   ```
   SHEET_WEBHOOK_URL=https://script.google.com/macros/s/.../exec
   SHEET_TOKEN=<token yang sama>
   ```
4. Kirim semua baris Approved yang sudah ada: `python3 ~/.hermes/skills/marketing/content-planning/scripts/save_plan.py sheet`

Data masuk ke tab "Content Plan". URL web app bisa dipanggil siapa saja, jadi `TOKEN` adalah satu-satunya pengaman: jangan ditaruh di repo atau di screenshot. Setiap kali isi Apps Script diubah, buat deployment versi baru supaya perubahan berlaku.

## Tim (virtual office)

`setup_team.sh` membuat tim berbasis profile Hermes + Kanban:

| Profile | Peran | Model (via 9router) |
|---|---|---|
| default (lead) | Ngobrol dengan SML, membuat kartu Kanban | ag/gemini-3.8-flash |
| content-planner | Rencana: pilar, funnel, hook, outline, CTA | cx/gpt-5.6-sol |
| content-writer | Naskah final per konten | ag/claude-opus-4-6-thinking |
| content-reviewer | Koreksi + approval, loop dengan writer sampai approve (batas aman 6 putaran), simpan CSV + lapor | cx/gpt-5.6-sol |

```bash
cd ~/hermes-office && git pull
bash setup_team.sh
```

Semua profile dilayani satu gateway (`gateway.multiplex_profiles: true`). Worker hanya jalan sebagai proses saat ada kartu Kanban, jadi tidak memakan RAM saat idle.

Mission Control 3D: [Ruang](https://github.com/yugienugraha/ruang) (read-only, membaca lewat `hermes` CLI).

## Ruang (Mission Control 3D)

```bash
curl -fsSL https://raw.githubusercontent.com/yugienugraha/ruang/main/install.sh | bash -s -- --service
bash ~/hermes-office/ruang_patch_timeout.sh     # wajib di VPS 2 vCPU, ulangi setiap update Ruang
```

Buka lewat tunnel: `ssh -L 3001:127.0.0.1:3001 ubuntu@IP_VPS`, lalu http://127.0.0.1:3001. Tutup tab Ruang kalau tidak dipakai, karena polling-nya ikut memakan CPU agent.

## Brain (second brain)

Arsip pengetahuan jangka panjang: catatan, tautan, hasil riset, dan fakta produk disimpan sebagai Markdown lalu dicari kembali lewat Telegram. Ringan: SQLite FTS5 dan satu script Python, tanpa Docker, tanpa model embedding, tanpa layanan yang terus hidup.

```bash
cd ~/hermes-office && git pull && bash install_brain.sh
```

Pakai di Telegram: `/simpan <isi atau tautan>`, `/cari <pertanyaan>`, atau cukup "simpan ini" dan "apa yang gw tau soal X".

| Lokasi | Isi |
|---|---|
| `~/hermes-data/brain/knowledge/<kategori>/` | Catatan Markdown dengan frontmatter (bisa dibuka di Obsidian) |
| `~/hermes-data/brain/brain.db` | Indeks pencarian; bisa dibangun ulang dari file |

Kategori: `produk` (fakta PeopleSync terkonfirmasi), `riset`, `artikel`, `ide`, `notes`.

Mengindeks folder Markdown yang sudah ada, misalnya salinan vault Obsidian (file tidak disalin, jalankan lagi setelah folder berubah):

```bash
python3 ~/.hermes/skills/productivity/brain/scripts/brain.py ingest ~/vault --category vault
```

Menyimpan file beserta isinya (.pdf, .docx, .md, .txt, .csv): `brain.py add-file <file> --title "..."`. File asli disalin ke `~/hermes-data/brain/files/`, teksnya diindeks per bagian (heading atau halaman), sehingga hasil pencarian menyebut dokumen dan bagiannya. PDF butuh `sudo apt install -y poppler-utils`.

Batasan versi ini: pencarian berbasis kata, bukan makna, jadi agen memperluas pertanyaan dengan sinonim sebelum mencari. PDF hasil pindai (tanpa teks), .xlsx, .pptx, dan gambar belum didukung. Catatan yang tampak memuat API key, token, atau password ditolak.

### Satu vault untuk brain, obsidian, dan llm-wiki
Skill bawaan Hermes `obsidian` dan `llm-wiki` diarahkan ke folder catatan brain, supaya semua pengetahuan ada di satu tempat. Tambahkan ke `~/.hermes/.env`, lalu restart gateway:

```
OBSIDIAN_VAULT_PATH=/home/ubuntu/hermes-data/brain/knowledge
WIKI_PATH=/home/ubuntu/hermes-data/brain/knowledge/wiki
```

Tidak perlu cron. Setiap `search` lebih dulu menyamakan indeks dengan isi folder `knowledge/`: halaman baru atau yang diedit (oleh kedua skill itu, atau dari Obsidian di PC) langsung bisa dicari, dan halaman yang dihapus hilang dari hasil. File yang tidak berubah tidak dibaca ulang, jadi tambahan waktunya kecil. Kategori diambil dari nama subfolder pertama; catatan buatan `add` mempertahankan kategorinya.
