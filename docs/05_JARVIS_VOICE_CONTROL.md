# JARVIS Voice Assistant - User Guide 🎤🤖

## Overview
JARVIS is a voice-controlled AI assistant that lets you control your entire OS using voice commands. Say "Jarvis" to wake it up, then give any command!

## Features

### 🎙️ Voice Control
- **Wake word activation**: Say "Jarvis" to activate
- **Natural language**: Speak naturally, no rigid commands
- **Voice feedback**: JARVIS speaks responses back to you
- **Continuous listening**: Always ready to help

### 🖥️ System Control
- Update system
- Shutdown/reboot
- Check system status
- Monitor resources
- Manage services

### 👤 User Management
- Login/logout users
- Create new users
- Switch users
- Manage permissions

### 📁 File Operations
- Create files and directories
- Delete files
- List files
- Find/search files
- Open files

### 🤖 AI Integration
- Ask questions
- Get explanations
- Analyze data
- Get help with commands

## Installation

JARVIS is pre-installed in your OS! After boot:

### First Time Setup:
```bash
# Setup dependencies (one-time)
jarvis setup

# Start JARVIS
systemctl start jarvis

# Enable auto-start
systemctl enable jarvis
```

## Usage

### Voice Commands

**Wake up JARVIS:**
```
"Jarvis" → Wait for response
```

**System commands:**
```
"Jarvis, update the system"
"Jarvis, shutdown"
"Jarvis, reboot"
"Jarvis, system status"
"Jarvis, check disk space"
```

**User management:**
```
"Jarvis, login me"
"Jarvis, create user john"
"Jarvis, switch to user john"
```

**File operations:**
```
"Jarvis, create file test.txt"
"Jarvis, delete file old.txt"
"Jarvis, list files"
"Jarvis, find file config"
"Jarvis, search for python files"
```

**AI queries:**
```
"Jarvis, what is Linux?"
"Jarvis, explain quantum computing"
"Jarvis, how do I install nginx?"
"Jarvis, write a Python hello world"
```

**Network commands:**
```
"Jarvis, show network status"
"Jarvis, check internet connection"
"Jarvis, what's my IP address?"
```

**Package management:**
```
"Jarvis, install firefox"
"Jarvis, update packages"
"Jarvis, search for vim"
```

### Manual Mode (Testing)

Test commands without voice:
```bash
# Test a command
jarvis test "create file test.txt"
jarvis test "system status"
jarvis test "what is docker?"

# Check if setup is complete
jarvis setup
```

### Configuration

Edit `/etc/jarvis/config.json`:
```json
{
  "wake_word": "jarvis",
  "voice_enabled": true,
  "continuous_mode": false,
  "language": "en-US",
  "ollama_model": "dolphin-mistral",
  "voice_feedback": true
}
```

**Options:**
- `wake_word`: Change activation word (default: "jarvis")
- `voice_enabled`: Enable/disable voice input
- `continuous_mode`: Always listen (no wake word needed)
- `language`: Speech recognition language
- `ollama_model`: AI model to use
- `voice_feedback`: Enable/disable voice responses

## Examples

### Complete Workflow:
```
You: "Jarvis"
JARVIS: "Yes, how can I help?"

You: "Create a new file called notes.txt"
JARVIS: "Creating file notes.txt"
JARVIS: "File notes.txt created"

You: "Jarvis"
JARVIS: "Yes, how can I help?"

You: "List all files"
JARVIS: "Listing files"
JARVIS: "Found 5 items in current directory"

You: "Jarvis"
JARVIS: "Yes, how can I help?"

You: "What is Docker?"
JARVIS: "Let me think about that"
JARVIS: "Docker is a platform for developing, shipping, and running applications in containers..."
```

### System Administration:
```
"Jarvis, update the system"
→ Runs: apt-get update && apt-get upgrade

"Jarvis, system status"
→ Shows: uptime, disk usage, memory

"Jarvis, shutdown"
→ Powers off the system
```

### Development Tasks:
```
"Jarvis, create file app.py"
→ Creates: touch app.py

"Jarvis, find all Python files"
→ Runs: find . -name "*.py"

"Jarvis, what is a REST API?"
→ AI explains REST APIs
```

## Advanced Features

### Custom Commands

Add custom commands in `/etc/jarvis/commands/`:

```bash
# /etc/jarvis/commands/backup.sh
#!/bin/bash
tar -czf /backup/system-$(date +%Y%m%d).tar.gz /home
```

