---
name: content-planning
description: Content planner PeopleSync. Menyusun content plan bertema masalah SaaS dan keuntungan software sekali beli, lewat alur pembuat lalu pemeriksa (koreksi + approval), lalu menyimpan hasilnya ke spreadsheet untuk direview SML.
version: 1.0.0
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

## Mode Tim (Kanban): dipakai kalau profile `content-planner` dan `content-reviewer` ada

Cek dulu dengan `hermes profile list`. Kalau kedua profile ada, alurnya dibagi per peran. Langkah 1-4 di bagian Procedure tetap jadi standar kerja, tapi dikerjakan oleh peran yang berbeda.

**Kalau kamu LEAD (profile default, sedang ngobrol dengan SML):**
1. Jangan menyusun konten sendiri. Buat kartu Kanban:
   `kanban_create(title="Content plan PeopleSync: <ringkas permintaan>", assignee="content-planner", body="<permintaan SML lengkap: periode, jumlah konten, platform, catatan khusus>. Pakai skill content-planning. Simpan draft ke ~/hermes-data/content-plan/drafts/<task_id>.json lalu request review ke content-reviewer.")`
2. Balas SML: kartu sudah dibuat, tim sedang bekerja, hasil akan dikirim ke topik ini sebagai file CSV.
3. Untuk review SML (approve / revisi / tolak), ikuti langkah 6. Revisi dikirim sebagai kartu baru ke content-planner dengan ID baris dan catatan SML di body.

**Kalau kamu CONTENT-PLANNER (worker Kanban):**
1. Kerjakan langkah 0-1 (pembuat). Tulis JSON draft ke `~/hermes-data/content-plan/drafts/<task_id>.json`.
2. Panggil `kanban_request_review` dengan reviewer `content-reviewer` dan summary berisi path file draft + jumlah konten.
3. Kalau kartu kembali dengan permintaan perubahan, perbaiki HANYA baris yang dikoreksi, timpa file draft, lalu request review lagi.

**Kalau kamu CONTENT-REVIEWER:**
1. Baca draft dari path di summary. Nilai setiap baris dengan `checker-rubric.md` dan `peoplesync-brief.md`. Kamu tidak tahu alasan pembuat, dan memang tidak perlu.
2. Ada baris "revisi" dan ini belum putaran ke-3: panggil `kanban_request_changes` dengan koreksi per ID dalam format JSON rubrik.
3. Semua baris lolos (atau sudah putaran ke-3): buang baris yang masih gagal, isi `skor_checker`, `catatan_checker`, `status` = "Menunggu review SML", lalu jalankan langkah 4 (save_plan.py add ... --send). Setelah itu `kanban_complete` dengan ringkasan langkah 5.

Kalau profile tim tidak ada, kerjakan seluruh Procedure sendiri seperti di bawah.

## Procedure

### 0. Pahami permintaan
Default kalau user tidak menyebut: 2 minggu, 3 konten per minggu, platform LinkedIn + Instagram, mulai Senin terdekat. Tanya HANYA kalau permintaannya bertentangan dengan brief.

### 1. PEMBUAT (Maker): susun draft
Baca brief produk dulu. Lalu susun konten sebagai JSON array dengan field berikut (semua wajib, string):

`id` (format CP-YYYYMMDD-NN), `tanggal_tayang` (YYYY-MM-DD), `platform`, `format` (Carousel, Reel, Single Post, Artikel LinkedIn, Thread), `pilar`, `funnel` (TOFU, MOFU, BOFU), `judul_hook`, `pesan_utama` (1-2 kalimat), `outline` (poin-poin dipisah " | "), `cta`, `keyword`, `sumber_klaim` (bagian brief yang dipakai, atau "-" kalau tidak ada klaim produk).

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
Tulis JSON ke file sementara, lalu jalankan:

```
python3 ${HERMES_SKILL_DIR}/scripts/save_plan.py add /tmp/content_plan_batch.json --send
```

Script menyimpan ke CSV (baris dengan ID sama akan ditimpa) dan mengirim file CSV ke topik Telegram review.

### 5. Laporan ke user
Balas singkat dalam bahasa Indonesia: jumlah konten yang lolos, yang dibuang beserta alasannya, sebaran pilar dan funnel, lalu daftar ID + judul_hook. Akhiri dengan cara review: "Balas dengan: approve CP-xxx, revisi CP-xxx <catatan>, atau tolak CP-xxx".

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
- Setiap baris di CSV punya skor_checker ≥ 80 dan status "Menunggu review SML".
- Script mengeluarkan "OK" dan file terkirim ke Telegram (atau pesan error yang dilaporkan ke user).
