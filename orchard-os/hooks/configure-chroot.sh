#!/usr/bin/env bash
# Runs inside the image chroot after the overlay is copied.
set -euo pipefail
echo "[hook] Orchard OS $ORCHARD_VERSION ($ORCHARD_CODENAME)"

# ---- Identity -------------------------------------------------------------
if [[ -f /usr/lib/os-release.orchard ]]; then
    dpkg-divert --local --rename --divert /usr/lib/os-release.ubuntu --add /usr/lib/os-release
    mv /usr/lib/os-release.orchard /usr/lib/os-release
fi
ln -sf ../usr/lib/os-release /etc/os-release
# lsb-release keeps DISTRIB_ID=Ubuntu so add-apt-repository and PPAs keep working.
sed -i "s/^DISTRIB_DESCRIPTION=.*/DISTRIB_DESCRIPTION=\"Orchard OS $ORCHARD_VERSION ($ORCHARD_CODENAME)\"/" /etc/lsb-release
if [[ -f /etc/issue.orchard ]]; then
    mv /etc/issue.orchard /etc/issue
    printf 'Orchard OS %s\n' "$ORCHARD_VERSION" > /etc/issue.net
fi

# Console login message: drop Ubuntu help, ESM and news adverts.
for f in 10-help-text 50-motd-news 91-contract-ua-esm-status 50-landscape-sysinfo 91-release-upgrade 95-hwe-eol; do
    [[ -f /etc/update-motd.d/$f ]] && chmod -x /etc/update-motd.d/$f
done
sed -i 's/^ENABLED=.*/ENABLED=0/' /etc/default/motd-news 2>/dev/null || true
cat > /etc/update-motd.d/00-header <<'MOTD'
#!/bin/sh
. /etc/os-release
printf 'Welcome to %s (%s %s)\n\n' "$PRETTY_NAME" "$(uname -o)" "$(uname -r)"
printf ' * Update everything:  orchard-update\n * Local AI assistant: orchard-ai help\n * Free disk space:    orchard-clean\n\n'
MOTD
chmod +x /etc/update-motd.d/00-header
cat > /etc/legal <<'LEGAL'

