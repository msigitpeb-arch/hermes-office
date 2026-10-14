---
name: content-planning
description: Content planner PeopleSync. Menyusun content plan bertema masalah SaaS dan keuntungan software sekali beli, lewat alur pembuat lalu pemeriksa (koreksi + approval dengan gerbang SEO/GEO/AEO dan anti AI slop), lalu menyimpan hasilnya ke spreadsheet untuk direview SML. Pakai juga untuk permintaan yang salah ketik seperti "content planing" atau "konten plan".
version: 2.1.0
author: SML
metadata:
  hermes:
    tags: [marketing, content, peoplesync, indonesia]
---

# Content Planning: PeopleSync

## When to Use
- User minta content plan, kalender konten, ide konten, atau ide posting untuk PeopleSync.
- User minta konten seputar masalah SaaS, biaya langganan, atau keuntungan software sekali beli.
- User membalas review content plan (approve, revisi, atau tolak per ID).
- Permintaan tidak harus diawali `/content-planning`. Pesan biasa seperti "buat content plan seminggu" atau alias `/konten`, `/cp`, `/content-plan` diperlakukan sama.

## Quick Reference
- Brief produk (SATU-SATUNYA sumber fakta): `${HERMES_SKILL_DIR}/references/peoplesync-brief.md`
- Rubrik pemeriksa: `${HERMES_SKILL_DIR}/references/checker-rubric.md`
- Standar artikel Website (WAJIB untuk Artikel Blog dan Berita Website): `${HERMES_SKILL_DIR}/references/article-standard.md`
- Cek AI slop: `python3 ${HERMES_SKILL_DIR}/scripts/slop_check.py <file.json>`
- Simpan dan kirim ke Telegram: `python3 ${HERMES_SKILL_DIR}/scripts/save_plan.py`
- Hasil pemeriksaan ke topik Content Reviewer: `save_plan.py notify --to reviewer @<file>`
- Tampilkan ringkasan konten di topik Content Reviewer: `save_plan.py detail <ID,ID>` atau `save_plan.py detail --status "Menunggu review"`
- File spreadsheet: `~/hermes-data/content-plan/peoplesync_content_plan.csv`

## Mode Tim (Kanban): dipakai kalau profile `content-planner`, `content-writer`, dan `content-reviewer` ada

Langkah PERTAMA, sebelum menulis apa pun: jalankan `hermes profile list` lewat terminal. Kalau ketiga profile ada, kamu WAJIB memakai mode tim ini sesuai peranmu. Dilarang mengerjakan peran lain.

Alur: LEAD → PLANNER (rencana) → WRITER (naskah) ⇄ REVIEWER (koreksi + approval, berulang sampai approve) → CSV + laporan ke SML.

Semua file kerja di `~/hermes-data/content-plan/drafts/`. Ganti `<run>` dengan ID kartu planner (misalnya `t_201a25d8`) supaya semua peran memakai nama file yang sama.

**Kalau kamu LEAD (profile default, sedang ngobrol dengan SML):**
1. Buat kartu untuk planner. Pakai tool `kanban_create` kalau tersedia:
   `kanban_create(title="Content plan PeopleSync: <ringkas permintaan>", assignee="content-planner", body="<permintaan SML lengkap: periode, jumlah konten, platform, catatan khusus>. Pakai skill content-planning, peran CONTENT-PLANNER.")`
   Kalau tool tidak ada: `hermes kanban create "Content plan PeopleSync: <ringkas>" --assignee content-planner`, lalu `hermes kanban comment <id> "<isi body>"`.
   Setelah kartu dibuat, boleh menjalankan `hermes kanban dispatch` supaya worker langsung mulai tanpa menunggu giliran polling gateway.
   Jangan pernah menjalankan `hermes kanban unblock`, `promote`, atau `reclaim` atas inisiatif sendiri. Kartu berstatus `blocked` bisa jadi sengaja dihentikan SML. Kalau menurutmu ada kartu yang tertahan tanpa sengaja, sebutkan ID-nya ke SML dan tunggu perintah.
2. Balas SML satu kali: kartu sudah dibuat, tim bekerja, dan hasilnya (laporan tiap putaran, ringkasan konten, file CSV) akan muncul di topik Content Reviewer (03.1), bukan di topik tempat permintaan dikirim. Jangan memantau atau melapor progres.
3. Untuk review SML (approve / revisi / tolak), ikuti langkah 6. Revisi dikirim sebagai kartu baru ke `content-writer` dengan ID baris dan catatan SML di body, lalu tetap lewat reviewer.

