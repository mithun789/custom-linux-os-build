#!/usr/bin/env python3
"""Orchard Voice: offline speech control for Orchard Agent.

  orchard-voice setup        download the speech engine (Vosk, ~50 MB, once)
  orchard-voice ptt          push-to-talk: listen once, act, speak the answer (Super+V)
  orchard-voice listen       hands-free: say "Jarvis" or "Orchard", then your request
  orchard-voice say TEXT     speak text
  orchard-voice test         record 5 seconds and print what was heard

Speech recognition runs on this computer (Vosk). Answers come from Orchard
Agent, so the voice assistant can run commands, open apps and search the web.
Commands that change the system still ask for approval in a dialog.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

DATA = Path.home() / ".local" / "share" / "orchard" / "voice"
VENV = DATA / "venv"
MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
MODEL = DATA / MODEL_NAME
WAKE = ("jarvis", "orchard", "hey orchard", "ok orchard")
RATE = 16000

# Quick local intents that do not need the AI model.
APPS = {
    "browser": "epiphany-browser", "web": "epiphany-browser", "files": "thunar", "file manager": "thunar",
    "terminal": "xfce4-terminal", "settings": "xfce4-settings-manager", "music": "rhythmbox",
    "software": "gnome-software", "store": "gnome-software", "calculator": "gnome-calculator",
    "text editor": "mousepad", "editor": "mousepad", "videos": "celluloid", "task manager": "xfce4-taskmanager",
}


def say(text):
    text = re.sub(r"```.*?```", " I showed the code on screen. ", text, flags=re.S)
    text = re.sub(r"[*_#`>|]", " ", text)[:1200]
    if shutil.which("espeak-ng"):
        subprocess.run(["espeak-ng", "-v", "en-us+f3", "-s", "165", text],
                       stderr=subprocess.DEVNULL)


def notify(title, body=""):
    subprocess.run(["notify-send", "-i", "audio-input-microphone", "-t", "4000", title, body],
                   stderr=subprocess.DEVNULL)


def ensure_engine():
    py = VENV / "bin" / "python3"
    if py.exists() and MODEL.exists() and os.environ.get("ORCHARD_VOICE_CHILD") != "1":
        # Re-run inside the venv that has vosk.
        os.environ["ORCHARD_VOICE_CHILD"] = "1"
        os.execv(str(py), [str(py), __file__] + sys.argv[1:])
    try:
        import vosk  # noqa: F401
        return True
    except ImportError:
        return False


def setup():
    DATA.mkdir(parents=True, exist_ok=True)
    if not (VENV / "bin" / "python3").exists():
        print("==> Creating Python environment")
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    print("==> Installing the Vosk speech engine")
    subprocess.run([str(VENV / "bin" / "pip"), "install", "-q", "--upgrade", "vosk"], check=True)
    if not MODEL.exists():
        print(f"==> Downloading speech model ({MODEL_NAME}, about 40 MB)")
        tmp = DATA / "model.zip"
        urllib.request.urlretrieve(MODEL_URL, tmp)
        with zipfile.ZipFile(tmp) as z:
            z.extractall(DATA)
        tmp.unlink()
    print("==> Voice assistant ready. Press Super+V and speak.")
    say("Voice assistant ready.")


def recorder():
    return subprocess.Popen(["arecord", "-q", "-f", "S16_LE", "-r", str(RATE), "-c", "1", "-t", "raw"],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)


def recognizer():
    from vosk import KaldiRecognizer, Model, SetLogLevel
    SetLogLevel(-1)
    return KaldiRecognizer(Model(str(MODEL)), RATE)


def listen_once(max_seconds=10, silence_after=1.3):
    """Record until the speaker pauses; return the recognized text."""
    rec = recognizer()
    proc = recorder()
    start = time.time()
    last_voice = None
    text = ""
    try:
        while time.time() - start < max_seconds:
            data = proc.stdout.read(4000)
            if not data:
                break
            if rec.AcceptWaveform(data):
                text += " " + json.loads(rec.Result()).get("text", "")
                last_voice = time.time()
            elif json.loads(rec.PartialResult()).get("partial"):
                last_voice = time.time()
            if last_voice and time.time() - last_voice > silence_after:
                break
    finally:
        proc.terminate()
    text += " " + json.loads(rec.FinalResult()).get("text", "")
    return text.strip()


def handle(text):
    t = text.lower().strip()
    for w in WAKE:
        if t.startswith(w):
            t = t[len(w):].strip(" ,")
    if not t:
        return
    m = re.match(r"(open|launch|start) (the )?(.+)", t)
    if m and m.group(3) in APPS:
        subprocess.Popen([APPS[m.group(3)]], start_new_session=True)
        say(f"Opening {m.group(3)}")
        return
    if t in ("dark mode", "switch to dark mode"):
        subprocess.run(["orchard-appearance", "dark"])
        say("Dark mode on")
        return
    if t in ("light mode", "switch to light mode"):
        subprocess.run(["orchard-appearance", "light"])
        say("Light mode on")
        return
    if t in ("lock", "lock the screen", "lock screen"):
        subprocess.run(["xflock4"])
        return
    notify("Orchard Voice", f"“{t}”")
    res = subprocess.run(["orchard-agent", "--gui", "--auto", "--quiet", t + " (Answer in 1-3 short spoken sentences.)"],
                         capture_output=True, text=True, stdin=subprocess.DEVNULL)
    answer = (res.stdout or res.stderr).strip() or "Sorry, I had no answer."
    notify("Orchard Voice", answer[:300])
    say(answer)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "setup":
        return setup()
    if cmd == "setup-gui":
        if MODEL.exists() and (VENV / "bin" / "python3").exists():
            subprocess.Popen(["zenity", "--info", "--title=Orchard Voice", "--width=420",
                              "--text=Voice assistant is ready.\n\nPress Super+V and speak, for example:\n"
                                    "“open the browser”, “what is using my memory?”, “dark mode”."])
            return 0
        os.execvp("xfce4-terminal", ["xfce4-terminal", "--hold", "-T", "Orchard Voice setup", "-x",
                                     "orchard-voice", "setup"])
    if cmd == "say":
        return say(" ".join(sys.argv[2:]))
    if cmd in ("help", "-h", "--help"):
        print(__doc__)
        return 0
    if not ensure_engine():
        notify("Orchard Voice", "Run: orchard-voice setup")
        print("The speech engine is not installed. Run: orchard-voice setup")
        return 1
    if cmd == "test":
        print("Speak now...")
        print("Heard:", listen_once(max_seconds=5) or "(nothing)")
        return 0
    if cmd == "ptt":
        lock = DATA / "ptt.lock"
        if lock.exists() and time.time() - lock.stat().st_mtime < 30:
            return 0
        lock.touch()
        try:
            subprocess.run(["canberra-gtk-play", "-i", "message"], stderr=subprocess.DEVNULL)
            notify("Listening…", "Speak your request")
            text = listen_once()
            if text:
                handle(text)
            else:
                notify("Orchard Voice", "I did not hear anything.")
        finally:
            lock.unlink(missing_ok=True)
        return 0
    if cmd == "listen":
        print("Hands-free mode. Say 'Jarvis' or 'Orchard' followed by your request. Ctrl+C to stop.")
        while True:
            text = listen_once(max_seconds=15, silence_after=1.0)
            if any(text.lower().startswith(w) for w in WAKE):
                print("Heard:", text)
                handle(text)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main() or 0)
