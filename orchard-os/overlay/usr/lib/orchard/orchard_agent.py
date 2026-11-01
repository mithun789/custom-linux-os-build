#!/usr/bin/env python3
"""Orchard Agent: an AI assistant that works on your computer.

It talks to any OpenAI-compatible chat API (Ollama on this PC, Hugging Face,
Groq, OpenRouter, Google Gemini, Mistral or a custom endpoint) and uses tools
to run commands, read and edit files, search and read the web, and check the
system. Every tool call and every approval decision is logged.

Safety model:
  ask   (default) every command and file change needs your approval
  auto  read-only commands run automatically, the rest need approval
  yolo  everything runs automatically, except commands on the always-ask list
"""
import argparse
import datetime as dt
import html
import html.parser
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

VERSION = "1.0"
HOME = Path.home()
CONF_DIR = HOME / ".config" / "orchard"
CONF_FILE = CONF_DIR / "agent.json"
KEYS_FILE = CONF_DIR / "keys.env"
LOG_DIR = HOME / ".local" / "share" / "orchard" / "agent"
LOG_FILE = LOG_DIR / "agent.log"
GUARD_ALERTS = Path("/var/log/orchard/guard-alerts.log")

PROVIDERS = {
    "ollama": {"base_url": "http://127.0.0.1:11434/v1", "key_env": None,
               "default_model": "qwen2.5:3b", "note": "Local models on this PC (orchard-ai setup)"},
    "huggingface": {"base_url": "https://router.huggingface.co/v1", "key_env": "HF_TOKEN",
                    "default_model": "Qwen/Qwen2.5-Coder-32B-Instruct",
                    "note": "Free token: huggingface.co/settings/tokens"},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "key_env": "GROQ_API_KEY",
             "default_model": "llama-3.3-70b-versatile", "note": "Free key: console.groq.com"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "key_env": "OPENROUTER_API_KEY",
                   "default_model": "meta-llama/llama-3.3-70b-instruct:free",
                   "note": "Free models end in ':free'. Key: openrouter.ai/keys"},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "key_env": "GEMINI_API_KEY",
               "default_model": "gemini-2.0-flash", "note": "Free key: aistudio.google.com"},
    "mistral": {"base_url": "https://api.mistral.ai/v1", "key_env": "MISTRAL_API_KEY",
                "default_model": "mistral-small-latest", "note": "Free tier key: console.mistral.ai"},
    "custom": {"base_url": "", "key_env": "CUSTOM_API_KEY", "default_model": "",
               "note": "Any OpenAI-compatible server (LM Studio, vLLM, llama.cpp server)"},
}

# Commands that always need approval, in every mode.
ALWAYS_ASK = [
    r"\brm\s+(-[a-zA-Z]*[rf][a-zA-Z]*\s+)+/(\s|$|\*)", r"\bmkfs", r"\bdd\b.*\bof=/dev/", r"\bwipefs\b",
    r"\bparted\b", r"\bfdisk\b", r"\bsgdisk\b", r":\(\)\s*\{", r"\bshutdown\b", r"\breboot\b",
    r"\bpoweroff\b", r"\bhalt\b", r"\bchmod\s+-R\s+[0-7]*7[0-7]*\s+/", r"\bchown\s+-R\s+\S+\s+/(\s|$)",
    r"(curl|wget)[^|]*\|\s*(sudo\s+)?(ba|z|)sh", r"\buserdel\b", r"\bpasswd\b", r">\s*/dev/sd",
    r"\bsystemctl\s+(disable|mask|stop)\s+(ssh|NetworkManager|lightdm|systemd)", r"/etc/(passwd|shadow|sudoers)",
]
# First words of commands that only read state; 'auto' mode runs them without asking.
READ_ONLY = {
    "ls", "cat", "head", "tail", "less", "grep", "rg", "find", "pwd", "whoami", "id", "uname", "uptime",
    "free", "df", "du", "ps", "top", "htop", "lsblk", "lscpu", "lspci", "lsusb", "ip", "ss", "nmcli",
    "date", "which", "file", "stat", "wc", "sort", "uniq", "echo", "env", "printenv", "hostname",
    "journalctl", "systemctl", "dpkg", "apt-cache", "git", "python3", "node", "sensors", "nvidia-smi",
    "ollama", "tree", "diff", "md5sum", "sha256sum", "lsmod", "dmesg", "w", "last", "timedatectl",
}
SAFE_SUBCOMMANDS = {
    "systemctl": {"status", "is-active", "is-enabled", "list-units", "list-unit-files", "--failed", "show"},
    "git": {"status", "log", "diff", "show", "branch", "remote", "rev-parse", "ls-files", "blame"},
    "dpkg": {"-l", "-L", "-S", "--list", "-s"},
    "apt-cache": {"policy", "show", "search", "depends", "rdepends"},
    "ollama": {"list", "ps", "show", "--version"},
    "ip": {"a", "addr", "r", "route", "link", "-br"},
    "nmcli": {"general", "device", "connection", "-t", "radio"},
}

