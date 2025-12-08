# 🚀 First Boot Guide - AI-Powered OS

## Your OS includes these AI features:
- **AI Model Manager**: Download and switch between 16 AI models
- **JARVIS Voice Assistant**: Voice-controlled system commands
- **OS Helper AI**: Lightweight configuration assistant
- **Ollama Runtime**: Local AI model server

---

## Step 1: Boot the OS

### Using QEMU (testing):
```bash
gunzip -k disk.img.gz
qemu-system-x86_64 -drive file=disk.img,format=raw -m 4096 -enable-kvm -cpu host -smp 4
```

### Using USB (real hardware):
```bash
sudo dd if=disk.img.gz of=/dev/sdX bs=4M status=progress conv=fsync
# Replace /dev/sdX with your USB drive
```

**Login credentials:**
- Username: `root`
- Password: (no password, just press Enter)

---

## Step 2: Connect to Internet

```bash
# Check network interface
ip addr

# For DHCP (most common):
dhclient eth0

# For WiFi:
wpa_passphrase "YourSSID" "YourPassword" > /etc/wpa_supplicant.conf
wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant.conf
dhclient wlan0

# Test connection:
ping -c 3 google.com
```

---

## Step 3: Choose Your AI Setup

### Option A: Download a Full AI Model (700MB - 4GB)
```bash
ai-models
# Select option 1-16 from the interactive menu
# Recommended: Option 1 (Dolphin Mistral 7B - uncensored)
```

**Available models:**
1. Dolphin Mistral 7B (4GB) - Uncensored, great for system control
2. WizardLM 7B (4GB) - Instruction following
3. Nous-Hermes2 (4GB) - Helpful and detailed
4. Orca-Mini (1.9GB) - Balanced performance
5. Phi-2 (1.7GB) - Fast, efficient
6. TinyLlama (637MB) - Quick responses

### Option B: Setup Lightweight OS Helper (<1GB)
```bash
setup-os-helper
# Choose option 1-7 for different tiny models
# Recommended: Option 2 (all-MiniLM - only 45MB!)
```

**Quick models:**
1. TinyLlama (637MB) - Small but capable
2. all-MiniLM (45MB) - Ultra-lightweight
3. TinyDolphin (637MB) - Small uncensored
4. Quantized Mistral (950MB) - Compressed quality

---

## Step 4: Test Your AI

### Test AI Model Manager:
```bash
# Check Ollama is running
systemctl status ollama

# Query your AI
ai query "What is the capital of France?"

# Natural language system commands
ai do "show me disk usage"

# Chat mode (interactive)
ai chat
```

### Test OS Helper:
```bash
# Ask configuration questions
os-helper "How do I add a new user?"
os-helper "Configure static IP address"
os-helper "Install a package"
```

---

## Step 5: Enable JARVIS Voice Control

```bash
# Install Python audio dependencies
pip3 install SpeechRecognition pyaudio pyttsx3

# Start JARVIS manually (first time)
jarvis

# Enable auto-start
systemctl enable jarvis
systemctl start jarvis
```

**Voice commands:**
- "Jarvis, update the system"
- "Jarvis, show disk space"
- "Jarvis, list running processes"
- "Jarvis, what is my IP address"
- "Jarvis, create user john"

**Note:** Voice control requires a microphone. In QEMU, use `-device intel-hda -device hda-duplex` for audio passthrough.

---

## Available Commands

### AI Commands:
```bash
ai query "your question"          # Ask AI anything
ai do "natural language command"   # Execute system commands
ai cmd "specific shell command"    # Run exact shell commands
ai chat                           # Interactive chat
ai status                         # Check AI system status

ai-models                         # Download/switch AI models
os-helper "configuration help"    # Quick OS help
jarvis                            # Start voice assistant
```

### System Management:
```bash
systemctl status ollama           # Check AI runtime
systemctl status ai-controller    # Check AI daemon
systemctl status jarvis          # Check voice assistant

journalctl -u ollama -f          # Watch AI logs
tail -f /var/log/ai-control.log  # AI controller logs
```

---

## Troubleshooting

### AI not responding:
```bash
# Restart Ollama
systemctl restart ollama
sleep 10  # Wait for startup

# Restart AI controller
systemctl restart ai-controller

# Check if model is downloaded
ollama list
```

### JARVIS not hearing you:
```bash
# Check audio devices
aplay -l   # List playback devices
arecord -l # List recording devices

# Test microphone
arecord -d 3 test.wav && aplay test.wav

# Reinstall audio packages
pip3 install --force-reinstall pyaudio
```

### No internet connection:
```bash
# Check interfaces
ip link

# Restart network
systemctl restart networking

# Manual DHCP
dhclient eth0
```

### Out of disk space:
```bash
# Check usage
df -h

# The OS has 8GB allocated, with ~3.5GB free for AI models
# To free space, remove unused models:
ollama rm <model-name>
```

---

## Performance Tips

### For 4GB RAM systems:
- Use small models: TinyLlama (637MB) or Phi-2 (1.7GB)
- Run one model at a time
- Disable JARVIS if not using voice: `systemctl stop jarvis`

### For 8GB+ RAM systems:
- Can run Mistral 7B models (4GB)
- Can keep JARVIS running alongside AI
- Can load multiple small models

### For 16GB+ RAM systems:
- Run any model comfortably
- Enable all features simultaneously
- Consider running AI-powered GUI when available

---

## Next Steps

1. **Customize your AI**: Try different models with `ai-models`
2. **Voice control**: Get JARVIS working for hands-free control
3. **GUI (coming soon)**: Desktop environment with Pearl OS style
4. **Share**: Star the repo at https://github.com/mithun789/custom-linux-os-build

---

## Support

- **Documentation**: See repository README.md and guides
- **Issues**: Report bugs on GitHub
- **Community**: Share your AI use cases!

**Repository**: https://github.com/mithun789/custom-linux-os-build

---

## Quick Reference Card

| Feature | Command | Description |
|---------|---------|-------------|
| AI Query | `ai query "question"` | Ask anything |
| AI Command | `ai do "natural command"` | System control |
| Voice Control | `jarvis` | Wake word: "jarvis" |
| Model Manager | `ai-models` | Download models |
| Quick Help | `os-helper "question"` | Config assistance |
| System Status | `ai status` | Check AI health |

**Your AI-powered OS is ready! 🎉**
