#!/bin/bash
# Naikkan batas waktu perintah hermes di Ruang (default 8 detik terlalu pendek untuk VPS 2 vCPU).
# Jalankan ulang setiap kali Ruang di-update lewat installer-nya.
set -e
SECONDS_LIMIT="${1:-25}"
F=~/.local/share/ruang/app/lib/node_modules/ruang/build/server/mission-control.js
[ -f "$F" ] || { echo "File Ruang tidak ditemukan: $F"; exit 1; }
sed -i -E "s/COMMAND_TIMEOUT_MS = [0-9_]+;/COMMAND_TIMEOUT_MS = ${SECONDS_LIMIT}_000;/" "$F"
grep -n "COMMAND_TIMEOUT_MS =" "$F"
systemctl --user restart ruang && echo "Ruang di-restart dengan batas ${SECONDS_LIMIT} detik"