**Kalau kamu CONTENT-PLANNER (strategi, worker Kanban):**
1. Kerjakan langkah 0-1 TANPA menulis naskah: isi semua field kecuali `naskah`. Fokus pada strategi: sebaran pilar dan funnel, angle tiap konten, hook, outline, CTA, dan `sumber_klaim`.
   - Field pencarian (`keyword`, `negara_bahasa`, `search_intent`, `meta_title`, `meta_description`, `slug`, `faq`) diisi olehmu. Kalau tool pencarian web tersedia, cari dulu keyword utamanya: pastikan memang dicari orang, lihat pertanyaan yang muncul di hasil teratas, dan pilih sudut yang belum dibahas di sana.
   - Jalankan `save_plan.py show` supaya keyword dan sudut pandang tidak mengulang konten yang sudah ada.
2. Simpan ke `drafts/<run>-plan.json` (ganti `<run>` dengan ID kartumu).
3. Buat kartu untuk writer: `kanban_create(title="Naskah content plan <run>", assignee="content-writer", body="Rencana di ~/hermes-data/content-plan/drafts/<run>-plan.json. Tulis naskah tiap baris. Pakai skill content-planning, peran CONTENT-WRITER. Run ID: <run>.", max_runtime_seconds=3600)`
   Batas waktu wajib 3600. Jangan mengisi 0: nol dibaca sebagai batas nol detik, bukan "tanpa batas", dan writer akan dimatikan di detik ke-60.
4. `kanban_complete` dengan ringkasan: jumlah konten, sebaran pilar dan funnel.

**Kalau kamu CONTENT-WRITER (penulis, worker Kanban):**
1. Baca `drafts/<run>-plan.json` dan brief produk. Untuk baris platform Website, baca juga `article-standard.md` sampai habis SEBELUM menulis, ikuti format frontmatter situs di sana, dan centang checklist-nya sebelum mengirim. Untuk setiap baris, isi field `naskah`: teks final yang siap diposting sesuai platform dan format.
   - LinkedIn Single Post / Artikel: 120-250 kata, paragraf pendek, hook di baris pertama.
   - Instagram Carousel: tulis per slide, format `Slide 1: ... | Slide 2: ...` (5-8 slide), lalu `Caption: ...`.
   - Reel: `Hook (0-3 dtk): ... | Isi: ... | Penutup: ...` lalu `Caption: ...`.
   - Artikel Blog (Website): 800-1.500 kata dalam Markdown, mengikuti "Kerangka konten Website" di bawah.
   - Berita Website: 400-700 kata dalam Markdown. Piramida terbalik: paragraf pertama menjawab apa, siapa, kapan, dan dampaknya bagi HR atau finance. Wajib berangkat dari peristiwa atau aturan nyata yang punya sumber bertanggal. Tanpa sumber, jangan ditulis sebagai berita; ubah menjadi Artikel Blog.
   - Selalu akhiri dengan CTA dari baris itu.
   - Sumber fakta dibedakan dua:
     - Klaim tentang PeopleSync (fitur, harga, garansi, cara kerja) HANYA dari brief.
     - Fakta umum HR, payroll, pajak, dan regulasi boleh dipakai kalau kamu menemukannya lewat pencarian web dan mencantumkan sumbernya (nama lembaga atau media, tahun, URL) di bagian "Sumber" dan di `sumber_klaim`. Tidak ketemu sumbernya = jangan ditulis. Angka contoh buatan sendiri wajib diberi label "ilustrasi" lengkap dengan asumsinya.

   Kerangka konten Website (inilah yang membuat SEO dan GEO-nya kuat):
   1. H1 memuat keyword utama, paling panjang 60 karakter.
   2. Blok "Ringkasan" tepat di bawah H1: 2-3 kalimat (40-60 kata) yang langsung menjawab pertanyaan pencari dan bisa dikutip utuh tanpa membaca sisanya.
   3. Keyword utama muncul di 100 kata pertama, di satu H2, dan di `meta_title`, `meta_description`, `slug`. Sisanya memakai variasi dan istilah terkait, bukan pengulangan.
   4. H2/H3 berupa pertanyaan atau frasa yang benar-benar dicari. Di bawah tiap heading pertanyaan ada jawaban langsung 40-60 kata, baru penjelasannya.
   5. Paling sedikit satu tabel (perbandingan atau hitungan) dan satu daftar bernomor (langkah atau checklist).
   6. Paling sedikit tiga kalimat kunci yang berdiri sendiri: menyebut subjeknya dengan nama, memuat angka beserta satuan, periode, dan asumsinya. Contoh: "Pada simulasi 100 karyawan dengan tarif Rp 45.000 per user per bulan, biaya langganan software payroll mencapai Rp 162 juta dalam 3 tahun."
   7. Definisi istilah penting ditulis satu kalimat dengan pola "X adalah ...".
   8. Nama entitas konsisten dari awal sampai akhir ("PeopleSync", "HR & payroll on-premise").
   9. Bagian "FAQ" dari field `faq`, lalu bagian "Sumber" berisi daftar rujukan fakta umum.
   10. Paling sedikit satu tautan ke peoplesync.id dan satu CTA sesuai funnel.
   - Ikuti "Aturan Bahasa" di bawah, terutama bagian menulis seperti manusia.
