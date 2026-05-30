#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import re
import shutil
import sys


def fail(message):
    raise SystemExit(f"ERROR: {message}")


def load(name):
    return (assets / name).read_text(encoding="utf-8")


def write_if_changed(path, text):
    original = path.read_text(encoding="utf-8", errors="replace")
    if text == original:
        print(f"Already current: {path}")
        return
    path.write_text(text, encoding="utf-8")
    print(f"Updated: {path}")


def replace_ring_svg(text, svg):
    pattern = re.compile(
        r'(<div class="gate ring-3">\s*<!-- prettier-ignore -->\s*)<svg[\s\S]*?</svg>',
        re.I,
    )
    if not pattern.search(text):
        fail("cannot find Retro ring-3 SVG")
    return pattern.sub(lambda match: match.group(1) + svg.rstrip(), text, count=1)


def install_html(path):
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    if "SG-1 ring-3 real 39 segment ring + glyphs" not in text:
        marker = '    <link rel="preconnect" href="https://fonts.googleapis.com" />'
        if marker not in text:
            fail(f"cannot find style insertion point in {path}")
        text = text.replace(marker, style + "\n" + marker, 1)
    if 'class="sg1-ring-segment"' not in text:
        text = replace_ring_svg(text, ring_svg)
    if "loadGateRingSymbols()" not in text:
        marker = '    <script type="module" src="js/startup.js"></script>'
        if marker not in text:
            fail(f"cannot find script insertion point in {path}")
        text = text.replace(marker, loader + marker, 1)
    text = re.sub(
        r'js/dial\.js(?:\?v=[^"\']*)?',
        f"js/dial.js?v=ring-symbols-overlay-{stamp}",
        text,
    )
    write_if_changed(path, text)


def install_js(path):
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    if "const RING_STEPS_PER_REVOLUTION = 1250;" not in text:
        marker = "let lastGateRotation = 0;\n"
        if marker not in text:
            fail(f"cannot find ring helper insertion point in {path}")
        text = text.replace(marker, marker + helpers, 1)
    pattern = re.compile(
        r"// That's a neat trick\nfunction trySpinning\(\) \{[\s\S]*?(?=async function dhd_press)",
    )
    if not pattern.search(text):
        fail(f"cannot find Retro ring animation block in {path}")
    text = pattern.sub(spinning, text, count=1)
    write_if_changed(path, text)


def remove_html(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text = text.replace(style + "\n", "")
    text = text.replace(style, "")
    text = text.replace(loader, "")
    if 'class="sg1-ring-segment"' in text:
        text = replace_ring_svg(text, base_ring_svg)
    write_if_changed(path, text)


def remove_js(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text = text.replace(helpers, "")
    pattern = re.compile(
        r"// That's a neat trick\nfunction trySpinning\(\) \{[\s\S]*?(?=async function dhd_press)",
    )
    if pattern.search(text):
        text = pattern.sub(base_spinning, text, count=1)
    write_if_changed(path, text)


target = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/pi/sg1_v4/web")
remove = "--remove" in sys.argv[2:]
if (target / "web/retro").is_dir():
    target = target / "web"
if not (target / "retro").is_dir():
    fail(f"target web folder not found: {target}")

assets = Path(__file__).resolve().parent / "assets"
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
style = load("ring-symbols-style.html")
ring_svg = load("ring-symbols-svg.html")
loader = load("ring-symbols-loader.html")
helpers = load("ring-position-helpers.js")
spinning = load("ring-position-spinning.js")
base_ring_svg = load("base-ring-svg.html")
base_spinning = load("base-ring-position-spinning.js")

files = [
    target / "retro/dial.html",
    target / "retro/dial9.html",
    target / "retro/js/dial.js",
]
for path in files:
    if not path.is_file():
        fail(f"missing file: {path}")

backup_base = target / "backups" / f"ring-symbols-overlay-{stamp}"
backup = backup_base
suffix = 1
while backup.exists():
    backup = Path(f"{backup_base}-{suffix}")
    suffix += 1
for path in files:
    destination = backup / path.relative_to(target)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
print(f"Backup saved: {backup}")

for path in files[:2]:
    (remove_html if remove else install_html)(path)
(remove_js if remove else install_js)(files[2])
print("Ring Symbols overlay removed." if remove else "Ring Symbols overlay installed.")
