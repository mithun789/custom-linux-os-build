# AI-Driven Custom Linux OS Development - Complete Setup Guide

## QUICK COST BREAKDOWN
- **Total Cost: $0** (All free and open-source)
- GitHub Copilot: Free (if student) or $20/month
- Tools: Free (Buildroot, Linux kernel, MCP SDK, VS Code)
- Hardware: You already have it

---

## PHASE 1: MAIN LAPTOP SETUP (Windows)

### Step 1: Install Node.js
```bash
# Download from https://nodejs.org/en/ (LTS version)
# Or use Windows package manager (if on Windows 11+):
winget install OpenJS.NodeJS.LTS
```

**Verify:**
```bash
node --version  # Should be v20.x or higher
npm --version   # Should be v10.x or higher
```

### Step 2: Install GitHub Copilot CLI
```bash
npm install -g @github/copilot
```

**Login to GitHub:**
```bash
copilot auth login
# Opens browser for GitHub authentication
```

**Verify:**
```bash
copilot --version
copilot /help
```

### Step 3: Install VS Code Extensions
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search and install:
   - `Remote - SSH` (Microsoft)
   - `GitHub Copilot` (GitHub)
   - `GitHub Copilot Chat` (GitHub)

### Step 4: Generate SSH Keys
```bash
# On Windows PowerShell (run as Admin):
ssh-keygen -t rsa -b 4096 -f "$env:USERPROFILE\.ssh\id_rsa" -N ""

# Verify:
Get-Content $env:USERPROFILE\.ssh\id_rsa.pub
```

### Step 5: Configure SSH Config
Create file: `C:\Users\{YourUsername}\.ssh\config`

```
Host buildhost
    User ubuntu
    HostName 192.168.1.100
    IdentityFile ~/.ssh/id_rsa
    LocalForward 127.0.0.1:3000 127.0.0.1:3000
    LocalForward 127.0.0.1:3001 127.0.0.1:3001
    LocalForward 127.0.0.1:3002 127.0.0.1:3002
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

Replace `192.168.1.100` with your old laptop's IP address.

**Test Connection:**
```bash
ssh buildhost "echo 'Connection successful'"
```

---

## PHASE 2: OLD LAPTOP SETUP (Linux - Debian 13 GUI)

### Prerequisites:
- Debian 13 with GUI installed (from previous steps)
- Internet connection
- Access via SSH

### Step 1: Update System
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl wget build-essential python3 python3-pip nodejs npm
```

### Step 2: Add SSH Public Key from Main Laptop
On old laptop:
```bash
mkdir -p ~/.ssh
nano ~/.ssh/authorized_keys
# Paste your Windows machine's public key (from Step 4 above)
# Ctrl+O, Enter, Ctrl+X to save

chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

sudo systemctl restart ssh
```

**Test from main laptop:**
```bash
ssh buildhost "whoami"  # Should show: ubuntu
```

### Step 3: Install Buildroot
```bash
cd ~
git clone https://git.buildroot.net/buildroot
cd buildroot

# Show available versions
git branch -a | grep "20" | tail -10
# Pick latest, e.g., 2024.08.x

git checkout 2024.08  # Use latest stable

# Verify installation
make help | head -20
```

### Step 4: Install MCP SDK (Python)
```bash
pip install mcp
pip install fastmcp
```

**Verify:**
```bash
python3 -c "import mcp; print('MCP installed successfully')"
```

### Step 5: Create MCP Servers Directory
```bash
mkdir -p ~/mcp-servers
cd ~/mcp-servers
```

---

## PHASE 3: DEVELOP MCP SERVERS (Old Laptop)

### MCP Server 1: Buildroot Configuration

Create: `~/mcp-servers/buildroot_mcp.py`

```python
#!/usr/bin/env python3
import subprocess
import os
import json
from fastmcp import FastMCP

mcp = FastMCP("buildroot-server")

@mcp.tool()
async def configure_buildroot(config_options: dict) -> str:
    """Configure Buildroot with custom options.
    
    Args:
        config_options: dict with keys like:
        - BR2_ARCH: arm, x86_64, aarch64
        - BR2_PACKAGE_OPENSSH: y/n
        - BR2_PACKAGE_BUSYBOX: y/n
    """
    buildroot_path = os.path.expanduser("~/buildroot")
    config_path = os.path.join(buildroot_path, ".config")
    
    try:
        # Create minimal .config
        with open(config_path, 'w') as f:
            f.write("BR2_DEFCONFIG=\"arch/configs/defconfig\"\n")
            for key, value in config_options.items():
                if value == "y" or value == "n":
                    f.write(f"{key}={value}\n")
                else:
                    f.write(f"{key}=\"{value}\"\n")
        
        # Validate configuration
        os.chdir(buildroot_path)
        result = subprocess.run(
            ["make", "oldconfig"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        return f"Configuration saved. Output:\n{result.stdout}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def get_buildroot_status() -> str:
    """Get current Buildroot configuration status."""
    buildroot_path = os.path.expanduser("~/buildroot")
    config_path = os.path.join(buildroot_path, ".config")
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = f.read()
        return f"Current config:\n{config[:500]}..."  # First 500 chars
    return "No .config found"

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
```