SYSTEM_PROMPT = """You are Orchard Agent, an expert assistant built into Orchard OS, a Linux desktop based on Ubuntu 24.04 (XFCE, apt, systemd, NetworkManager, Flatpak).
You act on the user's computer through tools. Work like a careful senior engineer:
- Plan briefly, then use tools. Prefer running a command to guessing.
- Before changing files, read them. Make small, precise edits with edit_file.
- When writing code, run it or its tests to check it works, then fix errors you see.
- For facts that may be recent, use web_search and fetch_url, and cite the URLs you used.
- Use sudo only when needed. Explain risky steps before doing them.
- If a tool fails, read the error, adjust and retry; stop after 3 failed attempts and explain.
- Keep answers short and concrete. Show commands you ran when useful.
Current directory: {cwd}. User: {user}. Date: {date}."""

TOOLS = [
    {"type": "function", "function": {
        "name": "run_command",
        "description": "Run a bash command on this computer and return stdout, stderr and exit code.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "The bash command"},
            "timeout": {"type": "integer", "description": "Seconds before the command is stopped (default 120)"}},
            "required": ["command"]}}},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a text file. Returns numbered lines.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"},
            "offset": {"type": "integer", "description": "First line, 1-based"},
            "limit": {"type": "integer", "description": "Number of lines (default 400)"}},
            "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Create or overwrite a file with the given content.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "edit_file",
        "description": "Replace one exact occurrence of old_text with new_text in a file.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}},
            "required": ["path", "old_text", "new_text"]}}},
    {"type": "function", "function": {
        "name": "list_dir",
        "description": "List files in a directory.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "search_files",
        "description": "Search file contents with a regular expression (like grep -rn).",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]}}},
    {"type": "function", "function": {
        "name": "web_search",
        "description": "Search the web. Returns titles, URLs and snippets.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "fetch_url",
        "description": "Download a web page and return its readable text.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {
        "name": "system_status",
        "description": "Report CPU, memory, disk, GPU, network, failed services, listening ports and security alerts.",
        "parameters": {"type": "object", "properties": {}}}},
]

COLORS = sys.stdout.isatty()


def c(code, text):
    return f"\033[{code}m{text}\033[0m" if COLORS else text


# ----------------------------------------------------------------- logging
def log_event(kind, **data):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    rec = {"time": dt.datetime.now().isoformat(timespec="seconds"), "event": kind, **data}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    try:
        os.chmod(LOG_FILE, 0o600)
    except OSError:
        pass


