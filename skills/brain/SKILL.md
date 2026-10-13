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

## Mencari dan menjawab

1. Cari dengan kata kunci inti pertanyaan, bukan kalimat panjang:
   ```
   python3 ${HERMES_SKILL_DIR}/scripts/brain.py search "<kata kunci>" --json --limit 6
   ```
   Hasil tipis? Coba sekali lagi dengan sinonim atau istilah Inggris/Indonesianya.
2. Butuh isi lengkap satu catatan: `brain.py show <doc_id>`.
3. Jawab HANYA dari hasil pencarian. Sebutkan judul catatan dan tanggalnya untuk tiap klaim, dan sumber aslinya kalau ada.
4. Tidak ada hasil yang relevan: katakan "tidak ada di brain". Kalau kamu lalu menjawab dari pengetahuan umum, pisahkan dengan jelas dan beri label bahwa itu bukan dari arsip.
5. Dua catatan saling bertentangan: tampilkan keduanya dengan tanggalnya, jangan memilih diam-diam.

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
