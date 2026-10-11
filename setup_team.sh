#!/bin/bash
# Bikin tim Hermes untuk content planning PeopleSync:
#   lead (profile default)  -> bikin kartu Kanban
#   content-planner         -> pembuat draft
#   content-reviewer        -> pemeriksa + approval, simpan ke CSV
# Aman dijalankan ulang (update SOUL.md, model, dan skill).
#
# Pemakaian: bash setup_team.sh
set -e
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
HERMES_ROOT="${HERMES_HOME:-$HOME/.hermes}"
SKILL_SRC="$REPO_DIR/skills/content-planning"

# Semua profile lewat 9router (provider custom)
ROUTER_URL="http://127.0.0.1:20128/v1"
LEAD_MODEL="ag/gemini-3.8-flash"
PLANNER_MODEL="ag/gemini-3.8-flash-high"
REVIEWER_MODEL="cx/gpt-6-astra"

use_router() {  # $1 = profile ("" untuk default), $2 = model
  local p=(); [ -n "$1" ] && p=(-p "$1")
  hermes "${p[@]}" config set model.provider custom >/dev/null
  hermes "${p[@]}" config set model.base_url "$ROUTER_URL" >/dev/null
  hermes "${p[@]}" config set model.default "$2" >/dev/null
  echo "   ${1:-default} -> 9router / $2"
}

command -v hermes >/dev/null || { echo "hermes tidak ditemukan di PATH"; exit 1; }

echo "== 1/5 Skill content-planning di profile default"
mkdir -p "$HERMES_ROOT/skills/marketing"
rm -rf "$HERMES_ROOT/skills/marketing/content-planning"
cp -r "$SKILL_SRC" "$HERMES_ROOT/skills/marketing/"
mkdir -p ~/hermes-data/content-plan/drafts

echo "== 2/5 Profile tim"
setup_profile() {
  local name="$1" desc="$2" model="$3" soul="$4"
  if ! hermes profile list 2>/dev/null | grep -qw "$name"; then
    hermes profile create "$name" --clone --description "$desc"
  else
    echo "   $name sudah ada, diperbarui"
  fi
  local dir="$HERMES_ROOT/profiles/$name"
  [ -d "$dir" ] || { echo "   Folder $dir tidak ditemukan, cek 'hermes profile show $name'"; return 1; }

  cp "$soul" "$dir/SOUL.md"
  mkdir -p "$dir/skills/marketing"
  rm -rf "$dir/skills/marketing/content-planning"
  cp -r "$SKILL_SRC" "$dir/skills/marketing/"

  # Worker tidak butuh Telegram. Hapus token supaya tidak ada dua proses yang
  # polling bot yang sama (Telegram akan error 409 Conflict).
  [ -f "$dir/.env" ] && sed -i '/^TELEGRAM_/d' "$dir/.env"

  use_router "$name" "$model"
  hermes -p "$name" tools enable kanban >/dev/null 2>&1 || true
}
setup_profile content-planner "Pembuat content plan PeopleSync" "$PLANNER_MODEL" "$REPO_DIR/team/content-planner.SOUL.md"
setup_profile content-reviewer "Pemeriksa dan approval content plan PeopleSync" "$REVIEWER_MODEL" "$REPO_DIR/team/content-reviewer.SOUL.md"

echo "== 3/5 Lead (profile default)"
touch "$HERMES_ROOT/SOUL.md"
grep -q "Peran sebagai Lead tim" "$HERMES_ROOT/SOUL.md" || cat "$REPO_DIR/team/lead.SOUL.append.md" >> "$HERMES_ROOT/SOUL.md"
use_router "" "$LEAD_MODEL"
hermes tools enable kanban >/dev/null 2>&1 || true

echo "== 4/5 Kanban + satu gateway untuk semua profile"
hermes kanban init >/dev/null 2>&1 || true
hermes config set gateway.multiplex_profiles true >/dev/null
echo "Restart Hermes (maks 60 detik)..."; timeout 60 hermes gateway restart >/dev/null 2>&1 || systemctl --user restart hermes-gateway

echo "== 5/5 Cek"
sleep 5
hermes profile list
for p in content-planner content-reviewer; do
  echo "--- $p"; hermes profile show "$p" 2>/dev/null | grep -iE 'model|soul|skill' || true
done
echo
echo "Selesai. Tes di topik Content Planning:"
echo "  /content-planning buat content plan 1 minggu untuk PeopleSync"
echo "Pantau kartu: hermes kanban list  (atau buka Ruang)"