# ------------------------------------------------------------------ config
def load_keys():
    if KEYS_FILE.exists():
        for line in KEYS_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_config():
    cfg = {"provider": "ollama", "model": "", "mode": "ask", "custom_base_url": ""}
    if CONF_FILE.exists():
        try:
            cfg.update(json.loads(CONF_FILE.read_text()))
        except json.JSONDecodeError:
            print(c("33", f"warning: ignoring broken {CONF_FILE}"))
    legacy = CONF_DIR / "ai-model"
    if not cfg["model"] and cfg["provider"] == "ollama" and legacy.exists():
        cfg["model"] = legacy.read_text().strip()
    return cfg


def save_config(cfg):
    CONF_DIR.mkdir(parents=True, exist_ok=True)
    CONF_FILE.write_text(json.dumps(cfg, indent=2) + "\n")


# --------------------------------------------------------------------- API
class ApiError(Exception):
    pass


class Client:
    def __init__(self, provider, model, base_url=None):
        if provider not in PROVIDERS:
            raise ApiError(f"unknown provider '{provider}'. Choose from: {', '.join(PROVIDERS)}")
        p = PROVIDERS[provider]
        self.provider = provider
        self.base_url = (base_url or p["base_url"]).rstrip("/")
        self.model = model or p["default_model"]
        self.key = os.environ.get(p["key_env"]) if p["key_env"] else None
        if not self.base_url:
            raise ApiError("custom provider needs a base URL: orchard-agent config custom_base_url URL")
        if p["key_env"] and not self.key and provider != "custom":
            raise ApiError(f"{provider} needs an API key. Run: orchard-agent key {provider}\n({p['note']})")

    def chat(self, messages, tools=None):
        body = {"model": self.model, "messages": messages, "temperature": 0.2}
        if tools:
            body["tools"] = tools
        headers = {"Content-Type": "application/json", "User-Agent": f"orchard-agent/{VERSION}"}
        if self.key:
            headers["Authorization"] = f"Bearer {self.key}"
        req = urllib.request.Request(self.base_url + "/chat/completions",
                                     data=json.dumps(body).encode(), headers=headers)
        last = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=600) as r:
                    data = json.loads(r.read().decode())
                if "choices" not in data or not data["choices"]:
                    raise ApiError(f"unexpected reply: {str(data)[:300]}")
                return data["choices"][0]["message"]
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")[:500]
                last = ApiError(f"HTTP {e.code} from {self.provider}: {detail}")
                if e.code in (429, 500, 502, 503, 504):
                    time.sleep(2 ** attempt * 2)
                    continue
                raise last
            except urllib.error.URLError as e:
                last = ApiError(f"cannot reach {self.base_url}: {e.reason}")
                if self.provider == "ollama":
                    raise ApiError(f"{last}\nStart the local AI with: orchard-ai setup")
                time.sleep(2 ** attempt)
        raise last


# ------------------------------------------------------------------- tools
class TextExtractor(html.parser.HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form"}

    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in ("p", "br", "li", "h1", "h2", "h3", "h4", "tr", "div", "pre"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self):
        t = "".join(self.parts)
        t = re.sub(r"[ \t\r\f\v]+", " ", t)
        return re.sub(r"\n\s*\n+", "\n\n", t).strip()


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) OrchardAgent/1.0",
        "Accept-Language": "en-US,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(3_000_000)
        charset = r.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace"), r.headers.get_content_type()


def run_shell(cmd, timeout=120):
    try:
        p = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, timeout=timeout)
        out = p.stdout[-12000:]
        err = p.stderr[-4000:]
        return {"exit_code": p.returncode, "stdout": out, "stderr": err}
    except subprocess.TimeoutExpired as e:
        return {"exit_code": None, "error": f"timed out after {timeout}s",
                "stdout": (e.stdout or "")[-4000:] if isinstance(e.stdout, str) else ""}


