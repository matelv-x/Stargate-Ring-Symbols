#!/usr/bin/env python3
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys


def fail(message):
    raise SystemExit(f"ERROR: {message}")


def load(name):
    return (assets / name).read_text(encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, payload):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def prepare_install_state(files):
    state_dir = target / ".stargate-ring-symbols-addon"
    state_file = state_dir / "state.json"
    if state_file.is_file():
        state = json.loads(state_file.read_text(encoding="utf-8"))
        if state.get("schema") != 1:
            fail("unsupported Ring Symbols state schema")
        for path in files:
            key = str(path.relative_to(target))
            original = state_dir / "originals" / key
            if key not in state.get("files", {}) or not original.is_file():
                fail(f"incomplete Ring Symbols state for {key}")
        return state

    state = {"schema": 1, "files": {}}
    for path in files:
        key = str(path.relative_to(target))
        original = state_dir / "originals" / key
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, original)
        state["files"][key] = {"original_sha256": sha256(original)}
    write_json(state_file, state)
    return state


def record_installed_state(files, state):
    state_dir = target / ".stargate-ring-symbols-addon"
    for path in files:
        key = str(path.relative_to(target))
        state["files"][key]["installed_sha256"] = sha256(path)
    write_json(state_dir / "state.json", state)


def restore_recorded_state(files):
    state_dir = target / ".stargate-ring-symbols-addon"
    state_file = state_dir / "state.json"
    if not state_file.is_file():
        return False

    state = json.loads(state_file.read_text(encoding="utf-8"))
    if state.get("schema") != 1:
        fail("unsupported Ring Symbols state schema")

    restore_plan = []
    for path in files:
        key = str(path.relative_to(target))
        record = state.get("files", {}).get(key)
        original = state_dir / "originals" / key
        if not record or not original.is_file():
            fail(f"incomplete Ring Symbols uninstall state for {key}")
        if sha256(original) != record.get("original_sha256"):
            fail(f"Ring Symbols original snapshot checksum failed for {key}")
        current_hash = sha256(path)
        allowed = {record.get("original_sha256"), record.get("installed_sha256")}
        if current_hash not in allowed:
            fail(f"refusing to overwrite later changes in {key}")
        if current_hash != record.get("original_sha256"):
            restore_plan.append((original, path))

    for original, path in restore_plan:
        shutil.copy2(original, path)
        print(f"Restored exact pre-install file: {path}")
    shutil.rmtree(state_dir)
    return True


def restore_legacy_state(files):
    html_files = files[:2]
    js_file = files[2]
    if not all("sg1-ring-segment" in path.read_text(encoding="utf-8", errors="replace") for path in html_files):
        fail("legacy Ring Symbols markers are incomplete; no files were restored")
    js_text = js_file.read_text(encoding="utf-8", errors="replace")
    if "centerGlyphInRing(newGlyph)" not in js_text:
        fail("legacy Ring Symbols JavaScript marker is missing; no files were restored")

    backup_root = target / "backups"
    for candidate in sorted(backup_root.glob("ring-symbols-overlay-*"), reverse=True):
        originals = [candidate / path.relative_to(target) for path in files]
        if not all(path.is_file() for path in originals):
            continue
        first_html = originals[0].read_text(encoding="utf-8", errors="replace")
        second_html = originals[1].read_text(encoding="utf-8", errors="replace")
        if "sg1-ring-segment" in first_html or "sg1-ring-segment" in second_html:
            continue
        for original, path in zip(originals, files):
            shutil.copy2(original, path)
            print(f"Restored legacy pre-install file: {path}")
        print(f"Legacy source snapshot: {candidate}")
        return
    fail("no safe pre-install Ring Symbols snapshot was found")


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
        r"\n?function centerGlyphInRing\(glyph\) \{[\s\S]*?\n\}\n"
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
    # Retro Visuals owns shouldDisplayIncomingGlyphs and its incoming-symbol
    # behavior. Restore the legacy guards only when that separate integration
    # is not present.
    if "function shouldDisplayIncomingGlyphs()" not in text:
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

install_state = None if remove else prepare_install_state(files)

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

if remove:
    if not restore_recorded_state(files):
        restore_legacy_state(files)
else:
    for path in files[:2]:
        install_html(path)
    install_js(files[2])
    record_installed_state(files, install_state)
print("Ring Symbols overlay removed." if remove else "Ring Symbols overlay installed.")
