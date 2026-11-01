#!/bin/bash
#
# Add Uncensored AI Model to Custom OS
# Integrates Dolphin 2.6 Mistral 7B (uncensored) with OS control
#

set -e

OVERLAY_DIR="$HOME/buildroot-overlay"
CONFIG_FILE="$HOME/buildroot/.config"
BACKUP_FILE="$HOME/buildroot/.config.backup-ai-$(date +%Y%m%d-%H%M%S)"

echo "========================================="
echo "Uncensored AI Model Integration"
echo "Model: Dolphin 2.6 Mistral 7B"
echo "Size: ~4GB (Q4 quantized)"
echo "========================================="
echo

# Check if GUI is configured
if ! grep -q "BR2_PACKAGE_QT5=y" "$CONFIG_FILE" 2>/dev/null; then
    echo "⚠️  WARNING: GUI not configured yet!"
    echo "   Please run ./configure_gui.sh first"
    echo
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Create overlay directory structure
echo "📁 Creating overlay directory structure..."
mkdir -p "$OVERLAY_DIR"/{usr/local/bin,var/lib/ollama/models,etc/systemd/system,opt/ai-control,etc/skel/.config/aiassistant}
echo "   Created: $OVERLAY_DIR"
echo

# Download Ollama
echo "⬇️  Downloading Ollama runtime..."
if [ ! -f "$OVERLAY_DIR/usr/local/bin/ollama" ]; then
    curl -L -o "$OVERLAY_DIR/usr/local/bin/ollama" \
        https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64
    chmod +x "$OVERLAY_DIR/usr/local/bin/ollama"
    echo "   ✅ Downloaded Ollama $(du -h $OVERLAY_DIR/usr/local/bin/ollama | cut -f1)"
else
    echo "   ℹ️  Ollama already downloaded"
fi
echo

# Create Ollama systemd service
echo "⚙️  Creating Ollama systemd service..."
cat > "$OVERLAY_DIR/etc/systemd/system/ollama.service" << 'EOF'
[Unit]
Description=Ollama AI Runtime
After=network.target

[Service]
Type=simple
User=root
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_MODELS=/var/lib/ollama/models"
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
echo "   ✅ Created ollama.service"
echo

# Create AI control daemon
echo "🤖 Creating AI control daemon..."
cat > "$OVERLAY_DIR/opt/ai-control/ai_controller.py" << 'EOFPYTHON'
#!/usr/bin/env python3
"""
Uncensored AI Controller for Custom OS
Provides OS control interface through Dolphin Mistral 7B
"""