class Tools:
    def __init__(self, mode, approver):
        self.mode = mode
        self.approve = approver

    def needs_approval_cmd(self, cmd):
        if any(re.search(p, cmd) for p in ALWAYS_ASK):
            return True, "on the always-ask list"
        if self.mode == "yolo":
            return False, ""
        if self.mode == "auto" and self.is_read_only(cmd):
            return False, ""
        return True, ""

    @staticmethod
    def is_read_only(cmd):
        if re.search(r"[>;&|`$]|\bsudo\b|\btee\b|\b-exec\b|\b-delete\b", cmd.replace("2>&1", "").replace("| head", "").replace("| tail", "").replace("| grep", "")):
            return False
        try:
            words = shlex.split(cmd)
        except ValueError:
            return False
        if not words or words[0] not in READ_ONLY:
            return False
        if words[0] in ("python3", "node"):
            return len(words) == 2 and words[1] in ("--version", "-V")
        if words[0] in SAFE_SUBCOMMANDS:
            return len(words) == 1 or words[1] in SAFE_SUBCOMMANDS[words[0]]
        return True

    def call(self, name, args):
        fn = getattr(self, "t_" + name, None)
        if fn is None:
            return {"error": f"unknown tool {name}"}
        try:
            return fn(**args)
        except TypeError as e:
            return {"error": f"bad arguments for {name}: {e}"}
        except Exception as e:  # report tool errors back to the model
            return {"error": f"{type(e).__name__}: {e}"}

    def t_run_command(self, command, timeout=120):
        ask, why = self.needs_approval_cmd(command)
        if ask and not self.approve("Run command", command, why):
            log_event("denied", tool="run_command", command=command)
            return {"error": "The user declined to run this command."}
        log_event("run_command", command=command, approved="user" if ask else "auto")
        res = run_shell(command, timeout=int(timeout or 120))
        log_event("result", tool="run_command", exit_code=res.get("exit_code"))
        return res

    def t_read_file(self, path, offset=1, limit=400):
        p = Path(path).expanduser()
        lines = p.read_text(errors="replace").splitlines()
        offset = max(1, int(offset or 1))
        chunk = lines[offset - 1: offset - 1 + int(limit or 400)]
        log_event("read_file", path=str(p))
        return {"path": str(p), "total_lines": len(lines),
                "content": "\n".join(f"{i:5d}  {l}" for i, l in enumerate(chunk, offset))}

    def _approve_write(self, path, preview):
        if self.mode == "yolo":
            return True
        return self.approve("Write file", f"{path}\n{preview}", "")

    def t_write_file(self, path, content):
        p = Path(path).expanduser()
        preview = textwrap.shorten(content.replace("\n", " | "), 300)
        if not self._approve_write(p, f"({len(content)} chars) {preview}"):
            log_event("denied", tool="write_file", path=str(p))
            return {"error": "The user declined this file change."}
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            shutil.copy2(p, str(p) + ".orchard-bak")
        p.write_text(content)
        log_event("write_file", path=str(p), size=len(content))
        return {"ok": True, "path": str(p), "backup": str(p) + ".orchard-bak" if Path(str(p) + ".orchard-bak").exists() else None}

    def t_edit_file(self, path, old_text, new_text):
        p = Path(path).expanduser()
        text = p.read_text()
        n = text.count(old_text)
        if n != 1:
            return {"error": f"old_text found {n} times; it must match exactly once. Read the file and retry."}
        if not self._approve_write(p, f"- {textwrap.shorten(old_text, 200)}\n+ {textwrap.shorten(new_text, 200)}"):
            log_event("denied", tool="edit_file", path=str(p))
            return {"error": "The user declined this file change."}
        shutil.copy2(p, str(p) + ".orchard-bak")
        p.write_text(text.replace(old_text, new_text, 1))
        log_event("edit_file", path=str(p))
        return {"ok": True, "path": str(p)}

    def t_list_dir(self, path="."):
        p = Path(path).expanduser()
        items = []
        for e in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name))[:300]:
            items.append(e.name + ("/" if e.is_dir() else f"  ({e.stat().st_size} B)"))
        return {"path": str(p), "entries": items}

    def t_search_files(self, pattern, path="."):
        res = run_shell(f"grep -rnI --exclude-dir=.git -E {shlex.quote(pattern)} {shlex.quote(path)} | head -100", 60)
        return {"matches": res.get("stdout", "")}

    def t_web_search(self, query):
        log_event("web_search", query=query)
        page, _ = http_get("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query))
        results = []
        for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
                             r'class="result__snippet"[^>]*>(.*?)</a>', page, re.S):
            url = html.unescape(m.group(1))
            q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            if "uddg" in q:
                url = q["uddg"][0]
            strip = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
            results.append({"title": strip(m.group(2)), "url": url, "snippet": strip(m.group(3))})
            if len(results) >= 8:
                break
        return {"query": query, "results": results} if results else {"query": query, "error": "no results"}

    def t_fetch_url(self, url):
        if not re.match(r"https?://", url):
            return {"error": "only http and https URLs are allowed"}
        log_event("fetch_url", url=url)
        body, ctype = http_get(url)
        if "html" in ctype:
            ex = TextExtractor()
            ex.feed(body)
            body = ex.text()
        return {"url": url, "content_type": ctype, "text": body[:20000],
                "truncated": len(body) > 20000}

    def t_system_status(self):
        cmds = {
            "os": "grep PRETTY_NAME /etc/os-release | cut -d= -f2; uname -r",
            "uptime_load": "uptime",
            "cpu": "lscpu | grep -E 'Model name|^CPU\\(s\\)' ",
            "memory": "free -h",
            "disk": "df -h -x tmpfs -x devtmpfs -x squashfs -x overlay",
            "gpu": "lspci | grep -Ei 'vga|3d|display'; command -v nvidia-smi >/dev/null && nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv",
            "top_processes": "ps -eo pid,user,%cpu,%mem,comm --sort=-%cpu | head -8",
            "failed_services": "systemctl --failed --no-legend --plain | head -20",
            "network": "nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device 2>/dev/null; ip -br addr",
            "listening_ports": "ss -tulnpH 2>/dev/null | awk '{print $1, $5, $7}' | head -40",
            "recent_errors": "journalctl -p err -b --no-pager -n 15 2>/dev/null",
        }
        out = {k: run_shell(v, 30).get("stdout", "").strip() for k, v in cmds.items()}
        if GUARD_ALERTS.exists():
            out["security_alerts"] = "\n".join(GUARD_ALERTS.read_text().splitlines()[-10:])
        log_event("system_status")
        return out