2. Simpan semua baris (field rencana + `naskah`) ke `drafts/<run>-copy.json`.
3. Cek sendiri sebelum mengirim: `python3 ${HERMES_SKILL_DIR}/scripts/slop_check.py ~/hermes-data/content-plan/drafts/<run>-copy.json`. Baris dengan `lolos: false` ditulis ulang dulu. Jangan mengirim naskah yang kamu tahu akan gagal.
4. `kanban_request_review` dengan reviewer `content-reviewer` dan summary: path file, jumlah konten, dan putaran revisi ke berapa.
5. Kalau kartu kembali dengan permintaan perubahan, timpa file `-copy.json`, lalu ulangi langkah 3-4:
   - Keputusan "revisi": perbaiki HANYA baris dan bagian yang dikoreksi.
   - Keputusan "tulis_ulang": field `naskah` baris itu sudah dikosongkan reviewer. Tulis dari kertas kosong dengan pembuka dan susunan yang berbeda. Jangan membuka file arsip `*.ditolak-*.json` dan jangan mengulang kerangka lama. Field rencana (hook, keyword, outline) tetap dipakai.
   - Jangan membantah koreksi; kalau koreksi bertentangan dengan brief, ikuti brief dan jelaskan singkat di summary.

**Kalau kamu CONTENT-REVIEWER (editor + approval):**
1. Jalankan `slop_check.py` pada `drafts/<run>-copy.json`, lalu baca filenya. Nilai SETIAP baris (rencana DAN naskah) dengan `checker-rubric.md` dan `peoplesync-brief.md`. Baris platform Website juga diperiksa terhadap setiap aturan bernomor dan daftar frasa terlarang di `article-standard.md`; buka sendiri dokumen sumber untuk setiap angka regulasi, jangan cukup melihat ada sumbernya. Keputusan per baris: "approve", "revisi", atau "tulis_ulang".
2. Hitung putaran: lihat riwayat kartu (`kanban_show`), jumlah `request_changes` sebelumnya + 1.
3. Setiap putaran, kirim hasil pemeriksaan ke topik Content Reviewer. Tulis ke file, lalu `save_plan.py notify --to reviewer @<file>`. Format persis, satu baris per konten, tanpa heading, tabel, atau bold:
   ```
   Review <run> · putaran <n>
   <ID> · APPROVE · skor <n> · SEO <n> · slop <n> · AI <n atau n/a>
   <ID> · REVISI · skor <n> · SEO <n> · slop <n> · AI <n atau n/a> · <alasan satu kalimat>
   <ID> · TULIS ULANG · slop <n> · AI <n atau n/a> · <temuan utama>
   Hasil: <a> approve, <b> revisi, <c> tulis ulang. <Dikembalikan ke writer. | Disimpan ke CSV, ringkasan menyusul di topik ini.>
   ```
4. Ada baris yang belum layak approve:
   - Untuk baris "tulis_ulang", kosongkan dulu naskahnya supaya writer tidak bisa menambal versi lama: `python3 ${HERMES_SKILL_DIR}/scripts/save_plan.py kosongkan ~/hermes-data/content-plan/drafts/<run>-copy.json <ID,ID>`. Versi lama diarsipkan otomatis.
   - Lalu `kanban_request_changes` berisi koreksi per ID dalam format JSON rubrik. Kartu kembali ke writer. Ulangi sampai semua baris approve.
