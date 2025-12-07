# TROUBLESHOOTING GUIDE

## SSH Connection Issues

### Problem: "Connection refused" or "Connection timed out"

**Diagnosis:**
```bash
# Check if old laptop is reachable
ping 192.168.1.100

# Check SSH service status
ssh buildhost "sudo systemctl status ssh"
```

**Solutions:**

1. **SSH service not running:**
```bash
# On old laptop
sudo systemctl start ssh
sudo systemctl enable ssh
```

2. **Firewall blocking SSH:**
```bash
# On old laptop
sudo ufw allow ssh
sudo ufw allow 22/tcp
sudo ufw reload
```

3. **Wrong IP address:**
```bash
# Find correct IP on old laptop
hostname -I
ip addr show | grep "inet"
# Update SSH config with correct IP
```

4. **SSH key permissions wrong:**
```bash
# On main laptop
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

---

## MCP Server Issues

### Problem: "MCP server not found" or "ImportError: No module named 'fastmcp'"

**Solution:**
```bash
# On old laptop, install MCP SDK
pip install mcp fastmcp --upgrade

# Verify installation
python3 -c "import fastmcp; print('OK')"
```

### Problem: MCP server starts but Copilot can't access it

**Diagnosis:**
```bash
# Test server locally on old laptop
python3 ~/mcp-servers/buildroot_mcp.py

# In another terminal, check if it's listening
netstat -tlnp | grep python

# Test from main laptop
ssh buildhost "python3 ~/mcp-servers/buildroot_mcp.py"
```

**Solution: Check SSH config has correct port forwarding:**
```
LocalForward 127.0.0.1:3000 127.0.0.1:3000
LocalForward 127.0.0.1:3001 127.0.0.1:3001
LocalForward 127.0.0.1:3002 127.0.0.1:3002
```

### Problem: Port already in use

**Check what's using the port:**
```bash
# On main laptop
netstat -tlnp | grep 3000
# or
lsof -i :3000
```

**Solution:**
```bash
# Kill process using the port
fuser -k 3000/tcp

# Or use different port in SSH config
LocalForward 127.0.0.1:3010 127.0.0.1:3000
```

---

## Buildroot Issues

### Problem: "make: command not found"

**Solution:**
```bash
# Install build tools
sudo apt install -y build-essential make gcc

# Verify
make --version
```

### Problem: Buildroot clone very slow

**Solution: Use shallow clone**
```bash
git clone --depth=1 https://git.buildroot.net/buildroot ~/buildroot
cd ~/buildroot

# Then fetch full history if needed
git fetch --unshallow
```

### Problem: "missing tool: xxxx"

**Common missing tools:**
```bash
# Install all required tools
sudo apt install -y \
  build-essential \
  git \
  python3 \
  python3-dev \
  rsync \
  libncurses5-dev \
  bzr \
  cvs \
  mercurial \
  subversion \
  wget \
  curl
```

### Problem: Build fails with "No space left on device"

**Solution:**
```bash
# Check disk space
df -h

# Clean previous builds
cd ~/buildroot
make clean
make distclean  # More aggressive

# If still full, use HDD instead of SSD
cd /mnt/storage
git clone https://git.buildroot.net/buildroot buildroot_large
```

---

## Copilot CLI Issues

### Problem: "copilot: command not found"

**Solution:**
```bash
# Verify installation
npm list -g @github/copilot

# If missing, reinstall
npm install -g @github/copilot --force

# Check npm path
npm config get prefix
```

### Problem: "Not authenticated with GitHub"

**Solution:**
```bash
# Login to GitHub
copilot auth login

# Verify token
copilot auth status
```

### Problem: "Tool not found" when running copilot commands

**Solution:**
```bash
# List available tools
copilot /tools

# Test tool connection
copilot -p "List files in current directory"
```

---

## Build Performance Issues

### Problem: Build very slow

**Check hardware usage:**
```bash
# On old laptop, while building
htop

# Check CPU usage
top -b -n 1 | head -15

# Check disk I/O
iostat -x 1 5
```

**Solutions:**

1. **Reduce parallel jobs (if CPU throttling):**
```bash
cd ~/buildroot
make all -j2  # Instead of -j8
```

2. **Use faster disk:**
```bash
# Move build to SSD if on HDD
mv ~/buildroot /tmp/buildroot_ssd
```

3. **Enable ccache for faster rebuilds:**
```bash
# On old laptop
sudo apt install ccache