# ---------------------------------------------------------------- approval
def make_approver(gui):
    def tty_approve(title, detail, why):
        print(c("33", f"\n? {title}") + (c("31", f"  [{why}]") if why else ""))
        print(textwrap.indent(detail, "    "))
        try:
            ans = input(c("33", "  Allow? [y]es / [n]o: ")).strip().lower()
        except EOFError:
            return False
        ok = ans in ("y", "yes")
        log_event("approval", title=title, detail=detail[:500], allowed=ok)
        return ok

    def gui_approve(title, detail, why):
        text = f"<b>{html.escape(title)}</b>\n\n<tt>{html.escape(detail[:1500])}</tt>"
        if why:
            text += f"\n\n<span foreground='red'>{html.escape(why)}</span>"
        if not shutil.which("zenity"):
            return tty_approve(title, detail, why)
        ok = subprocess.run(["zenity", "--question", "--title=Orchard Agent", "--width=520",
                             "--ok-label=Allow", "--cancel-label=Deny", f"--text={text}"]).returncode == 0
        log_event("approval", title=title, detail=detail[:500], allowed=ok, via="gui")
        return ok

    return gui_approve if gui else tty_approve


# ------------------------------------------------------------------- agent
FENCE = re.compile(r"```(?:bash|sh|shell)\n(.*?)```", re.S)


