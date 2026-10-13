---
name: brain
description: Second brain SML. Menyimpan catatan, tautan, hasil riset, dan fakta ke arsip Markdown, lalu mencarinya kembali. Pakai saat SML bilang simpan, catat, ingat, arsipkan, atau bertanya "apa yang gw tau soal X", "cari di brain", "dulu gw pernah nyimpen apa soal X".
version: 1.0.0
author: SML
metadata:
  hermes:
    tags: [memory, knowledge, rag, notes]
---

# Brain: second brain SML

Arsip pengetahuan jangka panjang. Catatan disimpan sebagai file Markdown di `~/hermes-data/brain/knowledge/` (bisa dibuka di Obsidian) dan dicari lewat indeks teks. Semua operasi lewat satu script:

```
python3 ${HERMES_SKILL_DIR}/scripts/brain.py <perintah>
```

## When to Use
- SML minta menyimpan sesuatu: "simpan ini", "catat", "ingat ini", meneruskan pesan, tautan, atau hasil riset.
- SML bertanya tentang sesuatu yang mungkin pernah disimpan.
- Kamu butuh fakta untuk pekerjaan lain (misalnya menulis konten) dan arsip ini mungkin memuatnya.

## Menyimpan

1. Tentukan apakah ini layak disimpan jangka panjang. Obrolan sambil lalu, kode tes, dan pesan sementara tidak disimpan.
2. Pilih kategori:
   - `produk`: fakta PeopleSync yang sudah dikonfirmasi SML atau berasal dari peoplesync.id.
   - `riset`: temuan dari web, selalu dengan sumber.
   - `artikel`: isi tautan atau tulisan orang lain.
   - `ide`: ide konten, produk, atau eksperimen.
   - `notes`: catatan lain.
3. Untuk tautan: buka halamannya dengan tool web, ambil isi utamanya (bukan menu dan iklan), lalu simpan isi itu beserta URL-nya di `--source`. Kalau halaman tidak bisa dibuka, katakan begitu; jangan menyimpan tebakan isi.
4. Tulis isi ke file dulu, lalu simpan. Jangan menaruh teks panjang langsung di baris perintah:
   ```
   python3 ${HERMES_SKILL_DIR}/scripts/brain.py add --title "<judul spesifik>" --tags "<a, b>" --category <kategori> --source "<URL kalau ada>" @<file>
   ```
5. Laporkan ke SML memakai keluaran script (`OK tersimpan #<id>: <path>`). Kalau script mengeluarkan ERROR, sampaikan errornya. Jangan pernah bilang "sudah disimpan" tanpa baris OK itu.

Aturan isi:
- Judul spesifik, bukan "Catatan" atau "Info penting".
- Simpan apa adanya dari sumbernya. Ringkasanmu boleh ditambahkan di bagian atas dengan label "Ringkasan:", tetapi jangan mengganti isi asli dengan tafsiranmu.
- Jangan menyimpan API key, token, password, atau data pribadi sensitif. Script menolak pola yang jelas; kamu tetap wajib membuangnya sebelum menyimpan. Jangan memakai `--force` kecuali SML sendiri yang memintanya.
- Kategori `produk` hanya untuk fakta yang SML nyatakan benar atau yang tertulis di peoplesync.id. Dugaanmu tentang produk masuk `ide`, bukan `produk`.

## Menyimpan file (SOP, kebijakan, kontrak, laporan)

SML mengirim file (.pdf, .docx, .md, .txt, .csv) atau menyebut path file di server:

```
python3 ${HERMES_SKILL_DIR}/scripts/brain.py add-file "<path file>" --title "<judul>" --tags "<a, b>" --category dokumen
```

- Pakai path lokal file yang diberikan gateway untuk lampiran Telegram. Kalau kamu tidak punya path-nya, katakan begitu; jangan mengetik ulang isi file dari ingatan.
- Script menyimpan file aslinya, mengambil teksnya, dan mengindeks per bagian (heading untuk Word dan Markdown, halaman untuk PDF).
- Laporkan keluaran script apa adanya, termasuk jumlah kata. Jumlah kata yang sangat kecil untuk dokumen panjang berarti teksnya tidak terbaca.
- PDF hasil pindai tidak punya teks dan akan ditolak script. Sampaikan ke SML bahwa file itu perlu versi teks atau OCR.
- Jenis lain (.xlsx, .pptx, gambar) belum didukung. Jangan mengaku sudah menyimpannya.

## Mencari dan menjawab

SML sering tidak tahu dokumen mana yang memuat jawabannya ("coba cari soal ketenagakerjaan atau lembur"). Tugasmu menemukan semua tempat yang mungkin cocok, menunjukkan letaknya, lalu bertanya mana yang dimaksud.

1. Pencarian ini mencocokkan kata, bukan makna, jadi KAMU yang memperluas katanya. Dari permintaan SML, susun 6-10 kata yang berkaitan (sinonim, istilah resmi, bentuk Inggris, kata turunan) dan cari sekaligus dalam satu perintah:
   ```
   python3 ${HERMES_SKILL_DIR}/scripts/brain.py search "lembur overtime upah lembur jam kerja ketenagakerjaan waktu kerja" --json --limit 10
   ```
   Hasil masih tipis? Ulangi sekali dengan kata lain. Dua kali kosong berarti memang tidak ada.
2. Kelompokkan hasil per topik temuan, dan sebutkan letaknya dari field `judul` dan `bagian`. Format jawaban:
   ```
   Ketemu 4 bagian yang mungkin cocok:
   a. Aturan persetujuan dan tarif lembur — SOP Kepegawaian 2026, bagian "Lembur"
   b. Jam kerja normal — SOP Kepegawaian 2026, bagian "Jam Kerja"
   c. Lembur di slip gaji — SOP Payroll, bagian "Komponen Lembur di Slip Gaji"
   d. BPJS Ketenagakerjaan — SOP Payroll, bagian "BPJS"
   Mau lihat yang mana?
   ```
   Satu baris per temuan, tanpa menyalin isi panjang. Urutkan dari yang paling mungkin dimaksud.
3. Setelah SML memilih, tampilkan isi bagian itu dari `kutipan`. Butuh dokumen lengkap: `brain.py show <doc_id>`. SML minta file aslinya: kirim file di `file_asli`.
4. Jawab HANYA dari hasil pencarian. Sebutkan judul dokumen dan bagiannya untuk tiap klaim, dan sumber aslinya kalau ada.
5. Tidak ada hasil yang relevan: katakan "tidak ada di brain". Kalau kamu lalu menjawab dari pengetahuan umum, pisahkan dengan jelas dan beri label bahwa itu bukan dari arsip.
6. Dua catatan saling bertentangan: tampilkan keduanya dengan tanggalnya, jangan memilih diam-diam.

## Perintah lain
- `brain.py list [--category x]`: catatan terbaru.
- `brain.py status`: jumlah catatan per kategori.
- `brain.py ingest <folder>`: mengindeks folder Markdown yang sudah ada (misalnya salinan vault Obsidian) tanpa menyalinnya. Jalankan lagi setelah folder itu berubah.
- `brain.py forget <doc_id>`: hanya atas permintaan eksplisit SML, setelah kamu menyebut judul catatannya dan SML mengonfirmasi.

## Pitfalls
- Mengaku menyimpan padahal script gagal.
- Menjawab dari ingatan percakapan lalu menyebutnya "dari brain".
- Menyimpan ringkasan buatanmu sebagai fakta `produk`.
- Menghapus atau menimpa catatan tanpa konfirmasi.