### MCP Server 2: Build Execution

Create: `~/mcp-servers/build_mcp.py`

```python
#!/usr/bin/env python3
import subprocess
import os
import time
from fastmcp import FastMCP

mcp = FastMCP("build-server")

@mcp.tool()
async def execute_build(target: str = "all", jobs: int = 4) -> dict:
    """Execute Buildroot build process.
    
    Args:
        target: 'all', 'kernel', 'rootfs', 'clean'
        jobs: number of parallel jobs
    """
    buildroot_path = os.path.expanduser("~/buildroot")
    os.chdir(buildroot_path)
    
    try:
        cmd = ["make", target, f"-j{jobs}"]
        print(f"Starting build: {' '.join(cmd)}")
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        elapsed = time.time() - start_time
        
        return {
            "success": result.returncode == 0,
            "target": target,
            "duration_seconds": elapsed,
            "output": result.stdout[-1000:],  # Last 1000 chars
            "errors": result.stderr[-500:] if result.stderr else "None"
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Build timeout (>1 hour)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def list_build_artifacts() -> dict:
    """List generated OS artifacts."""
    artifacts_path = os.path.expanduser("~/buildroot/output/images")
    
    try:
        if os.path.exists(artifacts_path):
            files = os.listdir(artifacts_path)
            details = {}
            for f in files:
                fpath = os.path.join(artifacts_path, f)
                size_mb = os.path.getsize(fpath) / (1024*1024)
                details[f] = f"{size_mb:.2f} MB"
            return {"artifacts": details}
        return {"artifacts": {}, "error": "Output directory not found"}
    except Exception as e:
        return {"error": str(e)}

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
```

### MCP Server 3: Testing & Validation

Create: `~/mcp-servers/testing_mcp.py`

```python
#!/usr/bin/env python3
import subprocess
import os
from fastmcp import FastMCP

mcp = FastMCP("testing-server")

@mcp.tool()
async def validate_build() -> dict:
    """Validate build artifacts."""
    artifacts = os.path.expanduser("~/buildroot/output/images")
    
    try:
        results = {}
        
        # Check kernel
        kernel = os.path.join(artifacts, "zImage")
        if os.path.exists(kernel):
            size = os.path.getsize(kernel) / (1024*1024)
            results["kernel"] = f"✓ Found ({size:.2f} MB)"
        else:
            results["kernel"] = "✗ Not found"
        
        # Check rootfs
        rootfs = os.path.join(artifacts, "rootfs.ext4")
        if os.path.exists(rootfs):
            size = os.path.getsize(rootfs) / (1024*1024)
            results["rootfs"] = f"✓ Found ({size:.2f} MB)"
        else:
            results["rootfs"] = "✗ Not found"
        
        return results
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def run_checksums() -> str:
    """Generate checksums of artifacts."""
    artifacts = os.path.expanduser("~/buildroot/output/images")
    os.chdir(artifacts)
    
    try:
        result = subprocess.run(
            ["sha256sum", "*"],
            capture_output=True,
            text=True,
            shell=True
        )
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
```

### Make MCP Servers Executable

```bash
chmod +x ~/mcp-servers/*.py
```

### Test MCP Servers Locally (on old laptop)

```bash
# Test in separate terminals:

# Terminal 1:
python3 ~/mcp-servers/buildroot_mcp.py

# Terminal 2:
python3 ~/mcp-servers/build_mcp.py

# Terminal 3:
python3 ~/mcp-servers/testing_mcp.py
```

---

## PHASE 4: CONFIGURE COPILOT ON MAIN LAPTOP

### Step 1: Create Copilot Configuration

