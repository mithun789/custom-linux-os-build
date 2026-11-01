#!/usr/bin/env bash
# Orchard OS ISO builder.
#
# Builds a bootable, installable live ISO (BIOS + UEFI, USB-hybrid) based on
# Ubuntu 24.04 LTS with a macOS-style XFCE desktop.
#
# Usage: sudo ./build-iso.sh [--work DIR] [--out DIR] [--clean] [--from STAGE]
#
# Stages: base packages themes config squashfs iso
# Each finished stage leaves a marker in $WORK/.done-<stage>, so a failed
# build resumes where it stopped. Use --from STAGE to force a rerun from a stage.
#
# Host requirements (Ubuntu/Debian):
#   apt-get install debootstrap squashfs-tools xorriso grub-pc-bin \
#     grub-efi-amd64-bin grub-common mtools dosfstools git python3-pil librsvg2-bin \
#     imagemagick fonts-inter

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=config/orchard.conf
source "$HERE/config/orchard.conf"

WORK="${WORK:-/var/tmp/orchard-build}"
OUT="${OUT:-$HERE/out}"
FROM=""
CLEAN=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --work) WORK="$2"; shift 2 ;;
        --out) OUT="$2"; shift 2 ;;
        --from) FROM="$2"; shift 2 ;;
        --clean) CLEAN=1; shift ;;
        -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
done

[[ $EUID -eq 0 ]] || { echo "run as root" >&2; exit 1; }

CHROOT="$WORK/chroot"
ISODIR="$WORK/iso"
SRC="$WORK/src"
STAGES=(base packages themes config squashfs iso)

log() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }


if [[ -n "$FROM" ]]; then
    hit=0
    for s in "${STAGES[@]}"; do
        [[ "$s" == "$FROM" ]] && hit=1
        [[ $hit -eq 1 ]] && rm -f "$WORK/.done-$s"
    done
    [[ $hit -eq 1 ]] || { echo "unknown stage: $FROM" >&2; exit 2; }
fi

mount_chroot() {
    for d in dev dev/pts proc sys run; do
        mkdir -p "$CHROOT/$d"
        mountpoint -q "$CHROOT/$d" || mount --bind "/$d" "$CHROOT/$d"
    done
}

umount_chroot() {
    for d in run sys proc dev/pts dev; do
        mountpoint -q "$CHROOT/$d" 2>/dev/null && umount -l "$CHROOT/$d"
    done
    return 0
}
trap umount_chroot EXIT

if [[ $CLEAN -eq 1 ]]; then
    log "Cleaning $WORK"
    umount_chroot
    for d in dev/pts dev proc sys run; do
        if mountpoint -q "$CHROOT/$d" 2>/dev/null; then
            echo "refusing to delete: $CHROOT/$d still mounted" >&2; exit 1
        fi
    done
    rm -rf --one-file-system "$WORK"
fi
mkdir -p "$WORK" "$OUT" "$SRC"

in_chroot() {
    chroot "$CHROOT" /usr/bin/env -i \
        HOME=/root TERM="${TERM:-xterm}" LANG=C.UTF-8 \
        PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        DEBIAN_FRONTEND=noninteractive ORCHARD_NO_SNAPSHOT=1 \
        "$@"
}

stage() {
    local name="$1"; shift
    if [[ -f "$WORK/.done-$name" ]]; then
        log "Stage '$name' already done, skipping"
        return 0
    fi
    log "Stage: $name"
    "$@"
    touch "$WORK/.done-$name"
}

# ---------------------------------------------------------------- base
stage_base() {
    rm -rf "$CHROOT"
    debootstrap --arch=amd64 --variant=minbase \
        --components=main,restricted,universe,multiverse \
        "$UBUNTU_SUITE" "$CHROOT" "$UBUNTU_MIRROR"
}

# ------------------------------------------------------------ packages
stage_packages() {
    cat > "$CHROOT/etc/apt/sources.list" <<EOF
deb $UBUNTU_MIRROR $UBUNTU_SUITE main restricted universe multiverse
deb $UBUNTU_MIRROR $UBUNTU_SUITE-updates main restricted universe multiverse
deb $UBUNTU_MIRROR $UBUNTU_SUITE-backports main restricted universe multiverse
deb $UBUNTU_SECURITY_MIRROR $UBUNTU_SUITE-security main restricted universe multiverse
EOF
    # Keep snapd out. Orchard OS uses deb + Flatpak.
    mkdir -p "$CHROOT/etc/apt/preferences.d"
    cp "$HERE/overlay/etc/apt/preferences.d/orchard-no-snap.pref" "$CHROOT/etc/apt/preferences.d/"
    echo "orchard" > "$CHROOT/etc/hostname"

    mount_chroot
    # Do not start services inside the chroot.
    printf '#!/bin/sh\nexit 101\n' > "$CHROOT/usr/sbin/policy-rc.d"
    chmod +x "$CHROOT/usr/sbin/policy-rc.d"

    in_chroot apt-get update
    in_chroot apt-get -y upgrade
    in_chroot apt-get -y install --no-install-recommends \
        $(grep -v '^\s*#' "$HERE/config/packages.list" | grep -v '^\s*$' | tr '\n' ' ')
    in_chroot apt-get -y purge snapd 2>/dev/null || true
    in_chroot apt-get -y autoremove --purge
    in_chroot apt-get clean
}