5. **Batas aman: putaran ke-6.** Kalau di putaran ke-6 masih ada baris yang gagal, jangan kirim balik lagi. Simpan baris yang sudah approve (langkah 6), lalu `kanban_block` dengan alasan, dan kirim eskalasi ke SML:
   `python3 ${HERMES_SKILL_DIR}/scripts/save_plan.py notify "Eskalasi content plan <run>: <n> konten belum lolos setelah 6 putaran. ID: <...>. Masalah utama: <ringkas>. Balas dengan arahan, atau minta lead membuat ulang."`
6. Semua baris approve → isi `skor_checker`, `skor_seo`, `skor_slop`, `skor_ai`, `catatan_checker`, `revisi_ke` (jumlah putaran), `status` = "Menunggu review", `catatan_sml` = "". Simpan dengan langkah 4 Procedure (save_plan.py add ... --send). Dengan `--send`, script juga menampilkan ringkasan tiap konten yang disimpan (skor, hook, pesan utama, keyword, CTA, catatan) sebagai pesan di topik Content Reviewer. Naskah lengkap ada di CSV; konten yang belum di-approve TIDAK dimasukkan ke Google Sheets (hanya konten Approved yang disinkronkan). Jangan menyalin naskah lengkap ke chat.
7. Kirim laporan langkah 5 Procedure dengan menulisnya ke file lalu `save_plan.py notify @<file>`. Tujuannya topik review di `config.env`, yang di setup ini sama dengan topik Content Reviewer (03.1). Setelah itu `kanban_complete`.

Kalau SML bertanya langsung di topik Content Reviewer ("sudah approve belum?", "status CP-xxx?"), jawab dari data, bukan ingatan: `save_plan.py show` untuk yang sudah disimpan dan `hermes kanban list` untuk yang masih dikerjakan.

Kalau profile tim tidak lengkap, kerjakan seluruh Procedure sendiri seperti di bawah, termasuk menulis `naskah`.

## Procedure

### 0. Pahami permintaan
Default kalau user tidak menyebut: 2 minggu, 3 konten per minggu, mulai Senin terdekat. Tanya HANYA kalau permintaannya bertentangan dengan brief.

Platform ditentukan oleh isi permintaan, bukan dicampur:
- User menyebut artikel, berita, news, blog, atau website → SEMUA baris `platform` = "Website". Pakai `format` "Artikel Blog" untuk artikel dan "Berita Website" untuk berita/news. Jangan menyisipkan konten Instagram atau LinkedIn.
- User menyebut platform lain secara eksplisit (misal "untuk LinkedIn saja") → ikuti persis.
- Tidak menyebut satu pun dari itu → normal: LinkedIn + Instagram dengan format sosial (Carousel, Reel, Single Post, Artikel LinkedIn, Thread).
- Kata SEO, GEO, AEO, atau ranking saja TIDAK mengubah platform. Kata-kata itu hanya menaikkan tuntutan pencarian pada platform yang sudah terpilih.

- "Setiap hari 1 konten" berarti 7 konten per minggu, satu `tanggal_tayang` per hari.
- `negara_bahasa` default "Indonesia / id". Kalau user minta banyak negara, PeopleSync tetap produk untuk perusahaan di Indonesia: buat versi "Global / en" untuk pencari berbahasa Inggris yang mengurus HR atau payroll di Indonesia (kantor regional, investor, konsultan). Jangan menulis seolah PeopleSync mengikuti aturan pajak atau ketenagakerjaan negara lain. Versi bahasa lain mendapat baris dan ID sendiri.

### 1. PEMBUAT (Maker): susun draft
Baca brief produk dulu. Lalu susun konten sebagai JSON array dengan field berikut (semua wajib, string):

`id` (format CP-YYYYMMDD-NN), `tanggal_tayang` (YYYY-MM-DD), `platform`, `format` (Carousel, Reel, Single Post, Artikel LinkedIn, Thread untuk sosial; Artikel Blog, Berita Website untuk website), `pilar`, `funnel` (TOFU, MOFU, BOFU), `judul_hook`, `pesan_utama` (1-2 kalimat), `outline` (poin-poin dipisah " | "), `cta`, `keyword` (keyword utama di depan, lalu turunannya, dipisah koma), `negara_bahasa` (misal "Indonesia / id"), `search_intent` (informasional, komersial, atau transaksional), `meta_title` (≤ 60 karakter), `meta_description` (140-160 karakter), `slug`, `faq` (3-5 tanya-jawab, format `T: ... J: ...` dipisah " | "), `sumber_klaim` (bagian brief yang dipakai, atau "-" kalau tidak ada klaim produk), `naskah` (teks final siap posting; di mode tim diisi oleh writer).

