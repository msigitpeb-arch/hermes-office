#!/usr/bin/env python3
"""
Cek "AI slop" pada naskah content plan. Heuristik lokal, hanya standard library.

    slop_check.py drafts/<run>-copy.json     nilai semua baris yang punya naskah
    slop_check.py --text "..."               nilai satu teks

Keluaran: JSON array {"id", "skor_slop", "skor_ai", "lolos", "temuan"}.
    skor_slop  0-100, makin kecil makin baik. Lolos kalau <= 20.
    skor_ai    persen "buatan AI" dari detektor eksternal, atau "n/a" kalau tidak aktif.
               Lolos kalau < 50.

Detektor eksternal (opsional) diatur di ~/hermes-data/content-plan/config.env:
    AI_DETECTOR=sapling | gptzero
    AI_DETECTOR_KEY=...
"""
import argparse
import json
import re
import statistics
import sys
import urllib.request
from collections import Counter
from pathlib import Path

from save_plan import CONFIG_PATH, read_env

BATAS_SLOP = 20
BATAS_AI = 50

# Frasa yang hampir selalu menandakan tulisan mesin atau tulisan malas (bobot 8)
FRASA = [
    "di era digital", "di era modern", "di era serba", "di tengah pesatnya", "di tengah persaingan",
    "dalam dunia yang", "dunia yang terus berubah", "seiring berjalannya waktu", "seiring perkembangan",
    "seiring dengan perkembangan", "tak dapat dipungkiri", "tidak dapat dipungkiri", "tidak bisa dipungkiri",
    "penting untuk diingat", "perlu diingat bahwa", "perlu dicatat bahwa", "patut dicatat",
    "pada akhirnya", "kesimpulannya", "secara keseluruhan", "dengan demikian", "oleh karena itu",
    "lebih lanjut,", "selain itu,", "di sisi lain,", "tidak heran jika", "bukan rahasia lagi",
    "memainkan peran penting", "memegang peranan penting", "peran krusial", "menjadi kunci",
    "kunci kesuksesan", "solusi terbaik", "solusi yang tepat", "solusi tepat", "jawaban yang tepat",
    "revolusioner", "terdepan", "game changer", "game-changer", "transformasi digital",
    "membuka potensi", "memaksimalkan potensi", "membawa ke level", "ke level berikutnya",
    "tahukah kamu", "tahukah anda", "pernahkah kamu", "pernahkah anda", "bayangkan jika", "bayangkan kalau",
    "mari kita", "yuk, simak", "simak selengkapnya", "jangan sampai ketinggalan", "saatnya beralih",
    "tunggu apa lagi", "jadi, tunggu", "lanskap bisnis", "lanskap digital",
    "in today's", "fast-paced", "ever-evolving", "ever-changing", "it's important to note",
    "it is important to note", "it's worth noting", "in conclusion", "in summary", "at the end of the day",
    "look no further", "whether you're", "when it comes to", "plays a crucial role", "plays a vital role",
    "a testament to", "unlock the", "unleash", "take it to the next level", "navigate the complexities",
    "delve", "tapestry", "in the realm of", "game changer", "say goodbye to",
]

# Kata yang wajar sesekali tapi menumpuk di tulisan mesin (bobot 3)
KATA = [
    "krusial", "signifikan", "komprehensif", "holistik", "optimal", "mengoptimalkan", "memberdayakan",
    "mulus", "inovatif", "terintegrasi", "efisien dan efektif",
    "leverage", "seamless", "seamlessly", "robust", "elevate", "empower", "streamline", "harness",
    "pivotal", "crucial", "moreover", "furthermore", "landscape", "foster", "comprehensive", "holistic",
]

LABEL = re.compile(r"(?i)\b(slide\s*\d+|caption|hook(\s*\([^)]*\))?|isi|penutup|cta)\s*:")
KONTRAS = re.compile(
    r"\b(?:bukan(?:\s+(?:hanya|sekadar|sekedar|cuma))?|tidak\s+(?:hanya|sekadar|sekedar|cuma))\b"
    r"[^.?!\n]{2,80}?\b(?:melainkan|tetapi|tapi)\b"
    r"|\bnot\s+(?:just|only|merely)\b[^.?!\n]{2,80}?\bbut\b"
    r"|\bit'?s\s+not\b[^.?!\n]{2,60}[,;]\s*it'?s\b"
)
TIGA = re.compile(r"[\w-]+(?: [\w-]+){0,2}, [\w-]+(?: [\w-]+){0,2},? (?:dan|serta|atau|and|or) [\w-]+")
TANYA_JAWAB = re.compile(r"(?:^|[.!?]\s+)(?:[\w-]+\s){0,3}[\w-]+\?\s+(?:[\w-]+\s){0,2}[\w-]+\.")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿]")


def hitung(frasa, teks):
    return len(re.findall(r"(?<!\w)" + re.escape(frasa) + r"(?!\w)", teks))