# -------------------------------------------------------------- themes
fetch_repo() {
    local name="$1" url="$2" rev="$3"
    if [[ ! -d "$SRC/$name/.git" ]]; then
        git clone --filter=blob:none "$url" "$SRC/$name"
    fi
    git -C "$SRC/$name" fetch -q --depth 1 origin "$rev" || true
    git -C "$SRC/$name" checkout -q "$rev"
}

stage_themes() {
    fetch_repo WhiteSur-gtk-theme  https://github.com/vinceliuice/WhiteSur-gtk-theme.git  "$WHITESUR_GTK_REV"
    fetch_repo WhiteSur-icon-theme https://github.com/vinceliuice/WhiteSur-icon-theme.git "$WHITESUR_ICON_REV"
    fetch_repo WhiteSur-cursors    https://github.com/vinceliuice/WhiteSur-cursors.git    "$WHITESUR_CURSOR_REV"

    local themes="$CHROOT/usr/share/themes" icons="$CHROOT/usr/share/icons"
    mkdir -p "$themes" "$icons"
    for v in WhiteSur-Light WhiteSur-Dark WhiteSur-Light-solid WhiteSur-Dark-solid; do
        rm -rf "${themes:?}/$v"
        tar -xJf "$SRC/WhiteSur-gtk-theme/release/$v.tar.xz" -C "$themes"
    done
    rm -rf "$icons/WhiteSur-cursors"
    cp -a "$SRC/WhiteSur-cursors/dist" "$icons/WhiteSur-cursors"
    "$HERE/scripts/install-whitesur-icons.sh" "$SRC/WhiteSur-icon-theme" "$icons"
    for d in WhiteSur WhiteSur-dark WhiteSur-cursors; do
        in_chroot gtk-update-icon-cache -f "/usr/share/icons/$d" || true
    done
    # GTK4 / libadwaita apps follow the light/dark preference via the portal,
    # and the gtk-4.0 folder of the theme is linked per-user by orchard-appearance.
}

# -------------------------------------------------------------- config
stage_config() {
    mount_chroot
    log "Installing any packages added to the list since the packages stage"
    in_chroot apt-get update
    in_chroot apt-get -y install --no-install-recommends \
        $(grep -v '^\s*#' "$HERE/config/packages.list" | grep -v '^\s*$' | tr '\n' ' ')
    log "Generating artwork"
    local bg="$CHROOT/usr/share/backgrounds/orchard"
    mkdir -p "$bg" "$CHROOT/usr/share/pixmaps" "$CHROOT/usr/share/orchard"
    python3 "$HERE/branding/make-wallpapers.py" "$bg"
    for s in 16 22 24 32 48 64 128 256; do
        mkdir -p "$CHROOT/usr/share/icons/hicolor/${s}x${s}/apps"
        rsvg-convert -w "$s" -h "$s" "$HERE/branding/orchard-logo.svg" \
            -o "$CHROOT/usr/share/icons/hicolor/${s}x${s}/apps/orchard-logo.png"
    done
    mkdir -p "$CHROOT/usr/share/icons/hicolor/scalable/apps"
    cp "$HERE/branding/orchard-logo.svg" "$CHROOT/usr/share/icons/hicolor/scalable/apps/orchard-logo.svg"
    rsvg-convert -w 256 -h 256 "$HERE/branding/orchard-logo.svg" -o "$CHROOT/usr/share/pixmaps/orchard-logo.png"
    in_chroot gtk-update-icon-cache -f /usr/share/icons/hicolor || true

    mkdir -p "$CHROOT/usr/share/sounds/orchard"
    python3 "$HERE/branding/make-chime.py" "$CHROOT/usr/share/sounds/orchard/login.wav"

    log "Copying overlay"
    cp -a "$HERE/overlay/." "$CHROOT/"
    chmod 0440 "$CHROOT/etc/sudoers.d/"* 2>/dev/null || true
    chmod +x "$CHROOT/usr/bin/orchard-"* "$CHROOT/usr/lib/orchard/"* 2>/dev/null || true

    # Calamares branding images.
    local cb="$CHROOT/etc/calamares/branding/orchard"
    rsvg-convert -w 128 -h 128 "$HERE/branding/orchard-logo.svg" -o "$cb/logo.png"
    convert "$bg/orchard-light.png" -resize 800x450^ -gravity center -extent 800x450 "$cb/welcome.png"
    convert "$bg/orchard-dark.png" -resize 800x450^ -gravity center -extent 800x450 "$cb/slide1.png"

    # Plymouth boot splash: logo + wordmark on a dark background.
    local pt="$CHROOT/usr/share/plymouth/themes/orchard"
    rsvg-convert -w 160 -h 160 "$HERE/branding/orchard-logo.svg" -o "$pt/logo.png"

    # Login screen wordmark (logo + name).
    cat > "$WORK/greeter-logo.svg" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="360" height="72">
  <image x="0" y="4" width="64" height="64" xlink:href="file://$HERE/branding/orchard-logo.svg"/>
  <text x="76" y="48" font-family="Inter, DejaVu Sans, sans-serif" font-size="34" font-weight="700" fill="#FFFFFF">Orchard OS</text>
</svg>
SVG
    rsvg-convert --unlimited "$WORK/greeter-logo.svg" -o "$CHROOT/usr/share/orchard/greeter-logo.png" 2>/dev/null \
        || cp "$CHROOT/usr/share/pixmaps/orchard-logo.png" "$CHROOT/usr/share/orchard/greeter-logo.png"

    # GRUB theme background.
    convert "$bg/orchard-dark.png" -resize 1920x1080 "$CHROOT/usr/share/orchard/grub-background.png"

    log "Running chroot configuration hook"
    cp "$HERE/hooks/configure-chroot.sh" "$CHROOT/tmp/configure-chroot.sh"
    in_chroot ORCHARD_VERSION="$ORCHARD_VERSION" ORCHARD_CODENAME="$ORCHARD_CODENAME" \
        bash /tmp/configure-chroot.sh
    rm -f "$CHROOT/tmp/configure-chroot.sh"
}

