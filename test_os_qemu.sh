#!/bin/bash
# Quick QEMU Test Script for Your Custom Linux OS

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       Testing Your AI-Powered Custom Linux OS              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if QEMU is installed
if ! command -v qemu-system-x86_64 &> /dev/null; then
    echo "⚠️  QEMU not found. Installing..."
    echo ""
    read -p "Install QEMU? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt update
        sudo apt install -y qemu-system-x86
    else
        echo "Please install QEMU first: sudo apt install qemu-system-x86"
        exit 1
    fi
fi

# Check if disk image exists
if [ ! -f ~/buildroot/output/images/disk.img ]; then
    echo "❌ Error: disk.img not found!"
    echo "Please build the OS first."
    exit 1
fi

echo "✅ Found custom Linux OS image"
echo ""
echo "Starting QEMU..."
echo ""
echo "💡 Tips:"
echo "  - Login as: root (no password)"
echo "  - Shut down: poweroff or halt"
echo "  - Exit QEMU: Ctrl+A then X"
echo ""
echo "Press Enter to start..."
read

cd ~/buildroot/output/images

# Run QEMU with your custom OS
qemu-system-x86_64 \
    -drive file=disk.img,format=raw \
    -m 2G \
    -enable-kvm \
    -cpu host \
    -smp 4 \
    -netdev user,id=net0 \
    -device e1000,netdev=net0 \
    -name "Custom AI-Powered Linux OS"

echo ""
echo "QEMU session ended."
