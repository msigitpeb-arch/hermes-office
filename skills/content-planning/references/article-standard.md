# Standar Artikel Website PeopleSync

Berlaku untuk format **Artikel Blog** dan **Berita Website** (platform Website). CONTENT-WRITER wajib membaca file ini sebelum menulis. CONTENT-REVIEWER memeriksa setiap artikel terhadap aturan bernomor di bawah, selain `checker-rubric.md`.

Asal aturan: empat artikel Hermes pertama (CP-20261019-01 sampai CP-20261022-01) lolos reviewer dengan skor 92 sampai 94 dan `skor_slop` 0, tetapi harus disunting berat sebelum bisa tayang di peoplesync.id. Setiap aturan di sini lahir dari perbaikan nyata pada empat naskah itu. Catatan lengkap sebelum dan sesudahnya ada di repo situs: `docs/content/artikel-hermes-perbaikan.md`.

Brief (`peoplesync-brief.md`) tetap satu-satunya sumber klaim produk. File ini mengatur cara menulis, sumber fakta umum, dan format.

## Kenapa naskah yang salah bisa lolos

Lima celah yang membuat reviewer memberi 92 sampai 94 pada naskah yang salah:

1. **Sumber cukup "tercantum", tidak harus dibuka.** Gerbang fakta di rubrik meloloskan fakta umum selama ada sumbernya. Writer menulis tarif TER dari ingatan dan mencantumkan beranda pajak.go.id; reviewer melihat ada sumber lalu meloloskannya. Tarif kategori B dan C ternyata salah.
2. **Brief dan simulasi sendiri dihitung sebagai sumber.** Bagian "Sumber" diisi "Brief Produk PeopleSync" dan "Simulasi Tarif SaaS", sehingga terlihat lengkap padahal tidak ada rujukan yang bisa diperiksa pembaca.
3. **Nama kompetitor lolos lewat daftar sumber.** Larangan menyebut kompetitor dibaca hanya untuk isi naskah. Blog Gadjian dan Mekari Talenta masuk lewat bagian Sumber dan `sumber_klaim`.
4. **Frasa UU PDP diizinkan aturan lama.** Brief dan SKILL.md membolehkan "sesuai UU PDP", sehingga "kepatuhan UU PDP" di judul, keyword, dan FAQ dianggap masih di dalam aturan.
5. **Kalimat diulang karena perintah planner.** Outline menyuruh writer memasang "tiga kalimat kunci GEO". Writer menaruh kalimat yang sama persis di Ringkasan, isi, dan FAQ, dan tidak ada gerbang yang menghitung pengulangan.

`slop_check.py` memberi skor 0 pada keempat naskah karena tidak menghitung kalimat kembar, kalimat moral, kalimat meta, atau register birokratis. Skor slop rendah bukan bukti tulisan sudah baik.

## Aturan bernomor

Setiap aturan bisa dicek. Pelanggaran aturan 1 sampai 12 = keputusan "revisi" dengan skor maksimal 59, apa pun skor lainnya.

### A. Fakta dan sumber

**1. Angka regulasi wajib dicek ke dokumen resmi yang dibuka, dan dirujuk sampai pasal atau lampiran.**
Tarif TER, iuran dan batas upah BPJS, PTKP, aturan THR dan lembur hanya boleh ditulis setelah writer membuka dokumen peraturannya (misalnya PDF di peraturan.bpk.go.id atau jdih.kemenkeu.go.id) atau halaman resmi lembaganya. Sumber ditulis dengan nama peraturan, pasal atau lampiran, dan URL dokumen, bukan beranda. Kalau dokumen tidak bisa dibuka, angkanya tidak ditulis.
- Sebelum: "Karyawan B (K/1, Kategori B), bruto Rp 12.000.000, tarif TER 4,00%." Sumber: `https://pajak.go.id`
- Sesudah: "B ... 3%" dengan sumber "PP 58 Tahun 2023, Pasal 2 dan Lampiran huruf B" dan URL dokumennya. (Lampiran B: di atas Rp 11.600.000 sampai Rp 12.600.000 = 3%.)

**2. Hitungan regulasi wajib mengikuti definisi resminya, bukan definisi sehari-hari.**
Untuk PPh 21 TER, penghasilan bruto pegawai tetap mencakup iuran JKK, JKM, dan BPJS Kesehatan yang dibayar perusahaan (PMK 168/2023 Pasal 5 ayat 1 dan Pasal 8). Simulasi yang memakai gaji sebagai bruto salah, dan bisa memindahkan karyawan ke tarif lain.
- Sebelum: bruto = "gaji pokok, tunjangan, dan lembur"; kategori C upah Rp 15.000.000, bruto Rp 15.000.000.
- Sesudah: bruto = upah + JKK 0,24% + JKM 0,30% + BPJS Kesehatan 4% (batas upah Rp 12.000.000) = Rp 15.561.000, tarif 6% karena lampiran C membatasi tarif 5% sampai Rp 15.550.000.

