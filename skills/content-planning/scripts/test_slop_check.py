#!/usr/bin/env python3
"""
Uji untuk pemeriksaan baru di slop_check.py: kalimat meta, kalimat kembar, frasa terlarang, dan format situs.

    python3 -m unittest test_slop_check.py     (jalankan dari folder scripts)

Contoh "sebelum" diambil dari naskah Hermes yang lolos reviewer dengan skor 92-94 tetapi harus disunting.
Contoh "wajar" memastikan pola baru tidak menolak tulisan yang benar.
"""
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import slop_check as sc  # noqa: E402

CFG = {}  # tanpa detektor eksternal


def periksa(naskah, faq="", platform="Website"):
    return sc.periksa("uji", naskah, CFG, faq, platform)


def ada(temuan, kata):
    return any(kata in t for t in temuan)


class KalimatMeta(unittest.TestCase):
    def test_pengumuman_isi_terdeteksi(self):
        for teks in [
            "Checklist artikel ini memuat 7 langkah untuk satu periode payroll, dengan asumsi cut-off sudah ada.",
            "Dalam artikel ini, kita akan melihat cara menghitung PPh 21 bulanan.",
            "Artikel ini membedah simulasi perbandingan TCO 3 tahun secara transparan.",
        ]:
            with self.subTest(teks=teks):
                self.assertTrue(ada(periksa(teks)["temuan"], "kalimat meta"))

    def test_keterangan_wajar_tidak_terdeteksi(self):
        for teks in [
            "Angka di artikel ini adalah ilustrasi dengan asumsi yang disebutkan di atas tabel.",
            "Tim payroll menjalankan empat langkah berikut setiap bulan sebelum tanggal gajian.",
        ]:
            with self.subTest(teks=teks):
                self.assertFalse(ada(periksa(teks)["temuan"], "kalimat meta"))

    def test_satu_kalimat_dihitung_sekali(self):
        teks = "Dalam artikel ini kita akan membahas cara menghitung payroll dengan benar."
        self.assertTrue(ada(periksa(teks)["temuan"], "kalimat meta yang mengumumkan isi ('artikel ini membahas'): 1x"))


class KalimatKembar(unittest.TestCase):
    KUNCI = ("Pada simulasi 100 karyawan dengan tarif Rp 45.000 per user per bulan, biaya langganan "
             "software payroll mencapai Rp 162.000.000 dalam 3 tahun.")

    def test_kalimat_kunci_disalin_ke_faq_terdeteksi(self):
        naskah = f"## Berapa biayanya?\n\n{self.KUNCI}\n\nTabel di bawah merinci per tahun."
        faq = f"T: Berapa biaya langganan 3 tahun? J: {self.KUNCI}"
        self.assertEqual(len(sc.kalimat_kembar(naskah, faq)), 1)
        self.assertTrue(ada(periksa(naskah, faq)["temuan"], "kalimat kembar"))

    def test_disalin_di_ringkasan_dan_isi_terdeteksi(self):
        naskah = f"**Ringkasan**: {self.KUNCI}\n\n## Tabel simulasi\n\nAsumsinya tertulis di bawah. {self.KUNCI}"
        self.assertEqual(len(sc.kalimat_kembar(naskah)), 1)

    def test_parafrase_tidak_terdeteksi(self):
        naskah = (f"{self.KUNCI}\n\n"
                  "Dengan tarif dan jumlah karyawan yang sama, tagihan setahun mencapai Rp 54.000.000.")
        self.assertEqual(sc.kalimat_kembar(naskah), [])

    def test_kalimat_pendek_tidak_dihitung(self):
        naskah = "Hubungi tim kami hari ini.\n\nHubungi tim kami hari ini."
        self.assertEqual(sc.kalimat_kembar(naskah), [])

    def test_field_faq_diabaikan_bila_naskah_memuat_faq_sendiri(self):
        # Format situs: FAQ ada di frontmatter, field faq hanya salinan dari isi yang sama.
        jawaban = "Lisensi PeopleSync dibayar sekali dan berlaku tanpa batas jumlah karyawan di server perusahaan."
        naskah = f'---\ntitle: "Contoh"\nfaq:\n  - q: "Apakah ada biaya per karyawan?"\n    a: "{jawaban}"\n---\n\nIsi artikel.'
        faq = f"T: Apakah ada biaya per karyawan? J: {jawaban}"
        self.assertEqual(sc.kalimat_kembar(naskah, faq), [])


