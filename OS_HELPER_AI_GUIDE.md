# OS Helper AI - Lightweight Configuration Assistant 🛠️

## Overview
A tiny AI model (<1GB) that helps users configure and troubleshoot the OS. Pre-built, lightweight, and optimized for quick system help.

## Why OS Helper?

When you need **quick help** without loading a large AI model:
- ✅ **Tiny size**: 45MB to 950MB (vs 4GB for full models)
- ✅ **Fast responses**: 1-2 seconds (vs 5-10 seconds)
- ✅ **Low RAM**: Uses ~1GB RAM (vs 6GB)
- ✅ **Always ready**: Quick to load
- ✅ **Specialized**: Optimized for OS configuration help

## Available Models

### 🔥 Recommended: TinyLlama-1.1B
- **Size**: 637MB
- **Quality**: Good for most tasks
- **Speed**: Very fast (~2s responses)
- **Use case**: General OS configuration help

### ⚡ Ultra-Fast: all-MiniLM
- **Size**: 45MB (tiniest!)
- **Quality**: Basic but helpful
- **Speed**: Instant (<1s responses)
- **Use case**: Quick command lookups

### 🎯 Uncensored: TinyDolphin-1.1B
- **Size**: 637MB
- **Quality**: Good + uncensored
- **Speed**: Very fast
- **Use case**: Unrestricted configuration help

### 🔧 Specialized: Quantized Models
- **codellama:7b-q2**: 950MB - For scripting/coding help
- **mistral:7b-q2**: 950MB - Better quality responses
- **stablelm-zephyr-3b**: 1.7GB - Excellent quality

## Installation

### Quick Setup (TinyLlama):
```bash
# After booting your OS
setup-os-helper setup

# Or interactive menu
setup-os-helper
```

### Choose Specific Model:
```bash
setup-os-helper install tiny        # TinyLlama (recommended)
setup-os-helper install dolphin     # TinyDolphin
setup-os-helper install mini        # all-MiniLM (ultra-tiny)
```

## Usage

### Ask Configuration Questions:
```bash
os-helper "how do I check disk space?"
os-helper "how to configure network?"
os-helper "how to install packages?"
os-helper "how to setup SSH server?"
os-helper "how to mount USB drive?"
os-helper "how to change hostname?"
os-helper "how to check system logs?"
os-helper "how to manage firewall?"
```

### Common Examples:

**System Information:**
```bash
os-helper "show system resources"
os-helper "check CPU usage"
os-helper "list running services"
```

**Network Configuration:**
```bash
os-helper "configure static IP"
os-helper "setup DNS server"
os-helper "troubleshoot network"
```

**Package Management:**
```bash
os-helper "install nginx"
os-helper "update all packages"
os-helper "search for package"
```

**User Management:**
```bash
os-helper "create new user"
os-helper "change user password"
os-helper "add user to sudo"
```

**File Operations:**
```bash
os-helper "find large files"
os-helper "change file permissions"
os-helper "compress directory"
```

## Integration with Other Tools

### With JARVIS:
```bash
# JARVIS can use OS Helper for quick lookups
"Jarvis, ask helper how to check disk space"
```

### With Main AI:
```bash
# Use OS Helper for quick help
os-helper "quick command for disk space"

# Use main AI for complex tasks
ai query "explain Linux kernel architecture in detail"
```

### With AI Models Manager:
```bash
# Manage multiple helper models
ai-models list
os-helper "which model should I use?"
```

## Comparison: OS Helper vs Main AI

| Feature | OS Helper (TinyLlama) | Main AI (Dolphin 7B) |
|---------|----------------------|---------------------|
| Size | 637MB | 4GB |
| RAM | ~1GB | ~6GB |
| Speed | 1-2 seconds | 5-10 seconds |
| Quality | Good for basics | Excellent |
| Use case | Quick help | Complex tasks |
| Loading | Instant | 2-5 seconds |

**Best Practice:**
- **OS Helper**: Quick configuration questions, commands, troubleshooting
- **Main AI**: Detailed explanations, complex problems, coding

## Example Workflow

```bash
# First boot - setup OS Helper
setup-os-helper setup

# Quick configuration help
os-helper "how do I check disk space?"
# → "Use 'df -h' to check disk space..."

# Follow the advice
df -h

# Need more detail? Ask main AI
ai query "explain disk partitioning in detail"
# → Detailed explanation...

# Quick lookup again
os-helper "how to format USB drive?"
# → "Use 'mkfs.ext4 /dev/sdX' to format..."
```

