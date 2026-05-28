#!/usr/bin/env bash
set -euo pipefail

TARGET_ROOT="${1:-/home/pi/sg1_v4/web}"
if [[ "$TARGET_ROOT" == "--target" ]]; then
  TARGET_ROOT="${2:-/home/pi/sg1_v4/web}"
fi
if [[ "$TARGET_ROOT" == */sg1_v4 ]]; then
  TARGET_ROOT="$TARGET_ROOT/web"
fi

fail() { echo "ERROR: $1" >&2; exit 1; }

[ -d "$TARGET_ROOT" ] || fail "Target web folder not found: $TARGET_ROOT"

if ! sudo -n true 2>/dev/null; then
  echo "This restore needs sudo because stargate files may be owned by root."
  sudo true
fi

echo "Restoring Stargate Ring Symbols upgrade backups in:"
echo "  $TARGET_ROOT"

sudo systemctl stop stargate.service || true

for rel in \
  "retro/dial.html" \
  "retro/dial9.html" \
  "retro/js/dial.js"
do
  backup="$TARGET_ROOT/$rel.bak-ring-symbols-upgrade"
  [ -f "$backup" ] || fail "Backup file not found: $backup"
  sudo rm -f "$TARGET_ROOT/$rel"
  sudo cp -a "$backup" "$TARGET_ROOT/$rel"
  echo "Restored: $rel"
done

sudo chown -R pi:pi "$TARGET_ROOT/retro"
sudo systemctl start stargate.service

echo "=== STARGATE RING SYMBOLS RESTORE COMPLETE ==="
