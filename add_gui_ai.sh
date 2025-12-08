#!/bin/bash
# AI-Powered OS Enhancement Script
# This script adds GUI and AI capabilities to your existing OS

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   AI-Powered Pearl OS Style - Enhancement Script          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Phase 1: Add GUI to existing OS
echo "PHASE 1: Adding GUI Support"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "We'll configure Buildroot to add:"
echo "  • X11 window system"
echo "  • Lightweight window manager (OpenBox or i3)"
echo "  • Qt5 for modern UI"
echo "  • Python 3 for AI"
echo ""

cd ~/buildroot

# Backup current config
cp .config .config.backup.cli

echo "Adding GUI packages to configuration..."
cat >> .config << 'GUIEOF'

# X11 Support
BR2_PACKAGE_XORG7=y
BR2_PACKAGE_XSERVER_XORG_SERVER=y
BR2_PACKAGE_XSERVER_XORG_SERVER_MODULAR=y

# Window Manager
BR2_PACKAGE_OPENBOX=y

# Terminal
BR2_PACKAGE_XTERM=y

# Qt5 for modern apps
BR2_PACKAGE_QT5=y
BR2_PACKAGE_QT5BASE=y
BR2_PACKAGE_QT5BASE_GUI=y
BR2_PACKAGE_QT5BASE_WIDGETS=y

# Python for AI
BR2_PACKAGE_PYTHON3=y
BR2_PACKAGE_PYTHON3_PIP=y
BR2_PACKAGE_PYTHON3_SSL=y
BR2_PACKAGE_PYTHON3_ZLIB=y

# File manager
BR2_PACKAGE_MC=y

# Increase rootfs size
BR2_TARGET_ROOTFS_EXT2_SIZE="4G"

GUIEOF

echo "✅ Configuration updated"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "NEXT STEPS:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "1. Apply configuration:"
echo "   $ cd ~/buildroot"
echo "   $ make olddefconfig"
echo ""
echo "2. Rebuild OS (this will take 2-3 hours):"
echo "   $ make -j8"
echo ""
echo "3. After rebuild, we'll:"
echo "   • Download Pearl OS ISO"
echo "   • Extract KDE themes"
echo "   • Install Ollama AI"
echo "   • Create AI control system"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Ready to start rebuild? (y/n)"