Use with: `"Jarvis, run backup"`

### Integration with AI Models

JARVIS automatically uses your installed AI model:
```bash
# Switch to faster model
ai-models download dolphin-phi
# Update JARVIS config to use it
```

### Multiple Languages

Change language in config:
```json
"language": "es-ES"  # Spanish
"language": "fr-FR"  # French
"language": "de-DE"  # German
```

## Troubleshooting

### No microphone detected:
```bash
# List audio devices
arecord -l

# Test recording
arecord -d 5 test.wav
aplay test.wav

# Check ALSA configuration
alsamixer
```

### JARVIS not responding:
```bash
# Check service status
systemctl status jarvis

# View logs
journalctl -u jarvis -f

# Restart
systemctl restart jarvis
```

### Voice recognition errors:
```bash
# Test internet connection (Google Speech API)
ping -c 3 google.com

# Test manually
jarvis test "hello"
```

### Audio issues:
```bash
# Install audio drivers
modprobe snd-hda-intel

# Set default audio device
export AUDIODEV=hw:0,0

# Test speaker
speaker-test -c 2
```

## Requirements

### Hardware:
- **Microphone**: USB or built-in mic
- **Speakers**: For voice feedback
- **Internet**: For speech recognition (Google API)
- **RAM**: 2GB minimum (more if using 7B AI models)

### Software (auto-installed):
- Python 3 with pip
- SpeechRecognition library
- PyAudio for mic input
- pyttsx3 for text-to-speech
- ALSA audio drivers
- Ollama + AI model

## Privacy & Security

### Data Flow:
1. **Wake word detection**: Local (no internet)
2. **Speech-to-text**: Sent to Google API
3. **Command processing**: Local
4. **AI queries**: Local Ollama (private)
5. **Voice synthesis**: Local (espeak/pyttsx3)

### Privacy Mode:
For offline speech recognition (no Google):
```bash
# Install Vosk (offline speech recognition)
pip3 install vosk

# Download language model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d /opt/vosk/

# Update JARVIS to use Vosk instead of Google
```

## Performance

### Resource Usage:
- **CPU**: ~5-10% idle, 30-50% when processing
- **RAM**: ~200MB base, +model size when querying AI
- **Disk**: ~100MB for dependencies

### Response Times:
- Wake word detection: <0.5s
- Speech recognition: 1-3s
- Simple commands: <1s
- AI queries: 2-10s (depends on model size)

## Tips

1. **Speak clearly**: Enunciate wake word and commands
2. **Wait for response**: Let JARVIS acknowledge before speaking
3. **Use natural language**: No need for rigid command structure
4. **Test first**: Use `jarvis test` to verify commands
5. **Check logs**: Use `journalctl -u jarvis` for debugging
6. **Adjust mic**: Use `alsamixer` to set input volume
7. **Choose model**: Smaller AI models = faster responses

## Integration with Other Tools

### With AI Models:
```bash
# JARVIS uses ai-models automatically
"Jarvis, which model are you using?"
"Jarvis, switch to faster model"
```

### With System Scripts:
```bash
# Call your scripts
"Jarvis, run my backup script"
"Jarvis, start development server"
```

### With Desktop GUI:
```bash
# Control GUI applications
"Jarvis, open Firefox"
"Jarvis, launch terminal"
"Jarvis, show desktop"
```

## Examples by Category

### Daily Use:
```
"Jarvis, good morning"           → Greets and shows summary
"Jarvis, what's the weather?"    → Checks weather
"Jarvis, remind me in 10 minutes" → Sets reminder
"Jarvis, play music"             → Opens music player
```

### Development:
```
"Jarvis, create React app"       → Runs npx create-react-app
"Jarvis, start Docker container" → docker-compose up
"Jarvis, run tests"              → pytest or npm test
"Jarvis, deploy to production"   → Custom deploy script
```

### System Admin:
```
"Jarvis, who is logged in?"      → Shows active users
"Jarvis, disk usage"             → df -h
"Jarvis, running processes"      → ps aux
"Jarvis, network connections"    → netstat -tulpn
```

## Summary

✅ **Fully voice-controlled OS**
✅ **Natural language commands**  
✅ **Integrated with AI models**
✅ **System-wide control**
✅ **Privacy-focused (local AI)**
✅ **Customizable wake word**
✅ **Extensible command system**

**Your OS is now controllable entirely by voice!** 🎤🤖✨