## Pre-configured OS Help Topics

Run `setup-os-helper topics` to see all categories:

### System Administration:
- User management
- Service management
- System monitoring
- Log analysis

### Network Configuration:
- IP configuration
- DNS setup
- Firewall rules
- Network troubleshooting

### Package Management:
- Installing packages
- Updating system
- Removing packages
- Repository management

### File System:
- Mounting drives
- Disk management
- File permissions
- Backup/restore

### Security:
- SSH configuration
- Firewall setup
- User permissions
- Security auditing

## Advanced Usage

### Custom System Prompts:
Edit `/opt/os-helper/helper.py` to customize:
```python
system_prompt = """You are specialized in [your focus area].
Provide brief, practical answers..."""
```

### Integration with Scripts:
```bash
#!/bin/bash
# Get quick help in scripts
ANSWER=$(os-helper "best way to backup directory")
echo "$ANSWER"
```

### Batch Questions:
```bash
# Ask multiple questions
for q in "check disk" "check memory" "check CPU"; do
    os-helper "$q"
done
```

## Performance Metrics

### TinyLlama (637MB):
- **Load time**: <1 second
- **Response time**: 1-2 seconds
- **RAM usage**: ~1GB
- **Quality**: 7/10

### all-MiniLM (45MB):
- **Load time**: Instant
- **Response time**: <1 second
- **RAM usage**: ~200MB
- **Quality**: 5/10 (basic)

### Quantized 7B (950MB):
- **Load time**: 1-2 seconds
- **Response time**: 2-3 seconds
- **RAM usage**: ~2GB
- **Quality**: 9/10

## Troubleshooting

### OS Helper not found:
```bash
# Reinstall
setup-os-helper setup

# Check if installed
ollama list | grep tiny
```

### Slow responses:
```bash
# Switch to smaller model
setup-os-helper install mini

# Check system resources
top
free -h
```

### Incorrect answers:
```bash
# Upgrade to better model
setup-os-helper install
# Choose option 3 (stablelm-zephyr-3b)

# Or use main AI for complex questions
ai query "detailed question here"
```

## Tips

1. **Start with TinyLlama**: Best balance of size, speed, and quality
2. **Use for quick lookups**: Don't overthink, just ask
3. **Combine with main AI**: OS Helper for quick, main AI for detailed
4. **Pre-install on boot**: Add to first-boot script
5. **Keep it updated**: Periodically check for model updates

## Size Comparison

```
OS Component Sizes:
├── Base OS:              ~500MB
├── Main AI (optional):    4GB
├── OS Helper:            637MB  ← You are here
├── JARVIS dependencies:  ~100MB
└── Total with helper:    ~1.2GB (without main AI)
                          ~5.2GB (with main AI)
```

## When to Use What

### Use OS Helper for:
✅ "How do I...?" questions
✅ Command syntax lookups
✅ Quick troubleshooting
✅ Configuration steps
✅ Common tasks

### Use Main AI for:
✅ Complex explanations
✅ Code generation
✅ Detailed analysis
✅ Creative tasks
✅ Long conversations

### Use JARVIS for:
✅ Voice commands
✅ Hands-free operation
✅ System automation
✅ Multi-step tasks

## Integration Examples

### In Shell Scripts:
```bash
#!/bin/bash
# Intelligent error handling
if ! command -v nginx &> /dev/null; then
    HELP=$(os-helper "how to install nginx")
    echo "Nginx not found. Helper says: $HELP"
fi
```

### With Aliases:
```bash
# Add to ~/.bashrc
alias h='os-helper'
alias help='os-helper'

# Now just type:
h "how to check logs"
```

### First Boot Setup:
```bash
# Add to /etc/rc.local or first-boot script
setup-os-helper setup
os-helper "system successfully configured"
```

## Summary

✅ **Lightweight**: 45MB - 950MB (vs 4GB for full AI)  
✅ **Fast**: 1-2 second responses  
✅ **Specialized**: Optimized for OS configuration  
✅ **Always ready**: Quick to load  
✅ **Multiple options**: Choose size vs quality  
✅ **Pre-configured**: Works out of the box  
✅ **Integrated**: Works with JARVIS and main AI  

**Your OS now has a lightweight AI helper for quick configuration assistance!** 🛠️✨