File: `~/.claude/claude_desktop_config.json` (Windows: `%APPDATA%\Claude\claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "buildroot-remote": {
      "command": "ssh",
      "args": [
        "buildhost",
        "python3 ~/mcp-servers/buildroot_mcp.py"
      ]
    },
    "build-remote": {
      "command": "ssh",
      "args": [
        "buildhost",
        "python3 ~/mcp-servers/build_mcp.py"
      ]
    },
    "testing-remote": {
      "command": "ssh",
      "args": [
        "buildhost",
        "python3 ~/mcp-servers/testing_mcp.py"
      ]
    }
  }
}
```

### Step 2: Test MCP Connection from Main Laptop

```bash
# Open VS Code and open Claude panel (Ctrl+Shift+L if using Copilot Chat)
# Or use Copilot CLI:
copilot /tools
# Should list all 3 MCP servers
```

---

## PHASE 5: CREATE WORKFLOW SPECIFICATION FILES

### On old laptop, create: `~/os-build/.spec.md`

```markdown
# Custom AI-Powered Linux OS Specification

## Target Hardware
- Processor: i5-9300H (x86_64)
- RAM: 16GB
- GPU: NVIDIA GTX 1650
- Storage: 256GB SSD + 1TB HDD

## OS Requirements
- Base: Debian 13 minimal
- GUI: GNOME Desktop
- Development: Python, Node.js, Docker
- AI: Ollama + Mistral 8B
- Connectivity: SSH, WiFi, Samba

## Build Configuration
- Architecture: x86_64
- Kernel: Linux 6.6 LTS
- Init: systemd
- Filesystem: ext4

## Key Packages
- busybox
- systemd
- openssh-server
- docker
- python3
- nodejs

## Build Strategy
1. Configure Buildroot
2. Compile kernel (parallel jobs: 8)
3. Build rootfs
4. Generate final ISO
5. Validate artifacts
```

### Create: `~/os-build/.instructions.md`

```markdown
---
applyTo: "**/*.py"
---

# OS Build Instructions

## Build Optimization
- Use -j$(nproc) for parallel make
- Enable ccache for faster rebuilds
- Strip debug symbols in production

## Error Handling
- Log all output to ~/build.log
- Parse errors and suggest fixes
- Retry on transient failures

## Validation Checklist
- ✓ All artifacts present
- ✓ Kernel size < 50MB
- ✓ Rootfs size < 1GB
- ✓ All packages included
- ✓ Checksums verified
```

### Create: `~/os-build/.prompt.md`

```markdown
---
mode: agent
model: claude-4
tools: ['buildroot-remote', 'build-remote', 'testing-remote']
---

# AI-Powered OS Build Workflow

## Phase 1: Configuration (5 minutes)
1. Load specification from .spec.md
2. Configure Buildroot with custom options
3. Validate configuration

## Phase 2: Build (2-8 hours)
1. Execute build: make all -j8
2. Monitor output, capture logs
3. Validate all artifacts generated

## Phase 3: Testing (30 minutes)
🚨 **STOP**: Request human approval
- Show artifact sizes
- Verify checksums
- Confirm all packages included

## Phase 4: Deployment
1. If approved, commit to git
2. Tag release
3. Create GitHub release
```

---

## PHASE 6: EXECUTE AUTONOMOUS BUILD

### Step 1: From Main Laptop, Start Copilot

```bash
copilot
```

### Step 2: Give Build Command to Copilot

```
> Build custom Linux OS with:
> - GUI (GNOME)
> - SSH server
> - Python 3 + Node.js
> - Docker support
> - GPU drivers (NVIDIA)
> Follow the .prompt.md workflow in ~/os-build/
```

### Step 3: Monitor Build Progress

In another terminal on main laptop:
```bash
ssh buildhost "tail -f ~/buildroot/build.log"
```

### Step 4: Approve Critical Gates

When Copilot pauses for approval:
```
Copilot: "Build phase complete. Artifacts:"
Copilot: "- zImage: 45MB"
Copilot: "- rootfs.ext4: 850MB"
Copilot: "Proceed with deployment?"

You: "Yes, deploy"
```

---

## COST BREAKDOWN

| Item | Cost | Notes |
|------|------|-------|
| GitHub Copilot | $0-20/month | Free if student, $20/month otherwise |
| VS Code | $0 | Free |
| Linux | $0 | Free (Debian, Buildroot) |
| Node.js | $0 | Free |
| Python | $0 | Free |
| SSH (OpenSSH) | $0 | Free |
| MCP SDK | $0 | Free (Apache 2.0 license) |
| **TOTAL** | **$0-20/month** | All open source except Copilot |

---

## QUICK REFERENCE: ALL COMMANDS

### Main Laptop (Windows PowerShell):
```powershell
# Install tools
winget install OpenJS.NodeJS.LTS
npm install -g @github/copilot
copilot auth login

# Generate SSH keys
ssh-keygen -t rsa -b 4096 -f "$env:USERPROFILE\.ssh\id_rsa" -N ""

# Connect to old laptop
ssh buildhost
ssh buildhost "tail -f ~/buildroot/build.log"

# Start Copilot
copilot
```

### Old Laptop (Linux Terminal):
```bash
# Update system
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl wget build-essential python3 python3-pip nodejs npm

# Install Buildroot
cd ~ && git clone https://git.buildroot.net/buildroot && cd buildroot
git checkout 2024.08

# Install MCP
pip install mcp fastmcp

# Create servers directory
mkdir -p ~/mcp-servers
cd ~/mcp-servers

# Make executable
chmod +x *.py

# Test server
python3 buildroot_mcp.py
```

---

## NEXT STEPS

1. Follow PHASE 1-2 for basic setup
2. Implement PHASE 3 MCP servers
3. Configure PHASE 4 on main laptop
4. Create workflow files PHASE 5
5. Execute build PHASE 6

**Estimated time: 6-8 hours total**
**Estimated build time: 4-8 hours (first run)**
**Subsequent builds: 1-2 hours (with ccache)**

