# AI Model Manager - User Guide 🤖

## Overview
Your custom OS now includes a flexible AI model manager that lets you download and switch between different AI models under 7B parameters.

## Available Models

### 🔥 Recommended (7B Parameters)
1. **dolphin-mistral** - Completely uncensored Mistral 7B (4GB)
2. **nous-hermes2-mistral** - Advanced reasoning, uncensored (4GB)
3. **wizardlm-uncensored** - No safety filters, creative (4GB)
4. **openhermes** - Excellent instruction following (4GB)

### ⚡ Smaller Models (1-3B Parameters - Very Fast)
5. **dolphin-phi** - Uncensored Phi-2 2.7B (1.6GB)
6. **orca-mini** - Small general purpose 3B (2GB)
7. **stablelm2** - Ultra-fast 1.6B (1GB)
8. **phi** - Microsoft Phi-2 2.7B (1.6GB)

### 🎯 Specialized Models
9. **codellama:7b-code** - Coding specialist (4GB)
10. **neural-chat** - Conversational AI (4GB)
11. **starling-lm** - High quality responses (4GB)
12. **solar** - Bilingual model (4GB)

### 🤗 Hugging Face Models
13. **TinyLlama-1.1B** - Ultra-lightweight (700MB)
14. **Phi-2** - Microsoft's efficient model (1.6GB)
15. **StableLM-3B** - Stability AI (2GB)
16. **RedPajama-3B** - Open source (2GB)

## Usage

### Interactive Menu (Recommended)
```bash
ai-models
```
This opens a friendly menu where you can:
- Download new models
- List installed models
- Delete models
- Switch default model
- Test models

### Command Line Usage

**Download a model:**
```bash
ai-models download dolphin-mistral
ai-models download phi
```

**List installed models:**
```bash
ai-models list
```

**Test a model:**
```bash
ai-models test dolphin-mistral
ai-models test phi "Write a Python hello world"
```

**Delete a model:**
```bash
ai-models delete
# Follow the prompts
```

## First Time Setup

After booting your OS:

**Step 1: Choose and download a model**
```bash
ai-models
# Select option 1, then choose a model (recommend #5 dolphin-phi for first test)
```

**Step 2: Start AI services**
```bash
systemctl start ollama
systemctl start ai-controller
```

**Step 3: Use your AI**
```bash
ai query "Hello, introduce yourself"
ai do "show system info"
ai chat
```

## Choosing the Right Model

### For Learning/Testing:
- **dolphin-phi (2.7B)** - Fast, uncensored, only 1.6GB
- **stablelm2 (1.6B)** - Very fast responses

### For General Use:
- **dolphin-mistral (7B)** - Best quality, uncensored
- **nous-hermes2-mistral (7B)** - Excellent reasoning

### For Coding:
- **codellama:7b-code** - Specialized for programming

### For Speed:
- **TinyLlama-1.1B** - Ultra-fast, minimal RAM

## Resource Requirements

| Model Size | RAM Needed | Disk Space | Speed |
|-----------|------------|------------|-------|
| 1-2B | ~1.5 GB | 700MB-1GB | Very Fast |
| 2-3B | ~3 GB | 1.6-2GB | Fast |
| 7B | ~6 GB | 4GB | Moderate |

Your system has:
- **8 CPU cores** ✅
- **15GB RAM** ✅ Can run any model
- **8GB disk allocated** ✅ Can fit 2-3 models

## Switching Models

To change which model the `ai` command uses:

```bash
ai-models
# Select option 4 (Switch default model)
# Enter model name
systemctl restart ai-controller
```

## Multiple Models

You can have multiple models installed:

```bash
# Download several models
ai-models download dolphin-phi      # 1.6GB
ai-models download orca-mini        # 2GB
ai-models download dolphin-mistral  # 4GB

# Total: 7.6GB (fits in your 8GB allocation)

# Test each one
ollama run dolphin-phi "Hello"
ollama run orca-mini "Hello"
ollama run dolphin-mistral "Hello"
```

## Advanced Usage

### Direct Ollama Commands:
```bash
# Run any model directly
ollama run dolphin-mistral "Your prompt here"

# Chat mode
ollama run dolphin-phi

# Show model details
ollama show dolphin-mistral
```

### Using Hugging Face Models:
After downloading HF models with `ai-models`, use them with:
```bash
python3 /opt/ai-control/hf_inference.py "model-name" "your prompt"
```

## Tips

1. **Start small**: Try dolphin-phi (1.6GB) first before downloading 7B models
2. **Multiple models**: Download 2-3 different sizes for different tasks
3. **RAM management**: 7B models need 6GB RAM, may slow down system if low
4. **Disk space**: Check available space before downloading large models
5. **Testing**: Always test a model before setting it as default

## Troubleshooting

**Model download fails:**
```bash
# Check Ollama is running
systemctl status ollama
systemctl restart ollama

# Check internet connection
ping -c 3 8.8.8.8
```

**Out of disk space:**
```bash
# Delete unused models
ai-models delete

# Check available space
df -h /var/lib/ollama
```

**Model too slow:**
```bash
# Switch to smaller model
ai-models
# Choose a 1-3B model instead of 7B
```

## Example Workflow

```bash
# 1. Boot your OS and login as root

# 2. Download a fast model for testing
ai-models download dolphin-phi

# 3. Download a powerful model for complex tasks  
ai-models download dolphin-mistral

# 4. Start services
systemctl start ollama ai-controller

# 5. Use the fast model for quick queries
ollama run dolphin-phi "Quick question: what is Linux?"

# 6. Use powerful model for complex work
ollama run dolphin-mistral "Explain quantum computing in detail"

# 7. Set your preferred default
ai-models
# Option 4 → switch default to dolphin-phi
systemctl restart ai-controller

# 8. Now `ai` command uses your default
ai query "Hello!"
ai chat
```

## Summary

✅ **Flexible**: Choose any model under 7B parameters  
✅ **Multiple sources**: Ollama + Hugging Face  
✅ **Easy management**: Interactive menu or CLI  
✅ **Switchable**: Change default model anytime  
✅ **Testable**: Try before you commit  
✅ **Space efficient**: Start small, grow as needed  

Your OS is now ready to download and manage multiple AI models! 🚀