def agent_turn(client, tools, messages, use_tools, max_steps=25, quiet=False):
    """Run the model until it answers without tool calls. Returns the final text."""
    for _ in range(max_steps):
        try:
            msg = client.chat(messages, TOOLS if use_tools[0] else None)
        except ApiError as e:
            if use_tools[0] and re.search(r"tool|function", str(e), re.I) and "HTTP 4" in str(e):
                # Model without tool support: switch to plain chat with fenced commands.
                use_tools[0] = False
                messages[0]["content"] += ("\nTools are unavailable for this model. To run a command, reply with "
                                           "exactly one ```bash block``` and wait for its output.")
                print(c("33", "(this model has no tool support; using command blocks instead)"))
                continue
            raise
        calls = msg.get("tool_calls") or []
        content = msg.get("content") or ""
        messages.append({k: v for k, v in msg.items() if k in ("role", "content", "tool_calls")})
        if calls:
            if content.strip() and not quiet:
                print(c("2", content.strip()))
            for call in calls:
                fn = call.get("function", {})
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                    if isinstance(args, str):
                        args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
                if not quiet:
                    shown = args.get("command") or args.get("path") or args.get("query") or args.get("url") or ""
                    print(c("36", f"● {name}") + (f" {shown}" if shown else ""))
                result = tools.call(name, args)
                if not quiet and name == "run_command" and "exit_code" in result:
                    preview = (result.get("stdout") or result.get("stderr") or "").strip().splitlines()[-6:]
                    for line in preview:
                        print(c("2", "  │ " + line[:160]))
                messages.append({"role": "tool", "tool_call_id": call.get("id", name),
                                 "name": name, "content": json.dumps(result, ensure_ascii=False)[:24000]})
            continue
        if not use_tools[0]:
            m = FENCE.search(content)
            if m:
                if not quiet:
                    print(c("2", content.strip()))
                res = tools.call("run_command", {"command": m.group(1).strip()})
                messages.append({"role": "user", "content": "Command output:\n" + json.dumps(res)[:12000]})
                continue
        return content
    return "(stopped after too many steps)"


