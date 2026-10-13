#!/bin/bash
# Pasang skill brain (second brain) ke profile default dan profile tim.
# Pemakaian: bash install_brain.sh
# Aman dijalankan ulang. Me-restart gateway, jadi jangan dijalankan saat ada kartu Kanban yang sedang berjalan.
set -e
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
HERMES_ROOT="${HERMES_HOME:-$HOME/.hermes}"
# Perintah lain yang membuka skill yang sama
ALIASES="simpan cari ingat"

pasang() {  # $1 = folder skills tujuan
  mkdir -p "$1/productivity"
  rm -rf "$1/productivity/brain"
  cp -r "$REPO_DIR/skills/brain" "$1/productivity/"
}

pasang "$HERMES_ROOT/skills"
for a in $ALIASES; do
  mkdir -p "$HERMES_ROOT/skills/productivity/$a"
  cat > "$HERMES_ROOT/skills/productivity/$a/SKILL.md" << ALIAS
---
name: $a
description: Alias dari skill brain (second brain SML). Dipakai saat user mengetik /$a.
version: 1.0.0
author: SML
---

# Alias: $a

Ini hanya alias. Muat skill \`brain\` dan ikuti seluruh isinya. Teks setelah perintah adalah permintaan user.
ALIAS
done
echo "[1/3] Skill brain terpasang di $HERMES_ROOT/skills/productivity/brain"
echo "      Alias perintah: /brain $(for a in $ALIASES; do printf '/%s ' "$a"; done)"

for dir in "$HERMES_ROOT"/profiles/*/; do
  [ -d "$dir" ] || continue
  pasang "${dir}skills"
  echo "      + profile $(basename "$dir")"
done
echo "[2/3] Profile tim ikut mendapat skill brain (untuk mencari fakta saat menulis dan memeriksa)"

mkdir -p ~/hermes-data/brain/knowledge
python3 "$HERMES_ROOT/skills/productivity/brain/scripts/brain.py" status
echo "[3/3] Data di ~/hermes-data/brain (catatan: knowledge/, indeks: brain.db)"

echo "Restart Hermes (maks 60 detik)..."; timeout 60 hermes gateway restart >/dev/null 2>&1 || systemctl --user restart hermes-gateway
echo
echo "Selesai. Coba di Telegram:"
echo "  /simpan PeopleSync punya garansi kepuasan 30 hari (kategori produk)"
echo "  /cari garansi"