# In Buildroot
cd ~/buildroot
make menuconfig
# Search for: BR2_CCACHE
# Enable: BR2_CCACHE=y
```

4. **Check network speed:**
```bash
# Test SSH throughput
ssh buildhost "dd if=/dev/zero bs=1M count=100" | dd of=/dev/null

# Should be >50MB/s on gigabit Ethernet
```

---

## Network Issues

### Problem: SSH disconnects during build

**Solution: Configure keep-alive**
```bash
# Edit ~/.ssh/config
Host buildhost
    ServerAliveInterval 60
    ServerAliveCountMax 10
    TCPKeepAlive yes
```

### Problem: Slow network connection to old laptop

**Diagnosis:**
```bash
# Test latency
ping -c 5 buildhost

# Test bandwidth
ssh buildhost "dd if=/dev/zero bs=1M count=100" | dd of=/dev/null
```

**Solutions:**
1. Use Ethernet instead of WiFi
2. Move router closer to old laptop
3. Check WiFi interference
4. Use 5GHz band instead of 2.4GHz

---

## Linux System Issues

### Problem: "sudo: command not found"

**Solution:**
```bash
# Check if user is in sudoers
groups

# If not in sudo group, add as root (requires reboot)
su - root
usermod -aG sudo ubuntu
exit
```

### Problem: apt/apt-get "cannot acquire lock"

**Solution:**
```bash
# Wait for other apt processes
ps aux | grep apt

# If stuck, kill them
sudo killall apt apt-get

# Then try again
sudo apt update
```

### Problem: Python 3 not found

**Solution:**
```bash
# Install Python
sudo apt install -y python3 python3-pip

# Create symlink if needed
sudo ln -s /usr/bin/python3 /usr/bin/python

# Verify
python3 --version
```

---

## GitHub/Git Issues

### Problem: Git credentials not working

**Solution:**
```bash
# Configure Git
git config --global user.email "your@email.com"
git config --global user.name "Your Name"

# Setup credential cache
git config --global credential.helper store

# Try clone again
git clone https://github.com/user/repo.git
```

### Problem: SSH key not added to GitHub

**Solution:**
```bash
# On main laptop, get public key
cat ~/.ssh/id_rsa.pub

# Go to https://github.com/settings/keys
# Click "New SSH key"
# Paste the key content
# Test connection
ssh -T git@github.com
```

---

## Docker Issues (if using Docker in OS build)

### Problem: "Docker daemon not running"

**Solution:**
```bash
sudo systemctl start docker
sudo systemctl enable docker

# Verify
docker ps
```

### Problem: "Permission denied while trying to connect to Docker daemon"

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker

# Or logout and login again
```

---

## Performance Optimization

### Enable Parallel Building
```bash
# On old laptop, edit Buildroot config
cd ~/buildroot
make menuconfig

# Search for: BR2_JLEVEL
# Set to: 8 (for 8-core processing)
# Or auto: $(nproc)
```

### Enable Incremental Builds
```bash
# First build: full
make all

# Subsequent builds (after changes): incremental
make

# Clean everything
make distclean
```

### Monitor Build Progress
```bash
# Watch build in real-time
ssh buildhost "tail -f ~/buildroot/build.log" | grep -i "^\["

# Or
ssh buildhost "watch -n 5 'tail -5 ~/buildroot/build.log'"
```

---

## Getting Help

If issue not resolved:

1. **Check Buildroot wiki:**
   ```
   https://buildroot.org/
   https://wiki.buildroot.org/
   ```

2. **Check MCP documentation:**
   ```
   https://modelcontextprotocol.io/
   ```

3. **Check GitHub Copilot docs:**
   ```
   https://github.com/features/copilot
   ```

4. **Get system logs:**
   ```bash
   # Save detailed logs for debugging
   ssh buildhost "journalctl -xe | head -100" > debug_logs.txt
   
   # Buildroot logs
   ssh buildhost "tail -100 ~/buildroot/build.log" > buildroot_logs.txt
   ```

5. **Ask Copilot for help:**
   ```bash
   copilot -p "Why is my build failing with: [error message here]"
   ```

