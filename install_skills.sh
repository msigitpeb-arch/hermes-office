#!/bin/bash
# Pasang skill Hermes dari repo ini ke ~/.hermes/skills
# Pemakaian: bash install_skills.sh <THREAD_ID_TOPIK_CONTENT_PLANNING>
set -e
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
THREAD_ID="$1"
GROUP_ID="-1004495571239"

if [ -z "$THREAD_ID" ]; then
  echo "Isi thread ID topik Content Planning."
  echo "Cara cari: di Telegram, buka topik Content Planning, klik kanan pesan apa saja > Copy Message Link."
  echo "Link-nya berbentuk https://t.me/c/4495571239/<THREAD_ID>/<MSG_ID>. Ambil angka di tengah."
  exit 1
fi
case "$THREAD_ID" in
  ''|*[!0-9]*) echo "Thread ID harus angka, contoh: bash install_skills.sh 7"; exit 1 ;;
esac

# 1. Salin skill
mkdir -p ~/.hermes/skills/marketing
rm -rf ~/.hermes/skills/marketing/content-planning
cp -r "$REPO_DIR/skills/content-planning" ~/.hermes/skills/marketing/
echo "[1/3] Skill content-planning terpasang di ~/.hermes/skills/marketing/content-planning"

# 2. Konfigurasi tujuan review (topik Telegram)
mkdir -p ~/hermes-data/content-plan
cat > ~/hermes-data/content-plan/config.env << CFG
REVIEW_CHAT_ID=$GROUP_ID
REVIEW_THREAD_ID=$THREAD_ID
CFG
chmod 600 ~/hermes-data/content-plan/config.env
echo "[2/3] File review dikirim ke grup $GROUP_ID topik $THREAD_ID"

# 3. Izinkan Hermes menjawab di grup
if grep -q '^TELEGRAM_GROUP_ALLOWED_CHATS=' ~/.hermes/.env 2>/dev/null; then
  grep -q -- "$GROUP_ID" ~/.hermes/.env || sed -i "s|^TELEGRAM_GROUP_ALLOWED_CHATS=\"\{0,1\}\([^\"]*\)\"\{0,1\}|TELEGRAM_GROUP_ALLOWED_CHATS=\"\1,$GROUP_ID\"|" ~/.hermes/.env
else
  echo "TELEGRAM_GROUP_ALLOWED_CHATS=\"$GROUP_ID\"" >> ~/.hermes/.env
fi
echo "[3/3] Grup diizinkan: $(grep '^TELEGRAM_GROUP_ALLOWED_CHATS=' ~/.hermes/.env)"

hermes gateway restart >/dev/null 2>&1 || systemctl --user restart hermes-gateway
echo
python3 ~/.hermes/skills/marketing/content-planning/scripts/save_plan.py ping
echo "Pastikan pesan tes muncul di topik Content Planning. Kalau muncul di topik lain, jalankan ulang dengan thread ID yang benar."
echo
echo "Selesai. Di topik Content Planning, kirim:"
echo "  /content-planning buat content plan 2 minggu untuk PeopleSync"