**3. Angka yang berubah tiap tahun ditulis dengan tanggal dan peringatan.**
Batas upah Jaminan Pensiun disesuaikan BPJS Ketenagakerjaan setiap tahun (PP 45/2015 Pasal 29). Tulis angka yang tercantum di halaman resmi saat dibuka, tanggal membukanya, dan peringatan untuk memeriksanya lagi. Jangan memakai angka tahun lalu dari blog.
- Sebelum: "Jaminan Pensiun 1 persen dari upah (dengan plafon batas upah maksimal Rp 10.042.300)."
- Sesudah: "Batas upah JP ditetapkan BPJS Ketenagakerjaan setiap tahun. Per 14 Oktober 2026, halaman resminya mencantumkan Rp 10.547.400 per bulan, tanpa menyebut tahun berlakunya."

**4. Yang tidak boleh dicantumkan sebagai sumber: brief, simulasi sendiri, beranda situs, blog vendor, dan situs kompetitor.**
Klaim produk memang berasal dari brief, tetapi brief adalah dokumen internal dan tidak dicantumkan. Simulasi buatan sendiri ditulis sebagai ilustrasi dengan asumsinya, bukan sebagai sumber. Kalau artikel tidak memakai fakta pihak ketiga sama sekali, bagian Sumber cukup berisi satu kalimat yang menyatakan bahwa angka di artikel adalah simulasi dengan asumsi tertulis.
- Sebelum: "1. Brief Produk PeopleSync 2. Simulasi Tarif SaaS Payroll Pasar Indonesia 3. Paper.id Blog ..."
- Sesudah: "Semua angka di atas adalah simulasi dengan asumsi yang disebutkan di atas tabel, bukan data pasar, dan tidak ada data pihak ketiga yang dikutip."

**5. Nama kompetitor dilarang di mana pun, termasuk Sumber, `sumber_klaim`, dan alt text.**
Daftar minimum (tambah bila ada): Gadjian, Mekari, Mekari Talenta, Talenta, Nusawork, LinovHR, Hadirr, Kerjoo, Paper.id. Kalau satu-satunya sumber sebuah fakta adalah situs kompetitor, cari sumber resmi atau buang faktanya.
- Sebelum: "Sumber: Blog Gadjian, 'Proses Payroll Karyawan dan Cara Menghitungnya'; Mekari Talenta, 'Contoh Cara Menghitung Gaji...'"
- Sesudah: "Sumber: PP 58 Tahun 2023 ... (Database Peraturan BPK)."

**6. Angka contoh selalu berlabel "ilustrasi" dan menyebut asumsinya di kalimat atau tabel yang sama.**
Angka pasar tanpa sumber tidak boleh ditulis sebagai fakta ("rata-rata", "umumnya membayar", "berdasarkan data pasar").
- Sebelum: "Perusahaan yang mempekerjakan 100 karyawan di Indonesia rata-rata membayar biaya per user bulanan berkisar Rp 45.000."
- Sesudah: "Tabel berikut memakai asumsi ilustrasi: 100 karyawan, tarif SaaS Rp 45.000 per user per bulan, tanpa kenaikan tarif."

**7. Tidak ada angka, ambang, pengujian, atau hasil yang dikarang.**
Yang termasuk: ambang "di atas 50 orang", persentase kenaikan tanpa label, "dalam pengujian deployment", "dari beberapa hari menjadi hitungan menit". Kalau ingin memakai angka hipotetis, beri label ilustrasi dan hitung dampaknya.
- Sebelum: "Kenaikan harga lisensi tahunan sebesar 10 persen dapat merusak proyeksi anggaran."
- Sesudah: "Kalau vendor menaikkan tarif 10 persen di setiap perpanjangan tahunan (ilustrasi), biaya tahun kedua menjadi Rp 59.400.000 dan tahun ketiga Rp 65.340.000."

### B. Klaim produk dan klaim berisiko

**8. Klaim produk hanya dari brief, dengan istilah yang sama seperti di brief atau situs.**
Fitur yang tidak ada di brief tidak ditulis, termasuk sebagai contoh atau rencana. Absensi GPS/geofence, export transfer bank, dan instalasi Docker sudah dicabut dari produk. Istilah: "tanpa batas jumlah karyawan" (bukan "unlimited karyawan"), "lisensi seumur hidup" (bukan "lisensi perpetual" atau "selamanya"), "aturan Depnaker".
- Sebelum: "PeopleSync ... dipasang ... Linux, Windows Server, maupun container Docker ... absensi GPS dengan geofence ... export transfer BCA, Mandiri, BRI, dan BNI."
- Sesudah: "PeopleSync dipasang di server milik perusahaan, di Linux atau Windows Server. Modul payroll menghitung PPh 21 TER kategori A, B, C, potongan BPJS ..."

