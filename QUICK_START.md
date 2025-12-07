# QUICK START GUIDE: AI-Driven OS Development

## 15-MINUTE CHECKLIST

### Main Laptop (Windows)
- [ ] Install Node.js: `winget install OpenJS.NodeJS.LTS`
- [ ] Install Copilot CLI: `npm install -g @github/copilot`
- [ ] Generate SSH keys: `ssh-keygen -t rsa -b 4096 -f "$env:USERPROFILE\.ssh\id_rsa" -N ""`
- [ ] Copy SSH config template to `~/.ssh/config`
- [ ] Update IP address in SSH config (find it from old laptop)
- [ ] Test SSH: `ssh buildhost "echo OK"`

### Old Laptop (Linux)
- [ ] Update system: `sudo apt update && sudo apt upgrade -y`
- [ ] Install tools: `sudo apt install -y git python3 python3-pip nodejs npm`
- [ ] Install Buildroot: `git clone https://git.buildroot.net/buildroot ~/buildroot`
- [ ] Install MCP: `pip install mcp fastmcp`
- [ ] Create MCP dir: `mkdir -p ~/mcp-servers`
- [ ] Copy 3 MCP server files to ~/mcp-servers/
- [ ] Make executable: `chmod +x ~/mcp-servers/*.py`
- [ ] Add SSH public key: Edit ~/.ssh/authorized_keys with main laptop's key

### Both Machines
- [ ] Test MCP servers: `python3 ~/mcp-servers/buildroot_mcp.py`
- [ ] Test from main laptop: `ssh buildhost "python3 ~/mcp-servers/buildroot_mcp.py"`

---

## FIND YOUR OLD LAPTOP'S IP ADDRESS

### On Old Laptop (Linux Terminal):
```bash
# Method 1: Simple
hostname -I

# Method 2: Detailed
ip addr show | grep "inet " | grep -v 127.0.0.1

# Method 3: Check WiFi
ip addr show wlan0 | grep "inet "
```

**Example output:**
```
192.168.1.100
```

Then update SSH config with this IP.

---

## COST SUMMARY

| Service | Cost | Status |
|---------|------|--------|
| GitHub Copilot | $20/month | Only paid software |
| GitHub Copilot Student | FREE | Free for students |
| All other tools | $0 | 100% open source |

**Total: $0 (or $20/month if not student)**

---

## COMMON ISSUES & FIXES

### SSH Connection Refused
```bash
# Check if SSH is running on old laptop:
sudo systemctl status ssh

# Start if stopped:
sudo systemctl start ssh
```

### MCP Server Not Found
```bash
# Check if MCP is installed:
python3 -c "import mcp; print('OK')"

# If missing:
pip install mcp fastmcp
```

### Buildroot Clone Too Slow
```bash
# Use shallow clone instead:
git clone --depth=1 https://git.buildroot.net/buildroot ~/buildroot
```

### Port Already in Use
```bash
# If SSH forwarding fails, ports might be busy:
# Try different ports in SSH config:
LocalForward 127.0.0.1:3010 127.0.0.1:3000
```

---

## STEP-BY-STEP EXECUTION

### Day 1: Setup (4 hours)
1. Run checklist above on both machines
2. Test SSH connection
3. Test MCP servers locally
4. Copy Claude config file

### Day 2: First Build (8 hours)
1. Open Copilot on main laptop: `copilot`
2. Give command: "Build Linux OS with SSH, Python, Docker"
3. Monitor: `ssh buildhost "tail -f ~/buildroot/build.log"`
4. Approve when prompted
5. Review artifacts: `ssh buildhost "ls -lh ~/buildroot/output/images/"`

### Day 3+: Refinement
1. Adjust OS configuration in Buildroot
2. Re-run build (faster with ccache)
3. Test on actual hardware or QEMU

---

## USEFUL COMMANDS

```bash
# SSH to old laptop
ssh buildhost

# Run command on old laptop
ssh buildhost "uname -a"

# Transfer file from old laptop
scp buildhost:~/buildroot/output/images/zImage .

# View Buildroot logs
ssh buildhost "tail -100 ~/buildroot/build.log"

# Check build progress
ssh buildhost "ps aux | grep make"

# Get old laptop status
ssh buildhost "top -b -n 1 | head -20"
```

---

## NEXT: DETAILED SETUP GUIDE

See `01_COMPLETE_SETUP_GUIDE.md` for full instructions with all commands.

