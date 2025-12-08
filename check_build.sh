#!/bin/bash
# Simple build status checker

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         AI-POWERED LINUX OS - BUILD STATUS                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if pgrep -f "make -j8" > /dev/null 2>&1; then
    echo "Status: 🟢 BUILDING"
    BUILD_PID=$(pgrep -f "make -j8" | head -1)
    ELAPSED=$(ps -o etime= -p $BUILD_PID 2>/dev/null | tr -d ' ')
    echo "Time Elapsed: $ELAPSED"
else
    echo "Status: 🔴 NOT RUNNING"
    if [ -f ~/buildroot/output/images/bzImage ]; then
        echo "✅ BUILD COMPLETE!"
    elif grep -q "Error" ~/buildroot/build.log 2>/dev/null; then
        echo "❌ BUILD FAILED - Check ~/buildroot/build.log"
    fi
fi

echo ""
echo "Recent Activity:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -10 ~/buildroot/build.log 2>/dev/null | sed 's/^/  /'

echo ""
echo "System Resources:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "  Memory: $(free -h | awk '/^Mem:/ {printf "%s used / %s total", $3, $2}')"
echo "  Disk Free: $(df -h ~ | tail -1 | awk '{print $4}')"

echo ""
echo "Commands:"
echo "  Watch live: tail -f ~/buildroot/build.log"
echo "  This status: ~/Desktop/Mos/custom-linux-os-build/check_build.sh"
