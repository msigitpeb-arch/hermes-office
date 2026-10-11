#!/bin/bash
# Pasang skill Hermes dari repo ini ke ~/.hermes/skills
# Pemakaian: bash install_skills.sh <THREAD_ID_TOPIK_CONTENT_PLANNING> [THREAD_ID_TOPIK_CONTENT_REVIEWER]
# Thread kedua opsional: hasil pemeriksaan reviewer tiap putaran dikirim ke sana.
set -e
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
THREAD_ID="$1"
REVIEWER_THREAD_ID="$2"
GROUP_ID="-1004495571239"
CONFIG=~/hermes-data/content-plan/config.env
# Perintah lain yang membuka skill yang sama (salah ketik dan versi pendek)
ALIASES="konten cp content-plan content-planing contentplanning"

if [ -z "$THREAD_ID" ]; then
  echo "Isi thread ID topik Content Planning."
  echo "Cara cari: di Telegram, buka topik Content Planning, klik kanan pesan apa saja > Copy Message Link."
  echo "Link-nya berbentuk https://t.me/c/4495571239/<THREAD_ID>/<MSG_ID>. Ambil angka di tengah."
  exit 1
fi
case "$THREAD_ID" in
  ''|*[!0-9]*) echo "Thread ID harus angka, contoh: bash install_skills.sh 7"; exit 1 ;;
esac
case "$REVIEWER_THREAD_ID" in
  *[!0-9]*) echo "Thread ID topik reviewer harus angka, contoh: bash install_skills.sh 21 35"; exit 1 ;;
esac

# 1. Salin skill + alias perintah
mkdir -p ~/.hermes/skills/marketing
rm -rf ~/.hermes/skills/marketing/content-planning
cp -r "$REPO_DIR/skills/content-planning" ~/.hermes/skills/marketing/
for a in $ALIASES; do
  mkdir -p ~/.hermes/skills/marketing/"$a"
  cat > ~/.hermes/skills/marketing/"$a"/SKILL.md << ALIAS
---
name: $a
description: Alias dari skill content-planning (content plan PeopleSync). Dipakai saat user mengetik /$a.
version: 1.0.0
author: SML
---

# Alias: $a

Ini hanya alias. Muat skill \`content-planning\` dan ikuti seluruh isinya. Teks setelah perintah adalah permintaan user.
ALIAS
done
echo "[1/3] Skill content-planning terpasang di ~/.hermes/skills/marketing/content-planning"
echo "      Alias perintah: $(for a in $ALIASES; do printf '/%s ' "$a"; done)"

# 2. Konfigurasi tujuan review (topik Telegram)
mkdir -p ~/hermes-data/content-plan
# Yang tidak diatur script ini (topik reviewer lama, key detektor AI) dipertahankan
LAMA="$(grep -vE '^(REVIEW_CHAT_ID|REVIEW_THREAD_ID)=' "$CONFIG" 2>/dev/null || true)"
if [ -n "$REVIEWER_THREAD_ID" ]; then
  LAMA="$(printf '%s\n' "$LAMA" | grep -v '^REVIEWER_THREAD_ID=' || true)"
fi
{
  echo "REVIEW_CHAT_ID=$GROUP_ID"
  echo "REVIEW_THREAD_ID=$THREAD_ID"
  if [ -n "$REVIEWER_THREAD_ID" ]; then echo "REVIEWER_THREAD_ID=$REVIEWER_THREAD_ID"; fi
  if [ -n "$LAMA" ]; then printf '%s\n' "$LAMA"; fi
} > "$CONFIG"
chmod 600 "$CONFIG"
echo "[2/3] File review dikirim ke grup $GROUP_ID topik $THREAD_ID"
if grep -q '^REVIEWER_THREAD_ID=' "$CONFIG"; then
  echo "      Hasil pemeriksaan reviewer dikirim ke topik $(grep '^REVIEWER_THREAD_ID=' "$CONFIG" | cut -d= -f2)"
else
  echo "      Topik reviewer belum diatur, hasil pemeriksaan ikut ke topik $THREAD_ID."
  echo "      Atur dengan: bash install_skills.sh $THREAD_ID <THREAD_ID_TOPIK_CONTENT_REVIEWER>"
fi

# 3. Izinkan Hermes menjawab di grup
if grep -q '^TELEGRAM_GROUP_ALLOWED_CHATS=' ~/.hermes/.env 2>/dev/null; then
  grep -q -- "$GROUP_ID" ~/.hermes/.env || sed -i "s|^TELEGRAM_GROUP_ALLOWED_CHATS=\"\{0,1\}\([^\"]*\)\"\{0,1\}|TELEGRAM_GROUP_ALLOWED_CHATS=\"\1,$GROUP_ID\"|" ~/.hermes/.env
else
  echo "TELEGRAM_GROUP_ALLOWED_CHATS=\"$GROUP_ID\"" >> ~/.hermes/.env
fi
echo "[3/3] Grup diizinkan: $(grep '^TELEGRAM_GROUP_ALLOWED_CHATS=' ~/.hermes/.env)"

echo "Restart Hermes (maks 60 detik)..."; timeout 60 hermes gateway restart >/dev/null 2>&1 || systemctl --user restart hermes-gateway
echo
python3 ~/.hermes/skills/marketing/content-planning/scripts/save_plan.py ping
echo "Pastikan pesan tes muncul di topik Content Planning (dan topik Content Reviewer kalau diatur). Kalau muncul di topik lain, jalankan ulang dengan thread ID yang benar."
echo
echo "Selesai. Di topik Content Planning, kirim salah satu:"
echo "  /konten buat content plan 2 minggu untuk PeopleSync"
echo "  /content-planning buat content plan 2 minggu untuk PeopleSync"
echo "  buat content plan 2 minggu untuk PeopleSync        (tanpa garis miring juga bisa)"
