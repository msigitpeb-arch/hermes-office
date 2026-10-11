#!/bin/bash
# Pindahkan scraper yang sudah jalan dari ~/wa-news-scraper ke ~/hermes-office/news-scraper.
# Membawa .env dan riwayat berita (data/), membuat venv baru, dan mengganti path di crontab.
set -e
OLD="$HOME/wa-news-scraper"
NEW="$(cd "$(dirname "$0")" && pwd)"

[ -f "$OLD/.env" ] || { echo "Tidak ada $OLD/.env. Buat .env baru dari .env.example."; exit 1; }

cp "$OLD/.env" "$NEW/.env" && chmod 600 "$NEW/.env"
mkdir -p "$NEW/data" "$NEW/logs"
[ -d "$OLD/data" ] && cp -a "$OLD/data/." "$NEW/data/"
[ -f "$OLD/logs/cron.log" ] && cp "$OLD/logs/cron.log" "$NEW/logs/cron.log"
echo "[1/3] .env, riwayat berita, dan log disalin"

cd "$NEW"
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
echo "[2/3] venv siap"

CUR=$(crontab -l 2>/dev/null || true)
printf '%s\n' "$CUR" | sed "s|$OLD|$NEW|g; s|\$HOME/wa-news-scraper|\$HOME/hermes-office/news-scraper|g" | grep -v '^$' | crontab -
echo "[3/3] Crontab diperbarui:"
crontab -l | grep -E 'daily_scraper|9router'
echo
echo "Tes: cd $NEW && .venv/bin/python daily_scraper.py --dry-run --no-llm"
echo "Kalau sudah aman, folder lama bisa dihapus: rm -rf $OLD"
