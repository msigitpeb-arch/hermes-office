import requests
import time

def ambil_daftar_grup():
    print("=" * 50)
    print("   PENCARI GROUP ID WHATSAPP VIA FONNTE")
    print("=" * 50)
    token = input("Masukkan FONNTE_TOKEN Anda: ").strip()

    if not token:
        print("[Error] Token tidak boleh kosong!")
        return

    headers = {"Authorization": token}

    print("\n1. Sinkronisasi data grup dari WhatsApp device...")
    try:
        res_fetch = requests.post("https://api.fonnte.com/fetch-group", headers=headers, timeout=20)
        print("Status sinkronisasi:", res_fetch.json().get("reason", "OK"))
    except Exception as e:
        print("Catatan sinkronisasi:", e)

    print("\nMenunggu 3 detik agar Fonnte selesai memuat daftar grup...")
    time.sleep(3)

    print("\n2. Mengambil daftar grup...")
    try:
        res_list = requests.post("https://api.fonnte.com/get-whatsapp-group", headers=headers, timeout=20)
        data = res_list.json()

        daftar_grup = data.get("data", [])
        if not daftar_grup:
            print("[INFO] Tidak ada grup yang ditemukan atau belum tersinkronisasi.")
            print("Respons API:", data)
            return

        print(f"\nDitemukan {len(daftar_grup)} grup WhatsApp:\n")
        print("-" * 60)
        for i, g in enumerate(daftar_grup, start=1):
            nama = g.get("name", "Tanpa Nama")
            gid = g.get("id", "-")
            print(f"{i}. Nama Grup : {nama}")
            print(f"   Group ID  : {gid}")
            print("-" * 60)

        print("\nSilakan COPY 'Group ID' di atas (yang ada @g.us)")
        print("Lalu masukkan ke secret WA_TARGET_NUMBER di GitHub.")

    except Exception as e:
        print("[Error] Gagal mengambil daftar grup:", e)

if __name__ == "__main__":
    ambil_daftar_grup()
