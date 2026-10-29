#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURE_SOURCE="${1:?usage: test-roundtrip.sh FIXTURE_WEB_ROOT}"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/ring-symbols-roundtrip.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/web/retro/js"
cp "$FIXTURE_SOURCE/retro/dial.html" "$TMP/web/retro/dial.html"
cp "$FIXTURE_SOURCE/retro/dial9.html" "$TMP/web/retro/dial9.html"
cp "$FIXTURE_SOURCE/retro/js/dial.js" "$TMP/web/retro/js/dial.js"

mkdir -p "$TMP/original/retro/js"
cp "$TMP/web/retro/dial.html" "$TMP/original/retro/dial.html"
cp "$TMP/web/retro/dial9.html" "$TMP/original/retro/dial9.html"
cp "$TMP/web/retro/js/dial.js" "$TMP/original/retro/js/dial.js"

"$ROOT/apply-ring-symbols-upgrade.sh" "$TMP/web"
grep -q 'sg1-ring-segment' "$TMP/web/retro/dial.html"
grep -q 'centerGlyphInRing(newGlyph)' "$TMP/web/retro/js/dial.js"
"$ROOT/restore.sh" "$TMP/web"

cmp "$TMP/original/retro/dial.html" "$TMP/web/retro/dial.html"
cmp "$TMP/original/retro/dial9.html" "$TMP/web/retro/dial9.html"
cmp "$TMP/original/retro/js/dial.js" "$TMP/web/retro/js/dial.js"
test ! -e "$TMP/web/.stargate-ring-symbols-addon"

"$ROOT/apply-ring-symbols-upgrade.sh" "$TMP/web"
printf '\n// unrelated later change\n' >> "$TMP/web/retro/js/dial.js"
cp "$TMP/web/retro/dial.html" "$TMP/before-refusal-dial.html"
cp "$TMP/web/retro/dial9.html" "$TMP/before-refusal-dial9.html"
cp "$TMP/web/retro/js/dial.js" "$TMP/before-refusal-dial.js"
if "$ROOT/restore.sh" "$TMP/web"; then
  echo "ERROR: uninstall accepted an unrelated later change" >&2
  exit 1
fi
cmp "$TMP/before-refusal-dial.html" "$TMP/web/retro/dial.html"
cmp "$TMP/before-refusal-dial9.html" "$TMP/web/retro/dial9.html"
cmp "$TMP/before-refusal-dial.js" "$TMP/web/retro/js/dial.js"

# An installation made by the previous release has no state directory. The
# latest uninstaller must select a verified clean pre-install snapshot instead
# of trying to subtract code that may already belong to the base page.
mkdir -p "$TMP/legacy/web/retro/js" "$TMP/legacy/original/retro/js"
cp "$FIXTURE_SOURCE/retro/dial.html" "$TMP/legacy/web/retro/dial.html"
cp "$FIXTURE_SOURCE/retro/dial9.html" "$TMP/legacy/web/retro/dial9.html"
cp "$FIXTURE_SOURCE/retro/js/dial.js" "$TMP/legacy/web/retro/js/dial.js"
cp "$TMP/legacy/web/retro/dial.html" "$TMP/legacy/original/retro/dial.html"
cp "$TMP/legacy/web/retro/dial9.html" "$TMP/legacy/original/retro/dial9.html"
cp "$TMP/legacy/web/retro/js/dial.js" "$TMP/legacy/original/retro/js/dial.js"
"$ROOT/apply-ring-symbols-upgrade.sh" "$TMP/legacy/web"
rm -rf "$TMP/legacy/web/.stargate-ring-symbols-addon"
"$ROOT/restore.sh" "$TMP/legacy/web"
cmp "$TMP/legacy/original/retro/dial.html" "$TMP/legacy/web/retro/dial.html"
cmp "$TMP/legacy/original/retro/dial9.html" "$TMP/legacy/web/retro/dial9.html"
cmp "$TMP/legacy/original/retro/js/dial.js" "$TMP/legacy/web/retro/js/dial.js"

echo "Ring Symbols exact round-trip and refusal tests: PASS"
