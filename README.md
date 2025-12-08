# 🤖 AI-Powered Custom Linux OS

A lightweight, AI-powered Linux operating system built from scratch using Buildroot. Features uncensored AI models, voice control (JARVIS), and flexible AI model management.

## 🎯 Quick Start

**[Download Latest Release](https://github.com/mithun789/custom-linux-os-build/releases)** → Boot → Connect Internet → Download AI Model → Start Using!

## ✨ Features

- **🧠 AI Model Manager**: Choose from 16 AI models (45MB - 4GB)
- **🎙️ JARVIS Voice Assistant**: Voice-controlled system operations
- **💡 OS Helper AI**: Lightweight configuration assistant (<1GB)
- **🔓 Uncensored AI**: Dolphin Mistral and other unrestricted models
- **⚡ Lightweight**: 52MB compressed, 425MB actual data
- **🐧 Pure Linux**: Built from scratch with Buildroot

## 📦 Download & Install

### Option 1: QEMU (Testing)
```bash
# Download from releases
wget https://github.com/mithun789/custom-linux-os-build/releases/download/latest/disk.img.gz
gunzip disk.img.gz

# Run in VM
qemu-system-x86_64 -drive file=disk.img,format=raw -m 4096 -enable-kvm -cpu host -smp 4
```

### Option 2: USB Install (Physical Hardware)
```bash
# Download and write to USB
wget https://github.com/mithun789/custom-linux-os-build/releases/download/latest/disk.img.gz
gunzip disk.img.gz
sudo dd if=disk.img of=/dev/sdX bs=4M status=progress conv=fsync
# Replace /dev/sdX with your USB drive
```

**Login**: Username `root`, no password (press Enter)

## 📚 Documentation

Follow these guides in order to get started:

1. **[Quick Start](docs/01_QUICK_START.md)** - Get up and running in 5 minutes
2. **[First Boot Guide](docs/02_FIRST_BOOT_GUIDE.md)** - What to do after booting
3. **[AI Model Manager](docs/03_AI_MODEL_MANAGER.md)** - Download and manage AI models
4. **[AI Integration Details](docs/04_AI_INTEGRATION_DETAILS.md)** - How AI is integrated
5. **[JARVIS Voice Control](docs/05_JARVIS_VOICE_CONTROL.md)** - Setup voice assistant
6. **[OS Helper AI](docs/06_OS_HELPER_AI.md)** - Lightweight AI for quick help
7. **[Troubleshooting](docs/07_TROUBLESHOOTING.md)** - Common issues and fixes

**Reference Docs:**
- [Cost Analysis](docs/08_COST_ANALYSIS.md)
- [Complete Setup Reference](docs/09_COMPLETE_SETUP_REFERENCE.md)
- [Setup Complete](docs/10_SETUP_COMPLETE.md)

## 🚀 Quick Commands

After booting and connecting to internet:

```bash
# Download an AI model
ai-models                          # Interactive model selection

# Ask your AI anything
ai query "What is the capital of France?"

# Execute system commands naturally
ai do "show me disk usage"

# Setup lightweight helper (<1GB)
setup-os-helper                    # Choose from 7 tiny models

# Ask quick questions
os-helper "How do I add a new user?"

# Enable voice control
jarvis                             # Start voice assistant
# Say: "Jarvis, update the system"
```

## 🎯 Available AI Models

### Full Models (via ai-models):
- **Dolphin Mistral 7B** (4GB) - Uncensored, system control
- **WizardLM 7B** (4GB) - Instruction following
- **Nous-Hermes2** (4GB) - Helpful and detailed
- **Orca-Mini** (1.9GB) - Balanced performance
- **Phi-2** (1.7GB) - Fast, efficient
- **TinyLlama** (637MB) - Quick responses
- ...and 10 more options

### Lightweight Models (via setup-os-helper):
- **all-MiniLM** (45MB) - Ultra-lightweight
- **TinyLlama** (637MB) - Small but capable
- **TinyDolphin** (637MB) - Small uncensored
- **Quantized Mistral** (950MB) - Compressed quality

## 🛠️ System Requirements

**Minimum:**
- 2GB RAM (for tiny models)
- 4GB disk space
- x86_64 CPU
- Internet connection

**Recommended:**
- 8GB RAM (for 7B models)
- 16GB disk space
- Multi-core CPU
- Microphone (for JARVIS)

## 🏗️ Build from Source

```bash
# Clone repository
git clone https://github.com/mithun789/custom-linux-os-build.git
cd custom-linux-os-build

# Run MCP server for automated build
python3 -m venv mcp-venv
source mcp-venv/bin/activate
pip install fastmcp
python build_mcp.py

# Or build manually with Buildroot
cd ~/buildroot
make menuconfig
make -j$(nproc)
```

See [Complete Setup Reference](docs/09_COMPLETE_SETUP_REFERENCE.md) for detailed build instructions.

## 📋 What's Inside

- **Base System**: Buildroot 2024.11.x
- **Kernel**: Linux 6.1.x LTS
- **AI Runtime**: Ollama
- **Audio**: ALSA + espeak
- **Python**: 3.13.5 with AI libraries
- **Speech**: SpeechRecognition + PyAudio
- **Custom Tools**: ai, ai-models, jarvis, os-helper

## 🎤 JARVIS Voice Commands

Once JARVIS is running, use these voice commands:

- "Jarvis, update the system"
- "Jarvis, show disk space"
- "Jarvis, list running processes"
- "Jarvis, what is my IP address"
- "Jarvis, create user john"
- "Jarvis, install package curl"

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- GUI Desktop Environment (KDE/LXQT)
- More AI model integrations
- Additional voice commands
- Performance optimizations
- Documentation improvements

## 📝 License

This project is open source. Built with open source tools.

## 🙏 Credits

- **Buildroot** - Linux build system
- **Ollama** - Local AI runtime
- **Dolphin Models** - Uncensored AI
- **OpenAI Whisper** - Speech recognition
- **espeak** - Text-to-speech

## 📊 Project Stats

- **Build Time**: 2-4 hours (first build), 2 minutes (incremental)
- **OS Size**: 52MB compressed, 8.1GB uncompressed
- **Actual Data**: 425MB (rest is free space for AI models)
- **Boot Time**: ~10 seconds
- **First Release**: December 2025

## 🔗 Links

- **Repository**: https://github.com/mithun789/custom-linux-os-build
- **Releases**: https://github.com/mithun789/custom-linux-os-build/releases
- **Issues**: https://github.com/mithun789/custom-linux-os-build/issues

---

**Made with ❤️ by [mithun789](https://github.com/mithun789)**

*Star ⭐ this repo if you find it useful!*