# ------------------------------------------------------------ squashfs
stage_squashfs() {
    mount_chroot
    in_chroot apt-get clean
    rm -f "$CHROOT/usr/sbin/policy-rc.d"
    umount_chroot

    # Clean machine-specific and temporary state.
    rm -rf "$CHROOT"/tmp/* "$CHROOT"/var/tmp/* "$CHROOT"/var/lib/apt/lists/* \
           "$CHROOT"/var/cache/apt/*.bin "$CHROOT"/root/.bash_history
    : > "$CHROOT/etc/machine-id"
    rm -f "$CHROOT/var/lib/dbus/machine-id"
    mkdir -p "$CHROOT/var/lib/apt/lists/partial"

    rm -rf "$ISODIR"
    mkdir -p "$ISODIR/casper" "$ISODIR/boot/grub" "$ISODIR/.disk"

    local kver
    kver="$(ls "$CHROOT/boot" | sed -n 's/^vmlinuz-//p' | sort -V | tail -1)"
    cp "$CHROOT/boot/vmlinuz-$kver" "$ISODIR/casper/vmlinuz"
    cp "$CHROOT/boot/initrd.img-$kver" "$ISODIR/casper/initrd"

    chroot "$CHROOT" dpkg-query -W --showformat='${Package} ${Version}\n' > "$ISODIR/casper/filesystem.manifest"
    # Packages removed from the installed system by the installer.
    printf 'casper\ncalamares\n' > "$ISODIR/casper/filesystem.manifest-remove"

    mksquashfs "$CHROOT" "$ISODIR/casper/filesystem.squashfs" \
        -noappend -comp "$SQUASHFS_COMP" -b 1M -wildcards \
        -e 'proc/*' -e 'sys/*' -e 'dev/*' -e 'run/*' -e 'tmp/*'
    du -sx --block-size=1 "$CHROOT" | cut -f1 > "$ISODIR/casper/filesystem.size"

    echo "Orchard OS $ORCHARD_VERSION \"$ORCHARD_CODENAME\" - amd64 ($(date -u +%Y%m%d))" > "$ISODIR/.disk/info"
    touch "$ISODIR/.disk/base_installable"
    echo "full_cd/single" > "$ISODIR/.disk/cd_type"
}

# ----------------------------------------------------------------- iso
stage_iso() {
    cp "$HERE/config/grub-live.cfg" "$ISODIR/boot/grub/grub.cfg"
    sed -i "s/@VERSION@/$ORCHARD_VERSION/g" "$ISODIR/boot/grub/grub.cfg"
    mkdir -p "$ISODIR/boot/grub/themes/orchard"
    cp "$CHROOT/usr/share/orchard/grub-background.png" "$ISODIR/boot/grub/themes/orchard/background.png"
    cp "$HERE/overlay/usr/share/grub/themes/orchard/theme.txt" "$ISODIR/boot/grub/themes/orchard/theme.txt"
    if [[ -f /usr/share/grub/unicode.pf2 ]]; then
        cp /usr/share/grub/unicode.pf2 "$ISODIR/boot/grub/unicode.pf2"
    fi

    (cd "$ISODIR" && find . -type f ! -name md5sum.txt ! -path './boot/grub/*' -print0 \
        | xargs -0 md5sum > md5sum.txt)

    local iso="$OUT/orchard-os-$ORCHARD_VERSION-amd64.iso"
    grub-mkrescue -o "$iso" "$ISODIR" \
        --compress=xz \
        -- -volid "ORCHARD_OS"
    (cd "$OUT" && sha256sum "$(basename "$iso")" > "$(basename "$iso").sha256")
    log "ISO ready: $iso ($(du -h "$iso" | cut -f1))"
}

stage base stage_base
stage packages stage_packages
stage themes stage_themes
stage config stage_config
stage squashfs stage_squashfs
stage iso stage_iso