**9. Tidak ada klaim mutlak, dan tidak ada generalisasi tentang semua vendor SaaS.**
Frasa terlarang ada di bagian "Daftar frasa terlarang". Perbandingan dengan SaaS ditulis sebagai perbedaan kendali dan kebijakan, bukan sebagai "SaaS tidak aman". On-premise memindahkan risiko ke perusahaan; tulis juga risiko itu.
- Sebelum: on-premise "Kebal dari dampak celah keamanan akun penyewa lain"; SaaS "Teknisi vendor cloud memiliki akses sistem backend".
- Sesudah: on-premise "Tidak terpengaruh celah pada akun penyewa lain"; SaaS "Vendor, sesuai kontrak dan kebijakannya", ditambah "Tabel ini tidak berarti SaaS selalu kurang aman."

**10. Tanpa bahasa kepatuhan UU PDP.**
Jangan menulis "kepatuhan", "patuh", atau "sesuai UU PDP" di judul, keyword, heading, FAQ, atau isi. Tulis bahwa PeopleSync membantu perusahaan memegang kendali atas data karyawannya. Boleh menyebut kewajiban pengendali data dalam UU 27/2022 kalau pasalnya dibuka dan dikutip isinya, tanpa menyimpulkan bahwa produk memenuhi kewajiban itu.
- Sebelum: judul "... kontrol data dan kepatuhan UU PDP tanpa pihak ketiga"; "Menempatkan data pada server privat menghilangkan keraguan hukum."
- Sesudah: judul "Aplikasi HRIS On Premise Server Sendiri: Kontrol Data"; "Server sendiri tidak otomatis memenuhi kewajiban itu. Yang berubah adalah siapa yang memegang kendali."

**11. Tidak ada harga lisensi, dan tidak ada rupiah penghematan.**
Biaya SaaS boleh dihitung persis dari asumsi ilustrasi. Biaya PeopleSync ditulis "lisensi di awal, harga melalui penawaran resmi". Jangan menulis selisih rupiah antara keduanya, karena itu membuka harga lisensi.

**12. Nomor telepon dan WhatsApp tidak ditulis di artikel.**
CTA memakai tautan internal ke form kontak (lihat bagian Format). Nomor kontak bisa berubah, dan form sudah membawa keperluan yang benar.

### C. SEO, GEO, AEO

Pelanggaran aturan 13 sampai 20 = `skor_seo` maksimal 79 (otomatis "revisi").

**13. Keyword utama muncul di `title`, 100 kata pertama, `description`, dan `slug`, dalam kalimat yang gramatikal.**
Keyword persis yang tidak gramatikal hanya boleh di `title` dan `slug`. Di isi, tulis dengan kapitalisasi dan kata sambung yang benar, lalu variasikan. Keyword persis paling banyak tiga kali di isi.
- Sebelum: "Banyak manajemen keuangan mulai mempertimbangkan model software payroll sekali bayar indonesia guna memangkas..." (4x di isi, termasuk H2)
- Sesudah: "Bagi perusahaan yang sedang menimbang software payroll sekali bayar di Indonesia, angka yang perlu dibandingkan adalah total pengeluaran tiga tahun."

**14. `summary` berisi 2 sampai 3 kalimat, total 40 sampai 60 kata, yang menjawab pertanyaan pencari.**
Kalimat di `summary` tidak boleh muncul persis di isi atau FAQ.

**15. Setiap H2 berupa pertanyaan atau frasa yang dicari, dan paragraf pertama di bawahnya menjawab langsung dalam 40 sampai 60 kata.**
Penjelasan, contoh, dan tabel datang setelah jawaban langsung.

**16. Minimal satu tabel dan satu daftar bernomor yang berisi informasi, bukan pengulangan teks.**
Tabel perbandingan atau hitungan; daftar bernomor untuk langkah atau checklist yang bisa dikerjakan.

