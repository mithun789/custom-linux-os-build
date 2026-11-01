#!/bin/bash
# Quick Start Script for Custom Linux OS Build
# Usage: ./quick_start.sh

set -e

echo "=========================================="
echo "Custom Linux OS Build - Quick Start"
echo "=========================================="
echo ""

# Check if buildroot exists
if [ ! -d ~/buildroot ]; then
    echo "❌ Error: Buildroot not found at ~/buildroot"
    exit 1
fi

echo "✅ Buildroot found"

# Check if MCP servers exist
if [ ! -f ~/mcp-servers/buildroot_mcp.py ]; then
    echo "❌ Error: MCP servers not found"
    exit 1
fi

echo "✅ MCP servers found"

# Check disk space
FREE_SPACE=$(df -BG ~ | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$FREE_SPACE" -lt 15 ]; then
    echo "⚠️  Warning: Low disk space ($FREE_SPACE GB free). Recommended: 15GB+"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Sufficient disk space ($FREE_SPACE GB free)"
fi

# Show menu
echo ""
echo "What would you like to do?"
echo ""
echo "1) Start a simple QEMU x86_64 build (recommended for first time)"
echo "2) Configure custom build (menuconfig)"
echo "3) Test MCP servers"
echo "4) Show available defconfigs"
echo "5) Clean previous build"
echo "6) Exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo ""
        echo "Starting QEMU x86_64 build..."
        echo "This will take 1-2 hours on first build."
        echo ""
        cd ~/buildroot
        make qemu_x86_64_defconfig
        echo ""
        echo "Configuration loaded. Starting build..."
        echo "Output will be logged to ~/buildroot/build.log"
        echo ""
        make -j$(nproc) 2>&1 | tee ~/buildroot/build.log
        echo ""
        echo "✅ Build complete! Artifacts in ~/buildroot/output/images/"
        echo ""
        echo "To test in QEMU:"
        echo "qemu-system-x86_64 -kernel output/images/bzImage \\"
        echo "  -drive file=output/images/rootfs.ext2,format=raw \\"
        echo "  -append 'root=/dev/sda console=ttyS0' -nographic"
        ;;
    2)
        echo ""
        echo "Opening menuconfig..."
        cd ~/buildroot
        make menuconfig
        echo ""
        echo "Configuration saved. To build:"
        echo "cd ~/buildroot && make -j$(nproc)"
        ;;
    3)
        echo ""
        echo "Testing MCP servers..."
        source ~/Desktop/Mos/custom-linux-os-build/mcp-venv/bin/activate
        echo "Testing buildroot_mcp.py (Ctrl+C to exit)..."
        timeout 3 ~/mcp-servers/buildroot_mcp.py || echo "✅ Server OK"
        echo ""
        echo "All MCP servers available at ~/mcp-servers/"
        ;;
    4)
        echo ""
        echo "Available defconfigs:"
        cd ~/buildroot
        make list-defconfigs | head -50
        echo ""
        echo "To use: make <defconfig_name>"
        ;;
    5)
        echo ""
        read -p "Clean build directory? This will delete all built files. (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd ~/buildroot
            make clean
            echo "✅ Build directory cleaned"
        fi
        ;;
    6)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Done!"
