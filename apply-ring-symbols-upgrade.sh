#!/usr/bin/env bash
set -euo pipefail

TARGET_ROOT="${1:-/home/pi/sg1_v4/web}"
PACKAGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$TARGET_ROOT" == "--target" ]]; then
  TARGET_ROOT="${2:-/home/pi/sg1_v4/web}"
fi

python3 "$PACKAGE_DIR/install_overlay.py" "$TARGET_ROOT"

echo "OK: Ring Symbols surgical overlay applied."