**17. Minimal tiga kalimat kunci yang bisa dikutip utuh, dan ketiganya membawa informasi berbeda.**
Kalimat kunci menyebut subjek dengan nama (bukan "sistem ini"), memuat angka dengan satuan, periode, dan asumsi. Angka hitungan seperti "3 tahap" atau "7 langkah" tidak dihitung.
- Sebelum: "Audit satu siklus payroll membagi pekerjaan menjadi 3 tahap: pra-payroll, payroll processing, dan pasca-payroll."
- Sesudah: "Pada contoh audit ini, waktu tunggu 28 jam per siklus dua kali lebih panjang dari 14 jam kerja aktif, sehingga memperbaiki cut-off dan alur approval memberi dampak lebih besar daripada mempercepat perhitungan."

**18. Tidak ada kalimat yang diulang persis di `summary`, isi, dan `faq`.**
Kalimat kunci GEO ditulis sekali di isi. Ringkasan dan FAQ memakai kalimat sendiri. Kalimat kembar (6 kata atau lebih yang sama persis) di dua tempat = pelanggaran. `slop_check.py` menangkap otomatis kalimat kembar 8 kata atau lebih; yang 6 sampai 7 kata tetap diperiksa reviewer.

**19. `faq` berisi 3 sampai 5 tanya-jawab yang menjawab pertanyaan berbeda dari H2, dengan kalimat yang tidak disalin dari isi.**

**20. Panjang dan batas: `title` paling banyak 60 karakter; `description` 140 sampai 160 karakter dengan keyword di depan; isi 800 sampai 1.500 kata.**
Kalau "judul | PeopleSync" melebihi 60 karakter, isi `seoTitle` dengan versi pendek, misalnya dari `meta_title`.

### D. Gaya

Pelanggaran aturan 21 sampai 26 = keputusan "tulis_ulang" kalau muncul tiga kali atau lebih dalam satu naskah; di bawah itu "revisi".

**21. Tanpa kalimat meta yang mengumumkan isi.**
- Sebelum: "Checklist artikel ini memuat 7 langkah untuk satu periode payroll." / "Artikel ini membedah simulasi perbandingan TCO 3 tahun."
- Sesudah: kalimat dihapus; daftarnya langsung dimulai.

**22. Tanpa kalimat moral atau ringkasan kosong di akhir paragraf.**
- Sebelum: "Menghilangkan keempat ancaman ini memberikan ketenangan bagi jajaran direksi, tim personalia, serta serikat pekerja perusahaan."
- Sesudah: "Sebagai gantinya, risiko lain pindah ke perusahaan: server yang rusak, backup yang tidak pernah diuji, atau akun admin yang dipakai bersama."

**23. Register praktisi, bukan dokumen resmi.**
Hindari: "korporasi" (pakai "perusahaan"), "mengeliminasi" (pakai "mengurangi" atau "menghapus"), "diperuntukkan bagi" (pakai tabel atau "untuk"), "kepemilikan mutlak" (pakai "kendali penuh").
- Sebelum: "Kategori A diperuntukkan bagi status PTKP Tidak Kawin tanpa tanggungan (TK/0) ..."
- Sesudah: tabel "Kategori TER | Status PTKP" dengan baris "A | TK/0, TK/1, K/0".

**24. Tanpa pola "bukan X, melainkan/tetapi Y" dan tanpa tanya-jawab retoris.**
- Sebelum: "Sebagian besar waktu tersita pada tahap persiapan data, bukan pada mesin hitung."
- Sesudah: "Di banyak perusahaan, proses payroll sudah tersendat sebelum satu angka pun dihitung."

**25. Tanpa pengulangan fakta produk dalam paragraf berdekatan.**
- Sebelum: "PeopleSync menyimpan database di server pelanggan ..." muncul di dua paragraf berturut-turut.
- Sesudah: satu kali.

**26. Tanpa em dash (—) dan en dash (–).** Pakai koma, titik, titik dua, atau kata "sampai" untuk rentang.

## Daftar frasa terlarang

Reviewer mencari frasa berikut di seluruh naskah, termasuk FAQ, meta, dan Sumber. Satu temuan = "revisi" dengan perbaikan per baris. `slop_check.py` menampilkan temuannya di field `terlarang`; frasa yang terlalu umum untuk dicari mesin ("pasti", "akurat", "rata-rata", "komprehensif") tetap dicari reviewer sendiri.

