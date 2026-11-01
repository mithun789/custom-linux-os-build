#!/bin/bash
#
# Configure GUI for Custom OS - Pearl OS Style
# This script adds a Qt5-based desktop environment to our Buildroot OS
#

set -e

CONFIG_FILE="$HOME/buildroot/.config"
BACKUP_FILE="$HOME/buildroot/.config.backup-$(date +%Y%m%d-%H%M%S)"

echo "==================================="
echo "GUI Configuration for Custom OS"
echo "Target: Pearl OS inspired desktop"
echo "==================================="
echo

# Check if we're in the right place
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Buildroot .config not found at $CONFIG_FILE"
    echo "Please run this from the project directory"
    exit 1
fi

# Backup current config
echo "📦 Backing up current configuration..."
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "   Backup saved to: $BACKUP_FILE"
echo

# Add GUI packages
echo "🖥️  Adding GUI components to Buildroot configuration..."
echo

cat >> "$CONFIG_FILE" << 'EOF'

#
# GUI Configuration - Added by configure_gui.sh
#

# X11 Window System
BR2_PACKAGE_X11R7=y
BR2_PACKAGE_XORG7=y
BR2_PACKAGE_XSERVER_XORG_SERVER=y
BR2_PACKAGE_XSERVER_XORG_SERVER_MODULAR=y

# X11 drivers
BR2_PACKAGE_XDRIVER_XF86_INPUT_EVDEV=y
BR2_PACKAGE_XDRIVER_XF86_INPUT_KEYBOARD=y
BR2_PACKAGE_XDRIVER_XF86_INPUT_MOUSE=y
BR2_PACKAGE_XDRIVER_XF86_VIDEO_VESA=y
BR2_PACKAGE_XDRIVER_XF86_VIDEO_FBDEV=y

# X11 applications
BR2_PACKAGE_XTERM=y
BR2_PACKAGE_XAPP_XINIT=y
BR2_PACKAGE_XAPP_XAUTH=y

# Window Manager - OpenBox (lightweight)
BR2_PACKAGE_OPENBOX=y

# Qt5 Framework (for Pearl OS compatibility)
BR2_PACKAGE_QT5=y
BR2_PACKAGE_QT5BASE=y
BR2_PACKAGE_QT5BASE_CONCURRENT=y
BR2_PACKAGE_QT5BASE_GUI=y
BR2_PACKAGE_QT5BASE_WIDGETS=y
BR2_PACKAGE_QT5BASE_LINUXFB=y
BR2_PACKAGE_QT5BASE_XCB=y
BR2_PACKAGE_QT5BASE_OPENGL=y
BR2_PACKAGE_QT5BASE_OPENGL_DESKTOP=y

# Qt5 modules
BR2_PACKAGE_QT5QUICKCONTROLS=y
BR2_PACKAGE_QT5QUICKCONTROLS2=y
BR2_PACKAGE_QT5DECLARATIVE=y
BR2_PACKAGE_QT5GRAPHICALEFFECTS=y
BR2_PACKAGE_QT5SVG=y

# Mesa 3D (OpenGL support)
BR2_PACKAGE_MESA3D=y
BR2_PACKAGE_MESA3D_OPENGL_EGL=y
BR2_PACKAGE_MESA3D_OPENGL_ES=y

# GTK3 (for compatibility with some apps)
BR2_PACKAGE_LIBGTK3=y
BR2_PACKAGE_LIBGTK3_X11=y

# File Manager - PCManFM (lightweight Qt alternative)
BR2_PACKAGE_PCMANFM=y

# Image viewer
BR2_PACKAGE_ELINKS=y

# Audio support
BR2_PACKAGE_ALSA_UTILS=y
BR2_PACKAGE_PULSEAUDIO=y

# Fonts
BR2_PACKAGE_DEJAVU=y
BR2_PACKAGE_LIBERATION=y

# Python for AI integration
BR2_PACKAGE_PYTHON3=y
BR2_PACKAGE_PYTHON3_PIP=y
BR2_PACKAGE_PYTHON3_SQLITE=y
BR2_PACKAGE_PYTHON_NUMPY=y

# System utilities
BR2_PACKAGE_HTOP=y
BR2_PACKAGE_TMUX=y

# Increase root filesystem size for GUI
BR2_TARGET_ROOTFS_EXT2_SIZE="6G"

EOF

echo "✅ GUI packages added to configuration"
echo

# Run olddefconfig to resolve dependencies
echo "🔧 Resolving package dependencies..."
cd "$HOME/buildroot"
make olddefconfig > /dev/null 2>&1

echo "✅ Configuration updated successfully!"
echo
echo "==================================="
echo "Next Steps:"
echo "==================================="
echo
echo "1. Start the build process:"
echo "   cd ~/buildroot"
echo "   make -j\$(nproc)"
echo
echo "2. Expected build time: 2-4 hours"
echo
echo "3. After build completes, test in QEMU:"
echo "   cd ~/Desktop/Mos/custom-linux-os-build"
echo "   ./test_os_qemu.sh"
echo
echo "4. Once GUI is working, we'll add Pearl OS themes"
echo
echo "Configuration backup: $BACKUP_FILE"
echo "==================================="
echo

# Ask user if they want to start build now
read -p "Start build now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo
    echo "🚀 Starting build process..."
    echo "This will take 2-4 hours depending on your system"
    echo
    cd "$HOME/buildroot"
    time make -j$(nproc) 2>&1 | tee ~/Desktop/Mos/custom-linux-os-build/gui-build.log
    
    if [ $? -eq 0 ]; then
        echo
        echo "✅ Build completed successfully!"
        echo "   Output: ~/buildroot/output/images/"
        ls -lh ~/buildroot/output/images/disk.img
    else
        echo
        echo "❌ Build failed. Check log: ~/Desktop/Mos/custom-linux-os-build/gui-build.log"
        exit 1
    fi
else
    echo
    echo "Build not started. Run manually when ready:"
    echo "  cd ~/buildroot && make -j\$(nproc)"
fi