def interactive(client, tools, messages, use_tools):
    print(c("1;32", "Orchard Agent") + c("2", f"  {client.provider}:{client.model}  mode={tools.mode}"))
    print(c("2", "Ask anything, or give a task. Commands: /mode ask|auto|yolo, /model NAME, /clear, /log, /exit"))
    while True:
        try:
            line = input(c("1;32", "\n› ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not line:
            continue
        if line in ("/exit", "/quit", "exit", "quit"):
            return
        if line == "/clear":
            del messages[1:]
            print("Conversation cleared.")
            continue
        if line == "/log":
            subprocess.run(["tail", "-n", "20", str(LOG_FILE)])
            continue
        if line.startswith("/mode"):
            parts = line.split()
            if len(parts) == 2 and parts[1] in ("ask", "auto", "yolo"):
                tools.mode = parts[1]
            print(f"mode={tools.mode}")
            continue
        if line.startswith("/model"):
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                client.model = parts[1]
            print(f"model={client.model}")
            continue
        messages.append({"role": "user", "content": line})
        log_event("prompt", text=line[:2000], provider=client.provider, model=client.model)
        try:
            answer = agent_turn(client, tools, messages, use_tools)
            print("\n" + answer.strip())
            log_event("answer", text=answer[:4000])
        except ApiError as e:
            print(c("31", f"error: {e}"))
            log_event("error", error=str(e))
        except KeyboardInterrupt:
            print(c("33", "\n(interrupted)"))


def cmd_key(provider):
    p = PROVIDERS.get(provider)
    if not p or not p["key_env"]:
        sys.exit(f"{provider} does not use an API key")
    print(f"{provider}: {p['note']}")
    import getpass
    key = getpass.getpass(f"Paste {p['key_env']} (input hidden): ").strip()
    if not key:
        sys.exit("no key entered")
    CONF_DIR.mkdir(parents=True, exist_ok=True)
    lines = [l for l in (KEYS_FILE.read_text().splitlines() if KEYS_FILE.exists() else [])
             if not l.startswith(p["key_env"] + "=")]
    lines.append(f"{p['key_env']}={key}")
    KEYS_FILE.write_text("\n".join(lines) + "\n")
    os.chmod(KEYS_FILE, 0o600)
    print(f"Saved to {KEYS_FILE} (readable only by you).")


def main():
    load_keys()
    cfg = load_config()
    ap = argparse.ArgumentParser(prog="orchard-agent", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="Subcommands: providers | key PROVIDER | use PROVIDER [MODEL] | "
                                        "config KEY VALUE | log")
    ap.add_argument("prompt", nargs="*", help="task or question; empty starts an interactive session")
    ap.add_argument("-p", "--provider", default=cfg["provider"])
    ap.add_argument("-m", "--model", default=None)
    ap.add_argument("--mode", choices=["ask", "auto", "yolo"], default=cfg["mode"])
    ap.add_argument("--auto", action="store_const", const="auto", dest="mode")
    ap.add_argument("--yolo", action="store_const", const="yolo", dest="mode")
    ap.add_argument("--gui", action="store_true", help="ask approvals in dialogs (voice, launcher)")
    ap.add_argument("--quiet", action="store_true", help="print only the final answer")
    ap.add_argument("--no-tools", action="store_true", help="plain chat")
    args = ap.parse_args()

    words = args.prompt
    if words and words[0] == "providers":
        for name, p in PROVIDERS.items():
            have = "local" if not p["key_env"] else ("key set" if os.environ.get(p["key_env"]) else "no key")
            mark = "*" if name == cfg["provider"] else " "
            print(f"{mark} {name:12s} {have:8s} {p['default_model']:42s} {p['note']}")
        return 0
    if words and words[0] == "key" and len(words) == 2:
        cmd_key(words[1])
        return 0
    if words and words[0] == "use" and len(words) in (2, 3):
        if words[1] not in PROVIDERS:
            sys.exit(f"unknown provider {words[1]}")
        cfg["provider"] = words[1]
        cfg["model"] = words[2] if len(words) == 3 else ""
        save_config(cfg)
        print(f"Using {cfg['provider']}:{cfg['model'] or PROVIDERS[cfg['provider']]['default_model']}")
        return 0
    if words and words[0] == "config" and len(words) == 3:
        cfg[words[1]] = words[2]
        save_config(cfg)
        print(f"{words[1]} = {words[2]}")
        return 0
    if words and words[0] == "log":
        os.execvp("tail", ["tail", "-n", "50", str(LOG_FILE)])

    model = args.model or (cfg["model"] if args.provider == cfg["provider"] else "")
    try:
        client = Client(args.provider, model,
                        cfg.get("custom_base_url") if args.provider == "custom" else None)
    except ApiError as e:
        print(c("31", f"orchard-agent: {e}"), file=sys.stderr)
        return 2
    gui = args.gui or (not sys.stdin.isatty() and bool(os.environ.get("DISPLAY"))
                       and shutil.which("zenity") is not None)
    tools = Tools(args.mode, make_approver(gui))
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(
        cwd=os.getcwd(), user=os.environ.get("USER", "user"), date=dt.date.today().isoformat())}]
    use_tools = [not args.no_tools]

    if not words:
        interactive(client, tools, messages, use_tools)
        return 0
    prompt = " ".join(words)
    messages.append({"role": "user", "content": prompt})
    log_event("prompt", text=prompt[:2000], provider=client.provider, model=client.model)
    try:
        answer = agent_turn(client, tools, messages, use_tools, quiet=args.quiet)
    except ApiError as e:
        print(c("31", f"orchard-agent: {e}"), file=sys.stderr)
        log_event("error", error=str(e))
        return 1
    log_event("answer", text=answer[:4000])
    print(answer.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
