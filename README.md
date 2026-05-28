# Retro Wormhole GIF

Animated wormhole and black-hole GIF enhancement for the Stargate Retro web interface.

This repository is private while it is being checked and verified.

## Install

Clone or unzip this add-on into `/home/pi`, then run:

```bash
cd /home/pi
rm -rf Retro-Wormhole-GIF
git clone https://github.com/matelv-x/Retro-Wormhole-GIF.git
cd Retro-Wormhole-GIF
chmod +x install.sh restore.sh
sudo ./install.sh --target /home/pi/sg1_v4
sudo systemctl restart stargate.service
```

## Restore / uninstall

```bash
cd /home/pi/Retro-Wormhole-GIF
sudo ./restore.sh --target /home/pi/sg1_v4
sudo systemctl restart stargate.service
```

## What it changes

- Adds `wormhole.gif` and `blackhole.gif`.
- Patches Retro `dial.html`, `dial9.html`, and related CSS.
- Supports `--keep-crosshair` and `--dry-run`.

## Attribution and originality

Original base project: StargateProject SG1 software from the BuildAStargate/Jordan/Kristian/Jonnerd project lineage.

Retro UI source credit: The Retro pages being patched come from the Polklabs Retro UI project:
https://github.com/polklabs/stargate-retro

matelv-x/Codex modification: this repository adds the wormhole/black-hole GIF overlay behavior and packaging for the SG1 v4 Retro web interface.

How much is copied or changed: Medium Retro UI asset/HTML/CSS overlay.