Untuk format sosial pendek (Carousel, Reel, Single Post, Thread), `meta_title`, `meta_description`, `slug`, dan `faq` diisi "-".

Aturan pembuat:
- Pakai lima pilar di brief dengan porsi seimbang. Funnel kira-kira 50% TOFU, 30% MOFU, 20% BOFU.
- Konten TOFU membahas masalah pembaca (HR, finance, owner), bukan jualan. Produk baru muncul di MOFU dan BOFU.
- Hook spesifik dan konkret. Hindari hook generik seperti "Tahukah kamu?".
- Setiap klaim produk HARUS ada di brief. Angka penghematan wajib ditulis sebagai simulasi, bukan janji.
- Fakta umum di luar produk (regulasi, statistik, praktik industri) hanya boleh dipakai dengan sumber yang bisa dibuka. Tulis sumbernya di `sumber_klaim`.
- Untuk konten Website, pilih keyword yang benar-benar dicari: cari dulu di web, lihat pertanyaan yang muncul di hasil teratas, dan pakai pertanyaan itu sebagai H2 serta isi `faq`.
- Jangan menyebut atau menjelekkan merek kompetitor.

### 2. PEMERIKSA (Checker): koreksi + approval
Pemeriksa harus independen dari pembuat. Gunakan `delegate_task` untuk subagent pemeriksa dengan konteks HANYA: isi `checker-rubric.md`, isi `peoplesync-brief.md`, dan JSON draft. Jangan ikut sertakan alasan pembuat.

Sebelum menyerahkan ke pemeriksa, jalankan `slop_check.py` pada file draft dan sertakan keluarannya.

Minta pemeriksa mengembalikan JSON array sesuai rubrik: `{"id", "skor", "skor_seo", "skor_slop", "skor_ai", "keputusan" ("approve" | "revisi" | "tulis_ulang"), "koreksi" (apa yang salah + saran perbaikan konkret)}`.

Kalau `delegate_task` tidak tersedia, lakukan pemeriksaan sebagai langkah terpisah: baca ulang rubrik, lalu nilai setiap baris seolah-olah melihat draft orang lain.

### 3. Revisi
- Baris "revisi": pembuat memperbaiki sesuai koreksi, lalu kirim ulang ke pemeriksa.
- Baris "tulis_ulang": naskah dibuang dan ditulis dari awal, lalu kirim ulang ke pemeriksa.
- Maksimal 2 putaran. Baris yang tetap gagal setelah 2 putaran dibuang dan disebut di laporan.

### 4. Simpan dan kirim untuk review SML
Tambahkan ke setiap baris yang lolos: `skor_checker`, `skor_seo`, `skor_slop`, `skor_ai`, `catatan_checker` (ringkas apa yang sudah dikoreksi), `status` = "Menunggu review", `catatan_sml` = "".
Tulis JSON ke file BARU dengan nama unik (jangan memakai ulang file lama), lalu jalankan:

```
BATCH=~/hermes-data/content-plan/drafts/batch-$(date +%Y%m%d-%H%M%S).json
# tulis JSON ke $BATCH, lalu:
python3 ${HERMES_SKILL_DIR}/scripts/save_plan.py add $BATCH --send
```

Kalau penulisan file gagal, BERHENTI dan laporkan errornya ke SML. Jangan lanjut menyimpan atau melapor seolah berhasil. Laporan langkah 5 harus memakai ID dan jumlah dari output script (`OK ... baru: n, diperbarui: n, id: ...`), bukan dari ingatanmu.

Script menyimpan ke CSV (baris dengan ID sama akan ditimpa) dan mengirim file CSV ke topik Telegram review.

### 5. Laporan ke user (format WAJIB, jangan diubah)
Kirim SATU pesan saja setelah semua langkah selesai. Jangan kirim pesan progres, narasi langkah ("sekarang saya memeriksa..."), JSON, atau isi CSV ke chat. Detail lengkap ada di file CSV.

Format persis seperti ini (isi bagian dalam <>, baris kosong antar konten):

```
Content plan PeopleSync siap direview
<tgl mulai>–<tgl selesai> · <n> konten · lolos pemeriksa <n>/<total draft>
Funnel: TOFU <n> · MOFU <n> · BOFU <n>

<ID> · <Hari tgl/bln> · <Platform> <Format> · <Funnel>
<judul_hook>

<ID> · <Hari tgl/bln> · <Platform> <Format> · <Funnel>
<judul_hook>

Dibuang: <ID: alasan singkat>   ← hapus baris ini kalau tidak ada yang dibuang

Detail lengkap ada di file CSV di topik ini.
Balas: approve CP-xxx · revisi CP-xxx <catatan> · tolak CP-xxx <alasan>
```