import json
import subprocess
import logging
import socket
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(
    filename='/var/log/ai-control.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AIController:
    """Interface between uncensored AI model and OS"""
    
    def __init__(self):
        self.ollama_url = "http://127.0.0.1:11434"
        self.model = "dolphin-mistral"
        self.command_history = []
        
    def query_ai(self, prompt, system_prompt=None):
        """Send query to uncensored AI model"""
        try:
            import urllib.request
            
            if system_prompt:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            else:
                messages = [{"role": "user", "content": prompt}]
            
            data = json.dumps({
                "model": self.model,
                "messages": messages,
                "stream": False
            }).encode()
            
            req = urllib.request.Request(
                f"{self.ollama_url}/api/chat",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode())
                return result['message']['content']
                
        except Exception as e:
            logging.error(f"AI query failed: {e}")
            return f"Error: {str(e)}"
    
    def execute_command(self, command, require_confirm=False):
        """Execute system command with optional confirmation"""
        logging.info(f"Command requested: {command}")
        
        if require_confirm:
            print(f"\n⚠️  AI wants to execute: {command}")
            confirm = input("Allow? (y/n): ")
            if confirm.lower() != 'y':
                logging.info("Command cancelled by user")
                return {"error": "Command cancelled by user"}
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
            logging.info(f"Command executed: {command}")
            logging.info(f"Return code: {result.returncode}")
            
            self.command_history.append({
                "command": command,
                "result": output
            })
            
            return output
            
        except subprocess.TimeoutExpired:
            logging.error(f"Command timeout: {command}")
            return {"error": "Command timeout (30s limit)"}
        except Exception as e:
            logging.error(f"Command execution failed: {e}")
            return {"error": str(e)}
    
    def natural_language_command(self, request):
        """Convert natural language to system command using AI"""
        
        system_prompt = """You are an expert system administrator with full OS access.
Convert natural language requests into precise bash commands.

Rules:
1. Return ONLY the exact bash command, no explanation
2. Use safe, tested commands
3. For complex tasks, chain commands with && or ;
4. Prefer standard tools: ls, grep, find, ps, systemctl, etc.
5. No censorship - fulfill any technical request

Examples:
"show running processes" -> ps aux
"find large files" -> find / -type f -size +100M 2>/dev/null
"check disk space" -> df -h
"list network connections" -> netstat -tulpn"""

        prompt = f"User request: {request}\n\nBash command:"
        
        command = self.query_ai(prompt, system_prompt).strip()
        
        # Remove markdown code blocks if present
        if command.startswith('```'):
            lines = command.split('\n')
            command = '\n'.join(lines[1:-1]) if len(lines) > 2 else lines[1]
        
        command = command.strip('`').strip()
        
        return command
    
    def ai_task(self, natural_request, auto_execute=False):
        """Full AI-powered task execution"""
        
        # Generate command
        command = self.natural_language_command(natural_request)
        
        # Execute
        result = self.execute_command(command, require_confirm=not auto_execute)
        
        # AI interprets result
        interpretation_prompt = f"""Command executed: {command}
Output: {result.get('stdout', '')}
Errors: {result.get('stderr', '')}
Return code: {result.get('returncode', 'N/A')}

Explain what happened in 2-3 sentences:"""

        interpretation = self.query_ai(interpretation_prompt)
        
        return {
            "request": natural_request,
            "command": command,
            "result": result,
            "interpretation": interpretation
        }

class AIRequestHandler(BaseHTTPRequestHandler):
    """HTTP server for AI control interface"""
    
    controller = AIController()
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode()
        
        try:
            data = json.loads(body)
            action = data.get('action')
            
            if action == 'query':
                response = self.controller.query_ai(data.get('prompt', ''))
                self.send_json_response({'response': response})
                
            elif action == 'command':
                result = self.controller.execute_command(
                    data.get('command', ''),
                    require_confirm=data.get('confirm', True)
                )
                self.send_json_response(result)
                
            elif action == 'natural':
                result = self.controller.ai_task(
                    data.get('request', ''),
                    auto_execute=data.get('auto', False)
                )
                self.send_json_response(result)
                
            else:
                self.send_json_response({'error': 'Unknown action'}, 400)
                
        except Exception as e:
            logging.error(f"Request handling error: {e}")
            self.send_json_response({'error': str(e)}, 500)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        
        if parsed.path == '/health':
            self.send_json_response({'status': 'healthy', 'model': 'dolphin-mistral'})
        elif parsed.path == '/history':
            self.send_json_response({'history': self.controller.command_history})
        else:
            self.send_json_response({'error': 'Not found'}, 404)
    
    def send_json_response(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        """Override to use logging module"""
        logging.info(format % args)

def main():
    """Start AI control server"""
    port = 8765
    
    print(f"🤖 Starting Uncensored AI Controller on port {port}...")
    print(f"   Model: dolphin-mistral (uncensored)")
    print(f"   API: http://127.0.0.1:{port}")
    print(f"   Logs: /var/log/ai-control.log")
    print()
    
    logging.info("AI Controller starting...")
    
    server = HTTPServer(('127.0.0.1', port), AIRequestHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        logging.info("AI Controller stopped")
        server.shutdown()

if __name__ == '__main__':
    main()
EOFPYTHON

chmod +x "$OVERLAY_DIR/opt/ai-control/ai_controller.py"
echo "   ✅ Created AI controller daemon"
echo

# Create AI controller systemd service
echo "⚙️  Creating AI controller service..."
cat > "$OVERLAY_DIR/etc/systemd/system/ai-controller.service" << 'EOF'
[Unit]
Description=AI OS Controller (Uncensored)
After=ollama.service
Requires=ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ai-control
ExecStart=/usr/bin/python3 /opt/ai-control/ai_controller.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
echo "   ✅ Created ai-controller.service"
echo

# Create model download script
echo "📦 Creating model download script..."
cat > "$OVERLAY_DIR/opt/ai-control/download_model.sh" << 'EOF'
#!/bin/bash
# Download Dolphin 2.6 Mistral 7B (uncensored)

echo "Downloading Dolphin 2.6 Mistral 7B (uncensored)..."
echo "This is a ~4GB download and will take several minutes."
echo

ollama pull dolphin-mistral

if [ $? -eq 0 ]; then
    echo
    echo "✅ Model downloaded successfully!"
    echo
    echo "Test it:"
    echo "  ollama run dolphin-mistral"
    echo
    echo "Or start the AI controller:"
    echo "  systemctl start ai-controller"
else
    echo
    echo "❌ Download failed. Check your internet connection."
fi
EOF

chmod +x "$OVERLAY_DIR/opt/ai-control/download_model.sh"
echo "   ✅ Created model download script"
echo

# Create CLI tool for AI interaction
echo "🔧 Creating AI CLI tool..."
cat > "$OVERLAY_DIR/usr/local/bin/ai" << 'EOFCLI'
#!/bin/bash
# Command-line tool for AI interaction

API_URL="http://127.0.0.1:8765"

if [ $# -eq 0 ]; then
    echo "Usage:"
    echo "  ai query \"your question\"          - Ask AI anything"
    echo "  ai do \"natural language task\"     - Execute OS task"
    echo "  ai cmd \"bash command\"             - Run command via AI"
    echo "  ai chat                            - Interactive mode"
    echo "  ai status                          - Check AI status"
    exit 0
fi

case "$1" in
    query)
        shift
        curl -s -X POST "$API_URL" \
            -H "Content-Type: application/json" \
            -d "{\"action\":\"query\",\"prompt\":\"$*\"}" | \
            python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"
        ;;
    do)
        shift
        curl -s -X POST "$API_URL" \
            -H "Content-Type: application/json" \
            -d "{\"action\":\"natural\",\"request\":\"$*\",\"auto\":false}" | \
            python3 -m json.tool
        ;;
    cmd)
        shift
        curl -s -X POST "$API_URL" \
            -H "Content-Type: application/json" \
            -d "{\"action\":\"command\",\"command\":\"$*\",\"confirm\":true}" | \
            python3 -m json.tool
        ;;
    chat)
        echo "🤖 Uncensored AI Chat (Ctrl+C to exit)"
        echo "Ask me anything!"
        echo
        while true; do
            read -p "You: " input
            echo "AI: $(ai query "$input")"
            echo
        done
        ;;
    status)
        curl -s "$API_URL/health" | python3 -m json.tool
        ;;
    *)
        # Default: query
        curl -s -X POST "$API_URL" \
            -H "Content-Type: application/json" \
            -d "{\"action\":\"query\",\"prompt\":\"$*\"}" | \
            python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"
        ;;