| Frasa | Ganti dengan |
|---|---|
| kepatuhan UU PDP, patuh UU PDP, sesuai UU PDP | membantu perusahaan memegang kendali atas data karyawannya |
| menghilangkan keraguan hukum, menjamin kepatuhan | hapus |
| 100%, 100 persen (sebagai penekanan) | hapus, atau sebut faktanya tanpa angka |
| menjamin, pasti, dijamin | membantu, dapat |
| kebal, meniadakan, menghilangkan risiko, mengeliminasi risiko | mengurangi risiko |
| tanpa salah rumus, akurat (sebagai klaim) | sebut aturan yang dipakai sistem |
| dalam pengujian, berdasarkan data pasar, rata-rata (untuk angka pasar) | hapus, atau beri label ilustrasi |
| dari beberapa hari menjadi hitungan menit | hapus |
| unlimited karyawan | tanpa batas jumlah karyawan |
| lisensi perpetual, selamanya | lisensi seumur hidup |
| absensi GPS, geofence, export transfer bank, BCA/Mandiri/BRI/BNI (sebagai fitur), Docker | hapus, fitur sudah dicabut |
| korporasi, mengeliminasi, diperuntukkan bagi | perusahaan, mengurangi, untuk |
| artikel ini membahas, artikel ini memuat, dalam artikel ini | hapus |
| API | hapus (aturan situs) |
| komprehensif, revolusioner, solusi terbaik | sebut faktanya |

## Rujukan regulasi yang sudah dicek

Dicek ke dokumen resmi pada 14 Oktober 2026. Pakai sebagai titik awal, tetapi tetap buka dokumennya (aturan 1) dan cek ulang angka yang berubah tiap tahun (aturan 3).

