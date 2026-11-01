#!/bin/bash
# Build Monitor - Shows real-time build progress

while true; do
    clear
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║       AI-POWERED LINUX OS BUILD - LIVE MONITOR            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Check if build is running
    if pgrep -f "make.*buildroot" > /dev/null; then
        echo "🟢 BUILD STATUS: RUNNING"
    else
        echo "🔴 BUILD STATUS: STOPPED (completed or failed)"
    fi
    
    echo ""
    echo "📊 SYSTEM RESOURCES:"
    echo "-----------------------------------------------------------"
    echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
    echo "Memory: $(free -h | awk '/^Mem:/ {printf "%s / %s (%.1f%%)\n", $3, $2, ($3/$2)*100}')"
    echo "Disk Free: $(df -h ~ | tail -1 | awk '{print $4}')"
    
    echo ""
    echo "📝 LATEST BUILD ACTIVITY (last 15 lines):"
    echo "-----------------------------------------------------------"
    if [ -f ~/buildroot/build.log ]; then
        tail -15 ~/buildroot/build.log | sed 's/^/  /'
    else
        echo "  Waiting for build.log..."
    fi
    
    echo ""
    echo "⏱️  Build time: $(ps -o etime= -p $(pgrep -f "make.*buildroot" | head -1) 2>/dev/null || echo "N/A")"
    echo ""
    echo "Press Ctrl+C to exit monitor (build continues in background)"
    
    sleep 5
done
