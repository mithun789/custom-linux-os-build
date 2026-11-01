# Orchard OS build system

This folder builds the Orchard OS installer ISO from scratch.

## Layout

| Path | What it holds |
|------|---------------|
| `build-iso.sh` | Main builder. Stages: base, packages, themes, config, squashfs, iso |
| `config/orchard.conf` | Version, Ubuntu mirror, pinned theme revisions |
| `config/packages.list` | Every package in the image |
| `config/grub-live.cfg` | Boot menu of the ISO |
| `hooks/configure-chroot.sh` | Runs inside the image: identity, locale, desktop defaults, splash, services |
| `overlay/` | Files copied as-is into the image (desktop config, installer config, Orchard tools) |
| `branding/` | Logo (SVG) and wallpaper generator |
| `scripts/install-whitesur-icons.sh` | Installs the WhiteSur icon theme without prompts |
| `test/qemu-test.py` | Automated boot and install tests in QEMU |

## Build

You need an Ubuntu 24.04 or Debian 12 machine (a cloud VM works), root, about 25 GB of free disk and internet access.

```bash
sudo apt-get install -y debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin \
  grub-common mtools dosfstools git python3-pil librsvg2-bin imagemagick fonts-inter
```

```bash
sudo ./build-iso.sh
```

The ISO lands in `out/orchard-os-<version>-amd64.iso` with a `.sha256` file. A first build takes about 20 minutes on a 4-core server.

Useful options:

```bash
sudo ./build-iso.sh --from config     # rerun from a stage after editing overlay/ or hooks/
sudo ./build-iso.sh --clean           # start over
sudo SQUASHFS_COMP=zstd ./build-iso.sh  # faster compression for test builds
```

## Test

```bash
sudo apt-get install -y qemu-system-x86 qemu-utils ovmf python3-pexpect
```

```bash
sudo python3 test/qemu-test.py out/orchard-os-1.0-amd64.iso --out test-results
```

The test boots the ISO on BIOS and UEFI, logs in to the live session over the serial console, checks that the desktop, dock and installer start, installs to a virtual disk with `orchard-install`, then boots the installed disk on BIOS and UEFI. Screenshots go to `test-results/`. It uses KVM when `/dev/kvm` exists and falls back to software emulation (about 4x slower).

## Change things

- Add or remove apps: edit `config/packages.list`, then `sudo ./build-iso.sh --from config`.
- Desktop defaults: `hooks/configure-chroot.sh` (xfconf section) and `overlay/etc/xdg/xfce4/panel/default.xml`.
- Dock icons: `overlay/etc/skel/.config/plank/dock1/launchers/` and the `dock-items` list in `overlay/etc/dconf/db/local.d/00-orchard`.
- Wallpapers: `branding/make-wallpapers.py`.
- Version and name: `config/orchard.conf` and `overlay/usr/lib/os-release.orchard`.