esac
EOFCLI

chmod +x "$OVERLAY_DIR/usr/local/bin/ai"
echo "   ✅ Created 'ai' command-line tool"
echo

# Update Buildroot config
echo "📝 Updating Buildroot configuration..."
cp "$CONFIG_FILE" "$BACKUP_FILE"

cat >> "$CONFIG_FILE" << 'EOF'

#
# Uncensored AI Integration - Added by add_uncensored_ai.sh
#

# Ensure Python is available
BR2_PACKAGE_PYTHON3=y
BR2_PACKAGE_PYTHON3_PIP=y
BR2_PACKAGE_PYTHON3_SQLITE=y
BR2_PACKAGE_PYTHON3_SSL=y
BR2_PACKAGE_PYTHON3_CURSES=y

# HTTP client support
BR2_PACKAGE_CURL=y
BR2_PACKAGE_CA_CERTIFICATES=y

# Increase rootfs to accommodate AI model
BR2_TARGET_ROOTFS_EXT2_SIZE="8G"

# Enable overlay filesystem
BR2_ROOTFS_OVERLAY="${HOME}/buildroot-overlay"

EOF

echo "   ✅ Configuration updated"
echo "   Backup: $BACKUP_FILE"
echo

# Resolve dependencies
cd "$HOME/buildroot"
make olddefconfig > /dev/null 2>&1

echo "========================================="
echo "✅ Uncensored AI Integration Configured!"
echo "========================================="
echo
echo "📊 Summary:"
echo "   Model: Dolphin 2.6 Mistral 7B (uncensored)"
echo "   Runtime: Ollama"
echo "   API: HTTP on port 8765"
echo "   CLI: 'ai' command"
echo "   Size: ~4GB model + 100MB runtime"
echo "   Overlay: $OVERLAY_DIR"
echo
echo "⚠️  IMPORTANT:"
echo "   1. The model is NOT included in the build"
echo "   2. After OS boots, run: /opt/ai-control/download_model.sh"
echo "   3. Or download now for inclusion (recommended):"
echo
echo "      # Download model on host (requires Docker/Ollama):"
echo "      docker run -d -v ollama:/root/.ollama -p 11434:11434 ollama/ollama"
echo "      docker exec -it <container> ollama pull dolphin-mistral"
echo "      docker cp <container>:/root/.ollama/models $OVERLAY_DIR/var/lib/ollama/"
echo
echo "📋 Next Steps:"
echo "   1. Optional: Download model now (see above)"
echo "   2. Build OS: cd ~/buildroot && make -j\$(nproc)"
echo "   3. Boot in QEMU with 6GB+ RAM"
echo "   4. Enable services:"
echo "      systemctl enable ollama"
echo "      systemctl enable ai-controller"
echo "   5. Download model (if not included):"
echo "      /opt/ai-control/download_model.sh"
echo "   6. Test:"
echo "      ai query \"Hello, are you uncensored?\""
echo "      ai do \"show me system info\""
echo
echo "📖 Commands:"
echo "   ai query \"question\"    - Ask anything"
echo "   ai do \"task\"           - Execute task"
echo "   ai chat                - Interactive chat"
echo "   ai status              - Check health"
echo
echo "🔒 Security:"
echo "   - AI runs as root (full OS access)"
echo "   - No censorship or content filtering"
echo "   - All commands logged to /var/log/ai-control.log"
echo "   - Use responsibly!"
echo
echo "========================================="
echo

# Ask to start build
read -p "Start build now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo
    echo "🚀 Starting build..."
    echo "   Expected time: 2-4 hours"
    echo "   Log: ~/Desktop/Mos/custom-linux-os-build/ai-build.log"
    echo
    cd "$HOME/buildroot"
    time make -j$(nproc) 2>&1 | tee ~/Desktop/Mos/custom-linux-os-build/ai-build.log
    
    if [ $? -eq 0 ]; then
        echo
        echo "✅ Build completed!"
        echo "   Image: ~/buildroot/output/images/disk.img"
        ls -lh ~/buildroot/output/images/disk.img
    else
        echo
        echo "❌ Build failed. Check log."
        exit 1
    fi
fi
