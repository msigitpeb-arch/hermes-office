---
name: content-planning
description: Content planner PeopleSync. Menyusun content plan bertema masalah SaaS dan keuntungan software sekali beli, lewat alur pembuat lalu pemeriksa (koreksi + approval), lalu menyimpan hasilnya ke spreadsheet untuk direview SML.
version: 2.0.0
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

## Quick Reference
- Brief produk (SATU-SATUNYA sumber fakta): `${HERMES_SKILL_DIR}/references/peoplesync-brief.md`
- Rubrik pemeriksa: `${HERMES_SKILL_DIR}/references/checker-rubric.md`
- Simpan dan kirim ke Telegram: `python3 ${HERMES_SKILL_DIR}/scripts/save_plan.py`
- File spreadsheet: `~/hermes-data/content-plan/peoplesync_content_plan.csv`

## Mode Tim (Kanban): dipakai kalau profile `content-planner`, `content-writer`, dan `content-reviewer` ada

Langkah PERTAMA, sebelum menulis apa pun: jalankan `hermes profile list` lewat terminal. Kalau ketiga profile ada, kamu WAJIB memakai mode tim ini sesuai peranmu. Dilarang mengerjakan peran lain.

Alur: LEAD → PLANNER (rencana) → WRITER (naskah) ⇄ REVIEWER (koreksi + approval, berulang sampai approve) → CSV + laporan ke SML.

Semua file kerja di `~/hermes-data/content-plan/drafts/`. Ganti `<run>` dengan ID kartu planner (misalnya `t_201a25d8`) supaya semua peran memakai nama file yang sama.

**Kalau kamu LEAD (profile default, sedang ngobrol dengan SML):**
1. Buat kartu untuk planner. Pakai tool `kanban_create` kalau tersedia:
   `kanban_create(title="Content plan PeopleSync: <ringkas permintaan>", assignee="content-planner", body="<permintaan SML lengkap: periode, jumlah konten, platform, catatan khusus>. Pakai skill content-planning, peran CONTENT-PLANNER.")`
   Kalau tool tidak ada: `hermes kanban create "Content plan PeopleSync: <ringkas>" --assignee content-planner`, lalu `hermes kanban comment <id> "<isi body>"`.
2. Balas SML satu kali: kartu sudah dibuat, tim bekerja, hasil akan dikirim ke topik ini. Jangan memantau atau melapor progres.
3. Untuk review SML (approve / revisi / tolak), ikuti langkah 6. Revisi dikirim sebagai kartu baru ke `content-writer` dengan ID baris dan catatan SML di body, lalu tetap lewat reviewer.

**Kalau kamu CONTENT-PLANNER (strategi, worker Kanban):**
1. Kerjakan langkah 0-1 TANPA menulis naskah: isi semua field kecuali `naskah`. Fokus pada strategi: sebaran pilar dan funnel, angle tiap konten, hook, outline, CTA, dan `sumber_klaim`.
2. Simpan ke `drafts/<run>-plan.json` (ganti `<run>` dengan ID kartumu).
3. Buat kartu untuk writer: `kanban_create(title="Naskah content plan <run>", assignee="content-writer", body="Rencana di ~/hermes-data/content-plan/drafts/<run>-plan.json. Tulis naskah tiap baris. Pakai skill content-planning, peran CONTENT-WRITER. Run ID: <run>.")`
4. `kanban_complete` dengan ringkasan: jumlah konten, sebaran pilar dan funnel.

**Kalau kamu CONTENT-WRITER (penulis, worker Kanban):**
1. Baca `drafts/<run>-plan.json` dan brief produk. Untuk setiap baris, isi field `naskah`: teks final yang siap diposting sesuai platform dan format.
   - LinkedIn Single Post / Artikel: 120-250 kata, paragraf pendek, hook di baris pertama.
   - Instagram Carousel: tulis per slide, format `Slide 1: ... | Slide 2: ...` (5-8 slide), lalu `Caption: ...`.
   - Reel: `Hook (0-3 dtk): ... | Isi: ... | Penutup: ...` lalu `Caption: ...`.
   - Selalu akhiri dengan CTA dari baris itu. Klaim produk hanya dari brief.
2. Simpan semua baris (field rencana + `naskah`) ke `drafts/<run>-copy.json`.
3. `kanban_request_review` dengan reviewer `content-reviewer` dan summary: path file, jumlah konten, dan putaran revisi ke berapa.
4. Kalau kartu kembali dengan permintaan perubahan: perbaiki HANYA baris dan bagian yang dikoreksi, timpa file `-copy.json`, lalu `kanban_request_review` lagi. Jangan membantah koreksi; kalau koreksi bertentangan dengan brief, ikuti brief dan jelaskan singkat di summary.

**Kalau kamu CONTENT-REVIEWER (editor + approval):**
1. Baca `drafts/<run>-copy.json`. Nilai SETIAP baris (rencana DAN naskah) dengan `checker-rubric.md` dan `peoplesync-brief.md`.
2. Hitung putaran: lihat riwayat kartu (`kanban_show`), jumlah `request_changes` sebelumnya + 1.
3. Ada baris yang belum layak approve → `kanban_request_changes` berisi koreksi per ID dalam format JSON rubrik. Kartu kembali ke writer. Ulangi sampai semua baris approve.
4. **Batas aman: putaran ke-6.** Kalau di putaran ke-6 masih ada baris yang gagal, jangan kirim balik lagi. Simpan baris yang sudah approve (langkah 5), lalu `kanban_block` dengan alasan, dan kirim eskalasi ke SML:
   `python3 ${HERMES_SKILL_DIR}/scripts/save_plan.py notify "Eskalasi content plan <run>: <n> konten belum lolos setelah 6 putaran. ID: <...>. Masalah utama: <ringkas>. Balas dengan arahan, atau minta lead membuat ulang."`