def nilai_slop(naskah):
    """Kembalikan (skor 0-100, daftar temuan)."""
    # Heading markdown dan label format bukan bagian dari prosa yang dinilai
    baris = [b for b in naskah.replace("|", "\n").splitlines() if not b.lstrip().startswith("#")]
    teks = LABEL.sub(" ", "\n".join(baris))
    teks = re.sub(r"(?m)^\s*(?:[-*•]|\d+[.)])\s+", "", teks)
    low = teks.lower()
    kata = re.findall(r"[\w'-]+", low)
    kalimat = [k.strip() for k in re.split(r"(?<=[.!?])\s+|\n+", teks) if len(k.split()) >= 3]
    skor, temuan = 0, []

    def tambah(poin, pesan):
        nonlocal skor
        skor += poin
        temuan.append(pesan)

    kena = [(f, hitung(f, low)) for f in FRASA]
    kena = [(f, n) for f, n in kena if n]
    if kena:
        tambah(min(40, 8 * sum(n for _, n in kena)), "frasa klise: " + ", ".join(f"'{f}'" for f, _ in kena))

    ringan = [(k, hitung(k, low)) for k in KATA]
    ringan = [(k, n) for k, n in ringan if n]
    if ringan:
        tambah(min(15, 3 * sum(n for _, n in ringan)), "kata khas mesin: " + ", ".join(k for k, _ in ringan))

    n = len(KONTRAS.findall(low))
    if n:
        tambah(min(24, 6 * n), f"pola 'bukan X, melainkan Y': {n}x")

    n = teks.count("—") + len(re.findall(r"\s–\s", teks))
    if n:
        tambah(min(20, 5 * n), f"tanda pisah panjang (em dash): {n}x")

    lebih = len(TIGA.findall(low)) - (1 + len(kata) // 120)
    if lebih > 0:
        tambah(min(12, 4 * lebih), f"daftar tiga serangkai berlebihan: {lebih}x di atas wajar")

    n = len(TANYA_JAWAB.findall(teks))
    if n:
        tambah(min(15, 5 * n), f"tanya-jawab pendek ala 'Hasilnya? Boros.': {n}x")

    if len(kalimat) >= 8:
        panjang = [len(k.split()) for k in kalimat]
        if statistics.pstdev(panjang) / statistics.mean(panjang) < 0.30:
            tambah(12, "panjang kalimat terlalu seragam, ritme datar")
        awal, jumlah = Counter(k.split()[0].lower().strip(",") for k in kalimat).most_common(1)[0]
        if jumlah / len(kalimat) > 0.30:
            tambah(8, f"terlalu banyak kalimat dibuka dengan '{awal}'")

    n = len(EMOJI.findall(teks))
    if n > 1:
        tambah(min(12, 3 * (n - 1)), f"emoji: {n}")
    if "!!" in teks or teks.count("!") > 2:
        tambah(5, "tanda seru berlebihan")

    return min(100, skor), temuan


def post_json(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def nilai_detektor(naskah, cfg):
    """Kembalikan (persen AI atau None, pesan error atau None)."""
    penyedia, key = cfg.get("AI_DETECTOR", "").lower(), cfg.get("AI_DETECTOR_KEY")
    if not penyedia or not key:
        return None, None
    try:
        if penyedia == "sapling":
            data = post_json("https://api.sapling.ai/api/v1/aidetect", {"key": key, "text": naskah}, {})
            return round(float(data["score"]) * 100), None
        if penyedia == "gptzero":
            data = post_json("https://api.gptzero.me/v2/predict/text", {"document": naskah}, {"x-api-key": key})
            return round(float(data["documents"][0]["completion_generated_prob"]) * 100), None
        return None, f"AI_DETECTOR tidak dikenal: {penyedia}"
    except Exception as e:
        return None, f"detektor {penyedia} gagal: {e}"


def periksa(id_, naskah, cfg):
    skor, temuan = nilai_slop(naskah)
    ai, err = nilai_detektor(naskah, cfg)
    if err:
        temuan.append(err)
    if ai is not None and ai >= BATAS_AI:
        temuan.append(f"detektor eksternal menilai {ai}% buatan AI")
    return {
        "id": id_,
        "skor_slop": skor,
        "skor_ai": "n/a" if ai is None else ai,
        "lolos": skor <= BATAS_SLOP and (ai is None or ai < BATAS_AI),
        "temuan": temuan,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("json_file", nargs="?")
    p.add_argument("--text")
    args = p.parse_args()
    cfg = read_env(CONFIG_PATH)

    if args.text:
        hasil = [periksa("-", args.text, cfg)]
    elif args.json_file:
        batch = json.loads(Path(args.json_file).expanduser().read_text(encoding="utf-8"))
        if isinstance(batch, dict):
            batch = batch.get("items") or batch.get("rows") or [batch]
        hasil = [periksa(r.get("id", "-"), str(r["naskah"]), cfg) for r in batch if r.get("naskah")]
    else:
        p.error("isi path file JSON atau --text")
    print(json.dumps(hasil, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