Orchard OS is built from free software. The license of each program is in
/usr/share/doc/*/copyright. Orchard OS comes with ABSOLUTELY NO WARRANTY,
to the extent permitted by applicable law.

LEGAL

# ---- Locale ---------------------------------------------------------------
{
    echo "# Locales to generate. Uncomment a line and run 'sudo locale-gen'."
    grep -v '^en_US.UTF-8 ' /usr/share/i18n/SUPPORTED | sed 's/^/# /'
} > /etc/locale.gen.tmp
sed -i '1a en_US.UTF-8 UTF-8' /etc/locale.gen.tmp
mv /etc/locale.gen.tmp /etc/locale.gen
locale-gen
update-locale LANG=en_US.UTF-8

# ---- Desktop defaults (xfconf system files) ------------------------------
python3 - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path("/etc/xdg/xfce4/xfconf/xfce-perchannel-xml")
BASE.mkdir(parents=True, exist_ok=True)

def setprops(channel, props):
    path = BASE / f"{channel}.xml"
    if path.exists():
        tree = ET.parse(path)
        root = tree.getroot()
    else:
        root = ET.Element("channel", name=channel, version="1.0")
        tree = ET.ElementTree(root)
    for prop_path, typ, value in props:
        node = root
        parts = prop_path.strip("/").split("/")
        for i, name in enumerate(parts):
            child = next((c for c in node.findall("property") if c.get("name") == name), None)
            if child is None:
                child = ET.SubElement(node, "property", name=name, type="empty")
            node = child
        node.set("type", typ)
        node.set("value", str(value))
    ET.indent(tree)
    tree.write(path, encoding="UTF-8", xml_declaration=True)

setprops("xsettings", [
    ("/Net/ThemeName", "string", "WhiteSur-Light"),
    ("/Net/IconThemeName", "string", "WhiteSur"),
    ("/Net/SoundThemeName", "string", "freedesktop"),
    ("/Gtk/CursorThemeName", "string", "WhiteSur-cursors"),
    ("/Gtk/CursorThemeSize", "int", 24),
    ("/Gtk/FontName", "string", "Inter 10"),
    ("/Gtk/MonospaceFontName", "string", "JetBrains Mono 10"),
    ("/Gtk/DecorationLayout", "string", "close,minimize,maximize:"),
    ("/Gtk/DialogsUseHeader", "bool", "true"),
    ("/Xft/Antialias", "int", 1),
    ("/Xft/Hinting", "int", 1),
    ("/Xft/HintStyle", "string", "hintslight"),
    ("/Xft/RGBA", "string", "rgb"),
])
setprops("xfwm4", [
    ("/general/theme", "string", "WhiteSur-Light"),
    ("/general/button_layout", "string", "CHM|"),
    ("/general/title_alignment", "string", "center"),
    ("/general/title_font", "string", "Inter Semi-Bold 10"),
    # picom (orchard-compositor) provides blur; xfwm4 compositing is the fallback.
    ("/general/use_compositing", "bool", "false"),
    ("/general/show_dock_shadow", "bool", "false"),
    ("/general/show_frame_shadow", "bool", "true"),
    ("/general/show_popup_shadow", "bool", "true"),
    ("/general/placement_mode", "string", "center"),
    ("/general/placement_ratio", "int", 100),
    ("/general/workspace_count", "int", 2),
    ("/general/cycle_preview", "bool", "true"),
    ("/general/wrap_windows", "bool", "false"),
])
monitors = ["0", "Virtual-1", "Virtual1", "VGA-1", "VGA1", "HDMI-1", "HDMI1", "HDMI-A-1",
            "DP-1", "DP1", "eDP-1", "eDP1", "LVDS-1", "LVDS1", "default", "Default", "XWAYLAND0"]
desk = []
for m in monitors:
    for ws in range(4):
        p = f"/backdrop/screen0/monitor{m}/workspace{ws}"
        desk += [(f"{p}/last-image", "string", "/usr/share/backgrounds/orchard/orchard-light.png"),
                 (f"{p}/image-style", "int", 5)]
desk += [("/desktop-icons/file-icons/show-home", "bool", "false"),
         ("/desktop-icons/file-icons/show-filesystem", "bool", "false"),
         ("/desktop-icons/file-icons/show-trash", "bool", "true")]
setprops("xfce4-desktop", desk)
setprops("xfce4-notifyd", [
    ("/theme", "string", "Default"),
    ("/notify-location", "uint", 2),
    ("/initial-opacity", "double", 0.95),
])
setprops("xfce4-session", [
    ("/general/SaveOnExit", "bool", "false"),
])
setprops("thunar", [
    ("/last-view", "string", "ThunarIconView"),
    ("/misc-single-click", "bool", "false"),
    ("/last-side-pane", "string", "ThunarShortcutsPane"),
])
PY

# GTK defaults for apps started as root (installer, GParted) and outside XFCE.
mkdir -p /etc/gtk-3.0
cat > /etc/gtk-3.0/settings.ini <<'INI'
[Settings]
gtk-theme-name=WhiteSur-Light
gtk-icon-theme-name=WhiteSur
gtk-cursor-theme-name=WhiteSur-cursors
gtk-font-name=Inter 10
gtk-decoration-layout=close,minimize,maximize:
INI
grep -q QT_QPA_PLATFORMTHEME /etc/environment || echo 'QT_QPA_PLATFORMTHEME=gtk2' >> /etc/environment

# Default cursor for X (affects the greeter and root windows).
update-alternatives --install /usr/share/icons/default/index.theme x-cursor-theme \
    /usr/share/icons/WhiteSur-cursors/index.theme 90
update-alternatives --set x-cursor-theme /usr/share/icons/WhiteSur-cursors/index.theme

# ---- dconf system database (Plank dock, GTK4 apps) -----------------------
dconf update

# ---- Boot splash -----------------------------------------------------------
update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth \
    /usr/share/plymouth/themes/orchard/orchard.plymouth 200
update-alternatives --set default.plymouth /usr/share/plymouth/themes/orchard/orchard.plymouth

# ---- GRUB theme on the installed system ---------------------------------
mkdir -p /usr/share/grub/themes/orchard
cp /usr/share/orchard/grub-background.png /usr/share/grub/themes/orchard/background.png

# ---- Software sources -------------------------------------------------------
if command -v flatpak >/dev/null; then
    timeout 60 flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo \
        || echo "[hook] Flathub not reachable at build time. Users can enable it from the Welcome app."
fi

# ---- Services ---------------------------------------------------------------
systemctl set-default graphical.target
systemctl enable NetworkManager lightdm 2>/dev/null || true
systemctl disable systemd-networkd 2>/dev/null || true
# Security and memory services.
systemctl enable orchard-guard.timer orchard-scan.timer earlyoom auditd clamav-freshclam 2>/dev/null || true
# Firewall on: block incoming connections, allow outgoing.
if [[ -f /etc/ufw/ufw.conf ]]; then
    sed -i 's/^ENABLED=.*/ENABLED=yes/' /etc/ufw/ufw.conf
    sed -i 's/^DEFAULT_INPUT_POLICY=.*/DEFAULT_INPUT_POLICY="DROP"/; s/^DEFAULT_OUTPUT_POLICY=.*/DEFAULT_OUTPUT_POLICY="ACCEPT"/' /etc/default/ufw
    systemctl enable ufw 2>/dev/null || true
fi
mkdir -p /var/log/orchard
# Keep the system journal on disk so the agent and Guard can read history.
mkdir -p /var/log/journal /etc/systemd/journald.conf.d
printf '[Journal]\nStorage=persistent\nSystemMaxUse=500M\n' > /etc/systemd/journald.conf.d/orchard.conf
# NetworkManager manages every interface (Ubuntu minimal defaults to netplan/networkd).
mkdir -p /etc/netplan
cat > /etc/netplan/01-network-manager-all.yaml <<'NP'
network:
  version: 2
  renderer: NetworkManager
NP
chmod 600 /etc/netplan/01-network-manager-all.yaml

# ---- Initramfs ----------------------------------------------------------------
update-initramfs -u -k all
echo "[hook] done"
