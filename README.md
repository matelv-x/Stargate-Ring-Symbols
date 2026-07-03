# Stargate Ring Symbols Overlay Upgrade

[![Downloads](https://img.shields.io/github/downloads/matelv-x/Stargate-Ring-Symbols/total?label=downloads)](https://github.com/matelv-x/Stargate-Ring-Symbols/releases)

Surgical overlay add-on for the Retro web interface. It adds SG-1 ring symbols and ring-position animation to Retro dial pages.

<img width="3456" height="2060" alt="image" src="https://github.com/user-attachments/assets/bd1f4bc5-c810-4982-8c7b-2452e6fe3d1a" />

## Install

## Method 1 — GitHub Clone (Recommended)

```bash
cd /home/pi
rm -rf Stargate-Ring-Symbols
git clone https://github.com/matelv-x/Stargate-Ring-Symbols.git
cd Stargate-Ring-Symbols
chmod +x apply-ring-symbols-upgrade.sh restore.sh
sudo ./apply-ring-symbols-upgrade.sh /home/pi/sg1_v4/web
sudo systemctl restart stargate.service
```
## Method 2 — ZIP Download

Download and extract the ZIP archive into:
```bash
/home/pi/Stargate-Ring-Symbols
```
Then run:
```bash
cd Stargate-Ring-Symbols
chmod +x apply-ring-symbols-upgrade.sh restore.sh
sudo ./apply-ring-symbols-upgrade.sh /home/pi/sg1_v4/web
sudo systemctl restart stargate.service
```

## Restore / uninstall,

```bash
cd /home/pi/Stargate-Ring-Symbols
sudo ./restore.sh /home/pi/sg1_v4/web
sudo systemctl restart stargate.service
```

## What it changes,

- Updates only its own marked blocks inside `retro/dial.html`, `retro/dial9.html`, and `retro/js/dial.js`.
- Preserves Wormhole GIF and other additions already present in those files.
- Creates a timestamped backup before every install or removal.
- Does not patch classic `web/symbol_overview.htm`.
- Adds auto visual home parking: when Retro sees the gate return to idle with no outgoing or incoming address buffer and no active wormhole, the visual ring parks `ring_position = 0`, meaning the Earth symbol is shown at 12 o'clock. This also covers aborted or incomplete dialing after the backend clears the buffers.

## Attribution and originality

Retro UI source credit: The Retro pages and JavaScript being patched come from the Polklabs Retro UI project:
https://github.com/polklabs/stargate-retro

matelv-x/Codex modification: this repository adds SG-1 ring symbols and ring-position animation patches on top of the Polklabs Retro UI integration.

How much is copied or changed: Medium Retro UI patch. It ships patch files and an installer, not full replacement Retro pages.