5. Semua baris approve → isi `skor_checker`, `catatan_checker`, `revisi_ke` (jumlah putaran), `status` = "Menunggu review SML", `catatan_sml` = "". Simpan dengan langkah 4 (save_plan.py add ... --send).
6. Kirim laporan langkah 5 ke topik dengan menulisnya ke file lalu `save_plan.py notify @<file>`. Setelah itu `kanban_complete`.

Kalau profile tim tidak lengkap, kerjakan seluruh Procedure sendiri seperti di bawah, termasuk menulis `naskah`.

## Procedure

### 0. Pahami permintaan
Default kalau user tidak menyebut: 2 minggu, 3 konten per minggu, platform LinkedIn + Instagram, mulai Senin terdekat. Tanya HANYA kalau permintaannya bertentangan dengan brief.

### 1. PEMBUAT (Maker): susun draft
Baca brief produk dulu. Lalu susun konten sebagai JSON array dengan field berikut (semua wajib, string):

`id` (format CP-YYYYMMDD-NN), `tanggal_tayang` (YYYY-MM-DD), `platform`, `format` (Carousel, Reel, Single Post, Artikel LinkedIn, Thread), `pilar`, `funnel` (TOFU, MOFU, BOFU), `judul_hook`, `pesan_utama` (1-2 kalimat), `outline` (poin-poin dipisah " | "), `cta`, `keyword`, `sumber_klaim` (bagian brief yang dipakai, atau "-" kalau tidak ada klaim produk), `naskah` (teks final siap posting; di mode tim diisi oleh writer).

Aturan pembuat:
- Pakai lima pilar di brief dengan porsi seimbang. Funnel kira-kira 50% TOFU, 30% MOFU, 20% BOFU.
- Konten TOFU membahas masalah pembaca (HR, finance, owner), bukan jualan. Produk baru muncul di MOFU dan BOFU.
- Hook spesifik dan konkret. Hindari hook generik seperti "Tahukah kamu?".
- Setiap klaim produk HARUS ada di brief. Angka penghematan wajib ditulis sebagai simulasi, bukan janji.
- Jangan menyebut atau menjelekkan merek kompetitor.

### 2. PEMERIKSA (Checker): koreksi + approval
Pemeriksa harus independen dari pembuat. Gunakan `delegate_task` untuk subagent pemeriksa dengan konteks HANYA: isi `checker-rubric.md`, isi `peoplesync-brief.md`, dan JSON draft. Jangan ikut sertakan alasan pembuat.

Minta pemeriksa mengembalikan JSON array: `{"id", "skor" (0-100), "keputusan" ("approve" | "revisi"), "koreksi" (apa yang salah + saran perbaikan konkret)}`.

Kalau `delegate_task` tidak tersedia, lakukan pemeriksaan sebagai langkah terpisah: baca ulang rubrik, lalu nilai setiap baris seolah-olah melihat draft orang lain.

### 3. Revisi
- Baris "revisi": pembuat memperbaiki sesuai koreksi, lalu kirim ulang ke pemeriksa.
- Maksimal 2 putaran. Baris yang tetap gagal setelah 2 putaran dibuang dan disebut di laporan.

### 4. Simpan dan kirim untuk review SML
Tambahkan ke setiap baris yang lolos: `skor_checker`, `catatan_checker` (ringkas apa yang sudah dikoreksi), `status` = "Menunggu review SML", `catatan_sml` = "".
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
- `approve <ID>` → `python3 ${HERMES_SKILL_DIR}/scripts/save_plan.py status <ID> "Approved"`
- `tolak <ID> <alasan>` → status "Ditolak" dengan catatan alasan
- `revisi <ID> <catatan>` → perbaiki baris itu, ulangi langkah 2 untuk baris itu saja, lalu simpan dengan status "Menunggu review SML" dan catatan_sml berisi catatan user.
Untuk status dengan catatan: `save_plan.py status <ID> "<status>" --note "<catatan>"`. Bisa beberapa ID sekaligus dipisah koma.

## Aturan Bahasa (berlaku untuk semua output)
- Basis Bahasa Indonesia yang luwes.
- Istilah Inggris yang lazim dipakai profesional Indonesia JANGAN diterjemahkan: SaaS, software, on-premise, self-hosted, server, cloud, payroll, vendor lock-in, subscription, upgrade, update, dashboard, platform, malware, data breach, downtime, dan sejenisnya.
- Tanpa emoji berlebihan (maksimal 1 per konten, opsional), tanpa tanda seru beruntun, tanpa frasa klise ("di era digital", "tak dapat dipungkiri", "solusi terbaik", "revolusioner").

## Pitfalls
- Mengarang fitur, harga lisensi, nama klien, atau testimoni. Harga lisensi TIDAK ada di brief, jadi jangan menulis angka harga.
- Menulis "hemat 75%" sebagai janji pasti. Tulis sebagai hasil simulasi dengan asumsinya.
- Menyebut UU PDP secara keliru. Cukup sebut bahwa perusahaan perlu mengendalikan data pribadi karyawan sesuai UU PDP, tanpa pasal dan sanksi kecuali user memberi sumbernya.
- Menyimpan baris yang belum diperiksa pemeriksa.

## Verification
- Setiap baris di CSV punya `naskah` terisi, skor_checker ≥ 80, dan status "Menunggu review SML".
- Laporan ke user mengikuti format langkah 5 persis, satu pesan.
- Script mengeluarkan "OK" dan file terkirim ke Telegram (atau pesan error yang dilaporkan ke user).