| Topik | Isi | Dokumen |
|---|---|---|
| Kategori TER | A: TK/0, TK/1, K/0. B: TK/2, TK/3, K/1, K/2. C: K/3. Menurut status PTKP di awal tahun pajak | [PP 58/2023](https://peraturan.bpk.go.id/Details/274247/pp-no-58-tahun-2023-tarif-pemotongan-pajak-penghasilan-pasal-21-atas-penghasilan) Pasal 2 ayat (3) dan (4) |
| Tarif TER bulanan | Lampiran A, B, C. Contoh: A di atas Rp 7.500.000 sampai Rp 8.550.000 = 1,5%; B di atas Rp 11.600.000 sampai Rp 12.600.000 = 3%; C di atas Rp 14.150.000 sampai Rp 15.550.000 = 5%, di atas Rp 15.550.000 sampai Rp 17.050.000 = 6% | PP 58/2023 Lampiran |
| Berlaku | 1 Januari 2024 | PP 58/2023 Pasal 5 |
| Bruto pegawai tetap | Termasuk iuran JKK dan JKM serta BPJS Kesehatan yang dibayar pemberi kerja | [PMK 168/2023](https://peraturan.bpk.go.id/Details/286951/pmk-no-168-tahun-2023) Pasal 5 ayat (1) huruf a, Pasal 8 ayat (2) |
| Masa pajak terakhir | Pajak setahun dihitung ulang dengan tarif Pasal 17, dikurangi PPh 21 yang sudah dipotong | PMK 168/2023 Lampiran (contoh penghitungan) |
| BPJS Kesehatan | 5%: 4% perusahaan, 1% karyawan; batas upah Rp 12.000.000 | [Perpres 64/2020](https://peraturan.bpk.go.id/Download/127554/Perpres%20Nomor%2064%20Tahun%202020.pdf) Pasal 30 dan 32 |
| JHT | 5,7%: 3,7% perusahaan, 2% karyawan | [PP 46/2015](https://peraturan.bpk.go.id/Download/28934/PP%20Nomor%2046%20Tahun%202015.pdf) Pasal 16 |
| JP | 3%: 2% perusahaan, 1% karyawan; batas upah disesuaikan BPJS Ketenagakerjaan setiap tahun | [PP 45/2015](https://peraturan.bpk.go.id/Download/28931/PP%20Nomor%2045%20Tahun%202015.pdf) Pasal 28 dan 29; angka terkini di [halaman BPJS Ketenagakerjaan](https://www.bpjsketenagakerjaan.go.id/penerima-upah.html) |
| JKK, JKM | JKK 0,24% sampai 1,74% sesuai risiko; JKM 0,30%; keduanya dibayar perusahaan | [PP 44/2015](https://peraturan.bpk.go.id/Download/28927/PP%20Nomor%2044%20Tahun%202015.pdf) Pasal 16 dan 18 |
| Data pribadi | Pengendali wajib melindungi dan memastikan keamanan (Pasal 35), menjaga kerahasiaan (Pasal 36), dan mengawasi pihak yang terlibat dalam pemrosesan (Pasal 37) | [UU 27/2022](https://peraturan.bpk.go.id/Details/229798/uu-no-27-tahun-2022) |

## Format untuk situs peoplesync.id

Situs dibangun dengan Astro. Satu artikel adalah satu file Markdown: `src/content/artikel/id/<slug>.md`. Naskah Hermes harus bisa disalin ke file itu tanpa diubah.

Frontmatter:

```yaml
---
title: "Judul dengan keyword utama, paling banyak 60 karakter"
seoTitle: "Opsional. Isi bila 'judul | PeopleSync' melebihi 60 karakter"
description: "140 sampai 160 karakter, keyword di depan, manfaat dan ajakan"
hook: "Satu kalimat pendek untuk kartu Artikel terkait"
category: "Payroll | Biaya & TCO | Keamanan Data | Regulasi"
tags: ["Keyword utama", "Turunan 1", "Turunan 2", "Turunan 3"]
date: YYYY-MM-DD            # tanggal_tayang
cover: ../../../assets/articles/<slug>.jpg
coverAlt: "Deskripsi isi foto, bukan daftar keyword"
coverCredit:
  name: "Nama fotografer"
  url: "https://unsplash.com/photos/<id>"
summary:
  - "Kalimat Ringkasan 1."
  - "Kalimat Ringkasan 2."
faq:
  - q: "Pertanyaan?"
    a: "Jawaban satu sampai tiga kalimat."
draft: true
---
```

Aturan isi:

- Jangan menulis H1 (`# ...`) di isi. `title` sudah menjadi H1.
- Jangan menulis blok "Ringkasan" atau bagian "FAQ" di isi. Keduanya dirender dari `summary` dan `faq`, termasuk schema FAQPage.
- Subjudul memakai `##` (dan `###` bila perlu).
- Akhiri isi dengan bagian `## Sumber`, lalu satu kalimat CTA.
- Tautan internal yang boleh dipakai: `/kontak/?keperluan=demo`, `/kontak/?keperluan=konsultasi`, `/kontak/?keperluan=lisensi`, `/kalkulator-tco/`, `/harga/`. Jangan menautkan artikel lain yang masih draf, dan jangan menautkan `/add-on/` sampai halaman itu bersih dari klaim Docker.
- CTA sesuai funnel: TOFU dan MOFU ke konsultasi, BOFU ke demo atau penawaran lisensi.
- Foto sampul dari Unsplash dengan lisensi Unsplash (bukan Unsplash+), alt text menjelaskan isi foto, dan `coverCredit` diisi.
- `draft: true`. Pemilik yang mengubahnya ke `false`.

## Checklist sebelum menyerahkan naskah

Writer mencentang semua butir. Reviewer memeriksa ulang butir yang ditandai (R).

- [ ] (R) Setiap angka regulasi dicek ke dokumen resmi yang dibuka, dengan pasal atau lampiran dan URL dokumen di Sumber (aturan 1 sampai 3).
- [ ] (R) Bagian Sumber tidak berisi brief, simulasi sendiri, beranda situs, blog vendor, atau kompetitor (aturan 4 dan 5).
- [ ] Angka contoh berlabel ilustrasi dengan asumsi di kalimat atau tabel yang sama (aturan 6 dan 7).
- [ ] (R) Klaim produk ada di brief; tidak ada fitur yang sudah dicabut (aturan 8).
- [ ] (R) Tidak ada frasa dari "Daftar frasa terlarang".
- [ ] Tidak ada harga lisensi, rupiah penghematan, atau nomor telepon (aturan 11 dan 12).
- [ ] Keyword utama di title, 100 kata pertama, description, dan slug, dalam kalimat gramatikal; paling banyak tiga kali persis di isi (aturan 13).
- [ ] `summary` 40 sampai 60 kata (aturan 14).
- [ ] Setiap H2 dijawab langsung dalam 40 sampai 60 kata (aturan 15).
- [ ] Ada tabel dan daftar bernomor (aturan 16).
- [ ] (R) Tiga kalimat kunci dengan angka, satuan, periode, dan asumsi, masing-masing membawa informasi berbeda (aturan 17).
- [ ] (R) Tidak ada kalimat kembar di summary, isi, dan FAQ (aturan 18).
- [ ] FAQ 3 sampai 5 tanya-jawab dengan kalimat sendiri (aturan 19).
- [ ] Batas karakter title, description, dan panjang isi terpenuhi (aturan 20).
- [ ] Tidak ada kalimat meta, kalimat moral penutup, register birokratis, pola kontras, atau em dash (aturan 21 sampai 26).
- [ ] `slop_check.py` lolos. Skor rendah tidak menggantikan butir di atas.
- [ ] Frontmatter sesuai format situs, tanpa H1, Ringkasan, atau FAQ di isi.

## Contoh acuan

Artikel final berikut (CP-20261020-01, versi yang masuk ke repo situs) memenuhi semua aturan di atas. Pakai sebagai contoh bentuk, bukan sebagai template kalimat: jangan menyalin kalimatnya ke artikel lain.

````markdown
---
title: "Software Payroll Sekali Bayar Indonesia: TCO 3 Tahun"
description: "Simulasi biaya software payroll sekali bayar Indonesia vs SaaS langganan untuk 100 karyawan selama 3 tahun. Bandingkan TCO dan jadwalkan konsultasi teknis."
hook: "Simulasi biaya sewa SaaS untuk 100 karyawan selama 3 tahun."
category: "Biaya & TCO"
tags: ["Software payroll sekali bayar", "Software payroll tanpa langganan", "Aplikasi payroll beli putus", "Biaya software payroll", "TCO software payroll"]
date: 2026-10-20
cover: ../../../assets/articles/software-payroll-sekali-bayar-indonesia.jpg
coverAlt: "Staf keuangan menghitung biaya software payroll dengan kalkulator di meja kerja"
coverCredit:
  name: "Towfiqu barbhuiya"
  url: "https://unsplash.com/photos/JhevWHCbVyw"
summary:
  - "Untuk perusahaan dengan 100 karyawan, biaya software payroll berlangganan terus bertambah setiap bulan dan ikut naik saat tim bertambah."
  - "Software payroll sekali bayar mengganti tagihan berulang itu dengan satu lisensi di awal."
  - "Bandingkan keduanya dengan Total Cost of Ownership tiga tahun, termasuk biaya yang tidak tertulis di penawaran."
faq:
  - q: "Apa itu software payroll sekali bayar?"
    a: "Software payroll yang dibeli dengan satu kali pembayaran lisensi di awal, tanpa biaya langganan bulanan atau biaya per user."
  - q: "Kenapa perbandingan biaya software payroll dihitung untuk 3 tahun?"
    a: "Karena biaya langganan menumpuk dari bulan ke bulan. Dalam satu tahun selisihnya belum terasa, sedangkan dalam tiga tahun tagihan langganan sudah beberapa kali lipat dari tagihan tahun pertama."
  - q: "Apakah lisensi PeopleSync mengenakan biaya tambahan per karyawan?"
    a: "Tidak. Lisensi PeopleSync dibayar sekali, berlaku tanpa batas jumlah karyawan, dan tidak naik tarifnya setiap tahun. Layanan tambahan seperti instalasi atau kustomisasi dijual terpisah bila dibutuhkan."
  - q: "Berapa harga lisensi PeopleSync?"
    a: "Harga lisensi diberikan lewat penawaran resmi sesuai kebutuhan perusahaan, dan pembelian dilindungi Garansi Kepuasan 30 Hari."
draft: false
---

Setiap awal bulan, tagihan software payroll masuk ke meja finance, dan angkanya naik setiap kali ada karyawan baru. Bagi perusahaan yang sedang menimbang software payroll sekali bayar di Indonesia, angka yang perlu dibandingkan adalah total pengeluaran tiga tahun. Tagihan satu bulan tidak memperlihatkan selisihnya. Contoh di bawah memakai perusahaan dengan 100 karyawan.

## Apa itu software payroll sekali bayar?

Software payroll sekali bayar adalah sistem penggajian yang dibeli dengan satu kali pembayaran lisensi, tanpa biaya langganan bulanan atau biaya per user. Model harga ini berbeda dari istilah on-premise: sekali bayar menjelaskan cara membayar, sedangkan on-premise menjelaskan di mana software dan databasenya dipasang.

Dengan model langganan, perusahaan membayar hak pakai selama kontrak berjalan. Begitu langganan berhenti, akses ke sistem ikut berhenti. Dengan lisensi sekali bayar, biaya software dibayar di awal dan tidak bertambah saat perusahaan merekrut orang baru.

## Mengapa perbandingan biaya relevan untuk perusahaan 100 karyawan?

Pada skala 100 karyawan, tarif per user yang terlihat kecil berubah menjadi angka puluhan juta per tahun. Tagihan itu dicatat sebagai beban operasional yang berulang, tidak pernah menjadi aset, dan bertambah setiap kali tim tumbuh atau vendor menyesuaikan harga saat perpanjangan.

Perusahaan di ukuran ini biasanya masih merekrut. Tiap karyawan baru langsung menambah tagihan bulan berikutnya, sementara anggaran software sudah dikunci di awal tahun. Risiko kedua adalah kenaikan tarif saat kontrak diperpanjang, yang sepenuhnya ditentukan vendor.

## Tabel simulasi biaya software payroll 3 tahun: sewa vs beli putus

Tabel berikut memakai asumsi ilustrasi: 100 karyawan, tarif SaaS Rp 45.000 per user per bulan, tanpa kenaikan tarif dan tanpa penambahan karyawan selama tiga tahun.

| Komponen biaya | SaaS langganan (ilustrasi) | Lisensi sekali bayar (PeopleSync) |
|---|---|---|
| Tarif per user per bulan | Rp 45.000 | Tidak ada biaya per user |
| Tahun pertama | Rp 54.000.000 (100 x Rp 45.000 x 12 bulan) | Lisensi di awal, harga melalui penawaran resmi |
| Tahun kedua | Rp 54.000.000 | Tidak ada biaya lisensi berulang |
| Tahun ketiga | Rp 54.000.000 | Tidak ada biaya lisensi berulang |
| Total 3 tahun | Rp 162.000.000 | Biaya lisensi awal, tetap |
| Saat karyawan bertambah | Tambah Rp 45.000 per orang per bulan | Tanpa biaya tambahan per karyawan |
| Bila berhenti membayar | Akses berhenti | Lisensi seumur hidup tetap berlaku |

Pada simulasi 100 karyawan dengan tarif SaaS Rp 45.000 per user per bulan, biaya langganan software payroll mencapai Rp 54.000.000 per tahun dan Rp 162.000.000 dalam 3 tahun. Angka itu belum memasukkan kenaikan tarif.

Kalau vendor menaikkan tarif 10 persen di setiap perpanjangan tahunan (ilustrasi), biaya tahun kedua menjadi Rp 59.400.000 dan tahun ketiga Rp 65.340.000, sehingga total tiga tahun menjadi Rp 178.740.000. Untuk jumlah karyawan, tarif, dan periode yang lain, coba hitung skenario Anda di [Kalkulator TCO PeopleSync](/kalkulator-tco/).

## Komponen biaya tersembunyi apa yang perlu dihitung?

Selain tarif dasar, ada lima pos yang sering tidak tertulis di penawaran: biaya tambahan per user saat tim bertambah, modul yang dijual terpisah, biaya migrasi dan pelatihan, kenaikan tarif saat perpanjangan, dan biaya server serta pemeliharaan untuk sistem yang dipasang sendiri.

Masukkan kelimanya ke perhitungan sebelum memilih:

1. Biaya user tambahan untuk karyawan yang direkrut di tengah tahun.
2. Modul yang dijual sebagai paket lebih mahal, misalnya pajak, absensi, atau approval lembur.
3. Implementasi awal, pelatihan admin payroll, dan migrasi data master karyawan dari sistem lama.
4. Kenaikan tarif ketika kontrak diperpanjang.
5. Server, backup, dan waktu tim IT untuk merawat sistem bila software dipasang di infrastruktur sendiri.

Pos kelima berlaku untuk sistem on-premise seperti PeopleSync, jadi masukkan juga ke kolom lisensi sekali bayar saat membandingkan.

## Kapan perusahaan sebaiknya beralih ke lisensi beli putus?

Lisensi beli putus paling masuk akal ketika jumlah karyawan terus bertambah, anggaran software perlu pasti dari tahun ke tahun, dan perusahaan sudah punya tim IT atau mitra yang bisa merawat server. Kalau tiga kondisi itu belum ada, hitung dulu biaya server dan perawatannya sebelum memutuskan.

Perusahaan yang rutin membuka cabang merasakan selisihnya paling cepat, karena setiap cabang baru menambah karyawan sekaligus tagihan langganan. Bagi finance, lisensi sekali bayar juga memudahkan proyeksi: biaya software tidak lagi bergantung pada jumlah karyawan bulan depan.

## Apa yang ditawarkan lisensi sekali beli PeopleSync?

PeopleSync adalah sistem HR & payroll on-premise untuk perusahaan di Indonesia dengan lisensi sekali beli. Lisensinya berlaku tanpa batas jumlah karyawan dan perangkat, tanpa biaya per karyawan, dan tanpa kenaikan tarif tahunan. Semua modul aktif sejak instalasi, dan layanan tambahan dijual terpisah bila dibutuhkan.

PeopleSync dipasang di server milik perusahaan, di Linux atau Windows Server. Modul payroll menghitung PPh 21 TER kategori A, B, C, potongan BPJS Kesehatan dan Ketenagakerjaan, THR, dan lembur sesuai aturan Depnaker, lalu mengirim slip gaji terenkripsi via email.

Harga lisensi tidak dicantumkan di situs. Angkanya diberikan melalui [penawaran resmi](/kontak/?keperluan=lisensi), dan pembelian dilindungi Garansi Kepuasan 30 Hari.

## Sumber

Semua angka di atas adalah simulasi dengan asumsi yang disebutkan di atas tabel, bukan data pasar, dan tidak ada data pihak ketiga yang dikutip.

[Jadwalkan konsultasi teknis](/kontak/?keperluan=konsultasi) untuk memetakan kebutuhan dan menghitung simulasi TCO payroll tiga tahun perusahaan Anda.
````