Contoh satu konten:
```
CP-20261014-02 · Rab 14/10 · Instagram Carousel · TOFU
Simulasi biaya software payroll 100 karyawan selama 3 tahun: sewa vs beli putus
```

Larangan format: tanpa heading (#), tanpa tabel, tanpa bullet bertingkat, tanpa bold/italic, tanpa garis pemisah (— atau ---), tanpa skor checker, tanpa nama pilar di daftar. Satu konten = dua baris.

### 6. Saat user mereview
- `approve <ID>` → `python3 ${HERMES_SKILL_DIR}/scripts/save_plan.py status <ID> "Approved"` (otomatis disinkronkan ke Google Sheets)
- `tolak <ID> <alasan>` → status "Ditolak" dengan catatan alasan
- `revisi <ID> <catatan>` → perbaiki baris itu, ulangi langkah 2 untuk baris itu saja, lalu simpan dengan status "Menunggu review" dan catatan_sml berisi catatan user.
Untuk status dengan catatan: `save_plan.py status <ID> "<status>" --note "<catatan>"`. Bisa beberapa ID sekaligus dipisah koma.

## Aturan Bahasa (berlaku untuk semua output)
- Basis Bahasa Indonesia yang luwes. Baris dengan `negara_bahasa` berbahasa lain ditulis langsung dalam bahasa itu, bukan diterjemahkan dari versi Indonesia.
- Menulis seperti manusia (dicek `slop_check.py` dan reviewer):
  - Mulai dari satu situasi, angka, atau kejadian yang spesifik. Jangan membuka dengan pernyataan umum tentang zaman atau industri.
  - Satu paragraf membawa satu fakta atau contoh yang hanya berlaku untuk topik ini. Kalau paragrafnya bisa dipindah ke artikel produk lain tanpa diubah, hapus.
  - Variasikan panjang kalimat. Kalimat pendek boleh, asal tidak di akhir setiap paragraf.
  - Hindari pola "bukan X, melainkan Y", daftar tiga serangkai yang dipaksakan, tanya-jawab pendek ("Hasilnya? Boros."), tanda pisah panjang (—), dan penutup yang merangkum ulang.
  - Ganti kata sifat dengan bukti. "Hemat" kalah dari "Rp 162 juta dalam 3 tahun pada simulasi 100 karyawan".
- Istilah Inggris yang lazim dipakai profesional Indonesia JANGAN diterjemahkan: SaaS, software, on-premise, self-hosted, server, cloud, payroll, vendor lock-in, subscription, upgrade, update, dashboard, platform, malware, data breach, downtime, dan sejenisnya.
- Tanpa emoji berlebihan (maksimal 1 per konten, opsional), tanpa tanda seru beruntun, tanpa frasa klise ("di era digital", "tak dapat dipungkiri", "solusi terbaik", "revolusioner").

## Pitfalls
- Mengarang fitur, harga lisensi, nama klien, atau testimoni. Harga lisensi TIDAK ada di brief, jadi jangan menulis angka harga.
- Menulis "hemat 75%" sebagai janji pasti. Tulis sebagai hasil simulasi dengan asumsinya.
- Menyebut UU PDP secara keliru. Cukup sebut bahwa perusahaan perlu mengendalikan data pribadi karyawan sesuai UU PDP, tanpa pasal dan sanksi kecuali user memberi sumbernya.
- Menyimpan baris yang belum diperiksa pemeriksa.
- Meloloskan naskah yang kuat secara SEO tetapi `slop_check.py` menyatakan `lolos: false`. Gerbang slop tidak bisa ditawar dengan skor lain.
- Mengarang `skor_slop` atau `skor_ai`. Kedua angka itu hanya boleh berasal dari keluaran `slop_check.py`.
- Menjanjikan ranking, traffic, atau leads ke SML. Yang bisa dilaporkan hanya skor pemeriksaan.

## Verification
- Setiap baris di CSV punya `naskah` terisi, skor_checker ≥ 80, skor_seo ≥ 80, skor_slop ≤ 20, dan status "Menunggu review".
- Hasil pemeriksaan tiap putaran muncul di topik Content Reviewer.
- Laporan ke user mengikuti format langkah 5 persis, satu pesan.
- Script mengeluarkan "OK" dan file terkirim ke Telegram (atau pesan error yang dilaporkan ke user).
