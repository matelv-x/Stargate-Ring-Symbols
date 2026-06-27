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
    style_pattern = re.compile(
        r'    <style>\s*/\* SG-1 ring-3 real 39 segment ring \+ glyphs \*/[\s\S]*?</style>\n',
        re.I,
    )
    if style_pattern.search(text):
        text = style_pattern.sub(style + "\n", text, count=1)
    else:
        marker = '    <link rel="preconnect" href="https://fonts.googleapis.com" />'
        if marker not in text:
            fail(f"cannot find style insertion point in {path}")
        text = text.replace(marker, style + "\n" + marker, 1)
    if 'class="sg1-ring-segment"' not in text:
        text = replace_ring_svg(text, ring_svg)
    loader_pattern = re.compile(
        r'    <script>\s*\(function \(\) \{\s*const centerX = 336\.5;[\s\S]*?</script>\n'
        r'(?=    <script type="module" src="js/startup\.js"></script>)',
        re.I,
    )
    if loader_pattern.search(text):
        text = loader_pattern.sub(lambda _match: loader, text, count=1)
    else:
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
    helpers_pattern = re.compile(
        r"// Backend Stargate logic:[\s\S]*?(?=\n\nlet lockedGlyphs = \{\};)",
    )
    if helpers_pattern.search(text):
        text = helpers_pattern.sub(helpers.rstrip(), text, count=1)
    else:
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
    text = text.replace(
        "buffer.length > bufferIndex &&\n      gateStatus.address_buffer_incoming.length <= 0",
        "buffer.length > bufferIndex",
        1,
    )
    text = text.replace(
        "if (bufferIndex < 9 && gateStatus.address_buffer_incoming.length <= 0) {",
        "if (bufferIndex < 9) {",
        1,
    )
    center_helper = """function shouldDisplayIncomingGlyphs() {
  return (
    gateStatus.address_buffer_incoming.length === 0 ||
    window.retroVisuals?.shouldDisplayIncomingSymbols?.() !== false
  );
}

function centerGlyphInRing(glyph) {
  const appendHost = appendTarget;
  const ringCircle = document.querySelector('.ring-1 svg .sg1-ring-border');
  const ringHost = ringCircle || document.querySelector('.ring-1 svg') || document.querySelector('.ring-1');
  if (!ringHost || !appendHost || !glyph) return;

  const ringRect = ringHost.getBoundingClientRect();
  const hostRect = appendHost.getBoundingClientRect();
  const size = Math.min(ringRect.width, ringRect.height) * 0.34;
  const centerX = ringRect.left - hostRect.left + ringRect.width / 2;
  const centerY = ringRect.top - hostRect.top + ringRect.height / 2;

  glyph.style.left = `${centerX - size / 2}px`;
  glyph.style.top = `${centerY - size / 2}px`;
  glyph.style.width = `${size}px`;
  glyph.style.height = `${size}px`;
}

function lockGlyphInBox(glyph) {
  if (!glyph) return;

  let audioStopped = false;
  const stopGlyphAudio = () => {
    if (audioStopped) return;
    audioStopped = true;
    notifyBrowserAudio('glyphLandedInBox');
  };

  glyph.addEventListener('transitionend', stopGlyphAudio, {once: true});

  glyph.style.left = '';
  glyph.style.top = '';
  glyph.style.width = '';
  glyph.style.height = '';
  glyph.classList.add('locked');

  // Fallback for browsers/styles that do not emit transitionend here.
  setTimeout(stopGlyphAudio, gateStatus.address_buffer_incoming.length > 0 ? 760 : 1150);
}

"""
    center_pattern = re.compile(
        r"\n?(?:function shouldDisplayIncomingGlyphs\(\) \{[\s\S]*?\n\}\n\n)?"
        r"function centerGlyphInRing\(glyph\) \{[\s\S]*?\n\}\n"
        r"(?:\nfunction lockGlyphInBox\(glyph\) \{[\s\S]*?\n\}\n)?\n"
        r"(?=function dial\(\) \{)",
    )
    if center_pattern.search(text):
        text = center_pattern.sub("\n" + center_helper, text, count=1)
    else:
        marker = "function dial() {"
        if marker not in text:
            fail(f"cannot find glyph centering insertion point in {path}")
        text = text.replace(marker, center_helper + marker, 1)
    text = text.replace("newGlyph.classList.add('locked')", "lockGlyphInBox(newGlyph)")
    text = text.replace("newGlyph2.classList.add('locked')", "lockGlyphInBox(newGlyph2)")
    append_variants = (
        (
            "  appendTarget.append(newGlyph2);\n"
            "  appendTarget.append(newGlyph);\n",
            "  appendTarget.append(newGlyph2);\n"
            "  appendTarget.append(newGlyph);\n"
            "  centerGlyphInRing(newGlyph);\n"
            "  centerGlyphInRing(newGlyph2);\n",
        ),
        (
            "  appendTarget.append(newGlyph);\n"
            "  appendTarget.append(newGlyph2);\n",
            "  appendTarget.append(newGlyph);\n"
            "  appendTarget.append(newGlyph2);\n"
            "  centerGlyphInRing(newGlyph);\n"
            "  centerGlyphInRing(newGlyph2);\n",
        ),
    )
    if "centerGlyphInRing(newGlyph);" not in text:
        for old, new in append_variants:
            if old in text:
                text = text.replace(old, new, 1)
                break
        else:
            fail(f"cannot find glyph append point in {path}")
    write_if_changed(path, text)


def remove_html(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text = text.replace(style + "\n", "")
    text = text.replace(style, "")
    text = text.replace(loader, "")
    text = re.sub(
        r'js/dial\.js\?v=ring-symbols-overlay-[^"\']+',
        "js/dial.js",
        text,
    )
    if 'class="sg1-ring-segment"' in text:
        text = replace_ring_svg(text, base_ring_svg)
    write_if_changed(path, text)


def remove_js(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text = text.replace(helpers, "")
    text = re.sub(
        r"\n?(?:function shouldDisplayIncomingGlyphs\(\) \{[\s\S]*?\n\}\n\n)?"
        r"function centerGlyphInRing\(glyph\) \{[\s\S]*?\n\}\n"
        r"(?:\nfunction lockGlyphInBox\(glyph\) \{[\s\S]*?\n\}\n)?\n"
        r"(?=function dial\(\) \{)",
        "\n",
        text,
        count=1,
    )
    text = text.replace("lockGlyphInBox(newGlyph)", "newGlyph.classList.add('locked')")
    text = text.replace("lockGlyphInBox(newGlyph2)", "newGlyph2.classList.add('locked')")
    text = text.replace(
        "  centerGlyphInRing(newGlyph);\n"
        "  centerGlyphInRing(newGlyph2);\n",
        "",
    )
    text = text.replace(
        "buffer.length > bufferIndex\n    ) {",
        "buffer.length > bufferIndex &&\n"
        "      gateStatus.address_buffer_incoming.length <= 0\n"
        "    ) {",
        1,
    )
    text = text.replace(
        "if (bufferIndex < 9) {",
        "if (bufferIndex < 9 && gateStatus.address_buffer_incoming.length <= 0) {",
        1,
    )
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