class FrasaTerlarang(unittest.TestCase):
    def test_contoh_dari_naskah_hermes_terdeteksi(self):
        kasus = {
            "Aplikasi HRIS on premise server sendiri: kontrol data dan kepatuhan UU PDP tanpa pihak ketiga": "kepatuhan UU PDP",
            "Menempatkan data pada server privat menghilangkan keraguan hukum.": "klaim hukum",
            "100 persen database data pribadi tersimpan di server internal.": "100%",
            "On-premise kebal dari dampak celah keamanan akun penyewa lain.": "klaim mutlak",
            "Sistem ini mengeliminasi risiko kesalahan rumus manual.": "klaim mutlak",
            "Dalam pengujian deployment, instalasi selesai melalui 1 baris perintah.": "klaim karangan",
            "Perusahaan rata-rata membayar Rp 45.000 per karyawan.": "klaim karangan",
            "Lisensi perpetual dengan unlimited karyawan.": "istilah produk",
            "Absensi GPS dengan geofence dan export transfer bank BCA.": "fitur yang dicabut",
            "Instalasi di Linux, Windows Server, atau Docker.": "fitur yang dicabut",
            "Kategori A diperuntukkan bagi status PTKP TK/0.": "register birokratis",
            "Sumber: Blog Gadjian dan Mekari Talenta.": "nama kompetitor",
            "Integrasi lewat API pihak ketiga.": "kata API",
        }
        for teks, label in kasus.items():
            with self.subTest(teks=teks):
                self.assertTrue(ada(periksa(teks)["terlarang"], label), periksa(teks)["terlarang"])

    def test_kata_wajar_tidak_terdeteksi(self):
        for teks in [
            "PPh 21 bulanan memakai tarif efektif rata-rata sesuai kategori PTKP.",
            "Lisensi sekali bayar memberi kepastian angka di pembukuan tahunan.",
            "Data tersimpan rapi di server mandiri milik perusahaan.",
            "Lisensi seumur hidup berlaku tanpa batas jumlah karyawan.",
            "Tim IT menyiapkan backup terenkripsi dan menguji pemulihannya.",
        ]:
            with self.subTest(teks=teks):
                self.assertEqual(periksa(teks)["terlarang"], [])

    def test_tidak_memengaruhi_skor_slop(self):
        dasar = "Tim payroll menghitung potongan PPh 21 dan BPJS setiap bulan sebelum gajian."
        dengan = dasar + " Lisensi perpetual dengan unlimited karyawan."
        self.assertEqual(periksa(dasar)["skor_slop"], periksa(dengan)["skor_slop"])
        self.assertTrue(periksa(dengan)["lolos"])


class FormatSitus(unittest.TestCase):
    NASKAH_LAMA = ("# Software payroll sekali bayar\n\n**Ringkasan**: Isi ringkasan.\n\n"
                   "## Apa itu software payroll?\n\nJawaban.\n\n## FAQ\n\n**Apa itu?**\nJawaban.")

    def test_naskah_format_lama_terdeteksi(self):
        hasil = periksa(self.NASKAH_LAMA)["format_situs"]
        self.assertEqual(len(hasil), 3, hasil)

    def test_hanya_untuk_website(self):
        self.assertEqual(periksa(self.NASKAH_LAMA, platform="LinkedIn")["format_situs"], [])

    def test_frontmatter_tidak_terdeteksi(self):
        naskah = '---\ntitle: "Judul"\nsummary:\n  - "Ringkasan."\nfaq:\n  - q: "Tanya?"\n    a: "Jawab."\n---\n\nIsi.\n\n## Sumber\n\n1. Dokumen.'
        self.assertEqual(periksa(naskah)["format_situs"], [])


class PolaLama(unittest.TestCase):
    def test_em_dash_tetap_terdeteksi(self):
        self.assertTrue(ada(periksa("Biaya langganan naik setiap tahun — dan tim finance kaget.")["temuan"], "em dash"))


class ContohAcuan(unittest.TestCase):
    def test_contoh_acuan_di_article_standard_bersih(self):
        md = (HERE.parent / "references" / "article-standard.md").read_text(encoding="utf-8")
        blok = re.search(r"````markdown\n(.*?)````", md, re.S)
        self.assertIsNotNone(blok, "contoh acuan tidak ditemukan di article-standard.md")
        hasil = periksa(blok.group(1))
        self.assertTrue(hasil["lolos"], hasil)
        self.assertEqual(hasil["terlarang"], [])
        self.assertEqual(hasil["format_situs"], [])
        self.assertFalse(ada(hasil["temuan"], "kalimat meta"))
        self.assertFalse(ada(hasil["temuan"], "kalimat kembar"))


if __name__ == "__main__":
    unittest.main()
