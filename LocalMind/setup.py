#!/usr/bin/env python3
"""
LocalMind AI — Unified Setup & Launcher
=======================================
Plug-and-play USB AI launcher. Cross-platform: macOS, Windows, Linux.

What this does:
  1. Checks / installs Python
  2. Checks / downloads AI models
  3. Starts Ollama AI engine (bundled binary)
  4. Starts web dashboard
  5. Opens browser
  6. Lets you choose: Local Chat (web) or OpenClaw (terminal)

Run:  python3 setup.py
"""

import os
import sys
import json
import time
import shutil
import socket
import signal
import webbrowser
import subprocess
import urllib.request
from pathlib import Path

# ── Platform ──────────────────────────────────────────────
IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")
PLATFORM = "windows" if IS_WIN else "macos" if IS_MAC else "linux"

# ── Paths ────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()

# Repo mode: setup.py is at repo root, LocalMind/ is a subdir
# USB mode: setup.py is inside LocalMind/ directory
if (SCRIPT_DIR / "LocalMind").is_dir():
    USB_ROOT = SCRIPT_DIR / "LocalMind"
else:
    USB_ROOT = SCRIPT_DIR

LAUNCHER_DIR = USB_ROOT / "launcher"
OLLAMA_DIR = USB_ROOT / "ollama"
MODELS_DIR = USB_ROOT / "models"
DASHBOARD_DIR = USB_ROOT / "dashboard"
DATA_DIR = USB_ROOT / "data"
OPENCLAW_DIR = USB_ROOT / "openclaw"
MANIFEST_FILE = USB_ROOT / ".localmind" / "manifest.json"

OLLAMA_PORT = 11434
DASHBOARD_PORT = 3000

# ── Recommended Models ───────────────────────────────────
# Models that run on 8GB RAM average computers
RECOMMENDED_MODELS = [
    {"name": "gemma4:e4b", "size_gb": 2.6, "desc": "Google DeepMind's latest. Efficient, runs anywhere."},
    {"name": "qwen2.5:7b", "size_gb": 4.7, "desc": "Strong all-purpose. Great coding & reasoning."},
    {"name": "mistral:7b", "size_gb": 4.1, "desc": "Fast, reliable, well-tested."},
]

# ── Colors ───────────────────────────────────────────────
C = {
    "cyan": "\033[36m", "green": "\033[32m", "yellow": "\033[33m",
    "red": "\033[31m", "blue": "\033[34m", "dim": "\033[90m",
    "bold": "\033[1m", "reset": "\033[0m",
}
if IS_WIN:
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except:
        C = {k: "" for k in C}

def p(msg, lvl="info"):
    pre = {"info": "[i]", "ok": "[✓]", "warn": "[!]", "error": "[✗]", "ask": "[?]"}
    col = {"info": C["cyan"], "ok": C["green"], "warn": C["yellow"],
           "error": C["red"], "ask": C["blue"]}
    print(f"{col.get(lvl, '')}{pre.get(lvl, '[i]')}{C['reset']} {msg}")

def header():
    print()
    print(f"{C['cyan']}{C['bold']}    ╔═══════════════════════════════════════════════════════════╗{C['reset']}")
    print(f"{C['cyan']}{C['bold']}    ║                                                           ║{C['reset']}")
    print(f"{C['cyan']}{C['bold']}    ║              🤖  LOCALMIND AI - USB LAUNCHER               ║{C['reset']}")
    print(f"{C['cyan']}{C['bold']}    ║                                                           ║{C['reset']}")
    print(f"{C['cyan']}{C['bold']}    ║      Run AI models completely offline - No internet       ║{C['reset']}")
    print(f"{C['cyan']}{C['bold']}    ║                                                           ║{C['reset']}")
    print(f"{C['cyan']}{C['bold']}    ╚═══════════════════════════════════════════════════════════╝{C['reset']}")
    print()

# ── Utilities ────────────────────────────────────────────
def find_free_port(start=11435, end=11500):
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.bind(("127.0.0.1", port))
                return port
        except:
            continue
    return None

def is_port_free(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(("127.0.0.1", port))
            return True
    except:
        return False

def wait_for_url(url, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=2)
            return True
        except:
            time.sleep(0.5)
    return False

def run_bg(cmd, env=None, cwd=None, hide=True):
    kw = {"env": env, "cwd": str(cwd) if cwd else None}
    if IS_WIN:
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        # Set DLL search path so Ollama can find its CPU backend DLLs
        import ctypes
        try:
            dll_path = str(OLLAMA_DIR / "windows" / "lib")
            k32 = ctypes.CDLL("kernel32.dll")
            k32.AddDllDirectory(dll_path)
            env = dict(env or os.environ)
            env["PATH"] = dll_path + os.pathsep + env.get("PATH", "")
            kw["env"] = env
        except Exception:
            pass  # Non-critical if this fails
    if hide:
        kw["stdout"] = subprocess.DEVNULL
        kw["stderr"] = subprocess.DEVNULL
    return subprocess.Popen(cmd, **kw)

def kill_proc(proc):
    if not proc:
        return
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        try:
            proc.kill()
        except:
            pass

def ask(prompt, default=""):
    try:
        r = input(f"{C['blue']}[?]{C['reset']} {prompt} ").strip()
        return r if r else default
    except (EOFError, KeyboardInterrupt):
        return default

def confirm(prompt, default=True):
    d = "Y/n" if default else "y/N"
    r = ask(f"{prompt} ({d})").lower()
    if not r:
        return default
    return r in ("y", "yes")

# ── Step 1: Python Check ─────────────────────────────────
def check_python():
    p("Checking Python...", "info")
    ver = sys.version_info
    if ver.major >= 3 and ver.minor >= 9:
        p(f"Python {ver.major}.{ver.minor}.{ver.micro} — OK", "ok")
        return sys.executable

    py3 = shutil.which("python3")
    if py3:
        try:
            out = subprocess.run([py3, "--version"], capture_output=True, text=True, timeout=5)
            p(f"Found {out.stdout.strip()} — OK", "ok")
            return py3
        except:
            pass

    p("Python 3.9+ is required.", "error")
    if IS_MAC:
        print("\n   Install with:  brew install python3")
        print("   Or download:   https://www.python.org/downloads/")
    elif IS_WIN:
        print("\n   The installer will try to download Python automatically...")
        bat = LAUNCHER_DIR / "install-python.bat"
        if bat.exists():
            p("Running Python installer...")
            subprocess.run([str(bat)], shell=True)
            py = shutil.which("python") or shutil.which("python3")
            if py:
                return py
        else:
            print("   Download from: https://www.python.org/downloads/")
    else:
        print("   sudo apt install python3 python3-pip")
    sys.exit(1)

# ── Step 2: Ollama Binary ────────────────────────────────
def find_ollama():
    p("Finding Ollama AI engine...", "info")

    candidates = [
        OLLAMA_DIR / "ollama" if not IS_WIN else None,
        OLLAMA_DIR / "macos" / "ollama" if IS_MAC else None,
        OLLAMA_DIR / "windows" / "ollama.exe" if IS_WIN else None,
        OLLAMA_DIR / "linux" / "ollama" if IS_LINUX else None,
    ]

    for c in candidates:
        if c and c.exists():
            p(f"Found: {c.name}", "ok")
            return c

    system = shutil.which("ollama")
    if system:
        p(f"Using system Ollama: {system}", "warn")
        return Path(system)

    p("Ollama binary not found on USB.", "error")
    print("   Expected at one of:")
    for c in candidates:
        if c:
            print(f"   - {c}")
    sys.exit(1)

# ── Step 3: Model Download ───────────────────────────────
def get_installed_models(ollama_bin):
    try:
        env = os.environ.copy()
        env["OLLAMA_MODELS"] = str(MODELS_DIR)
        env["HOME"] = str(DATA_DIR)
        out = subprocess.run(
            [str(ollama_bin), "list"],
            capture_output=True, text=True, timeout=10, env=env
        )
        lines = [l.strip() for l in out.stdout.splitlines() if l.strip() and not l.startswith("NAME")]
        return lines
    except:
        return []

def download_model(ollama_bin, model_name):
    p(f"Downloading {model_name}...", "info")
    env = os.environ.copy()
    env["OLLAMA_MODELS"] = str(MODELS_DIR)
    env["HOME"] = str(DATA_DIR)

    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    proc = subprocess.Popen(
        [str(ollama_bin), "pull", model_name],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    i = 0
    while proc.poll() is None:
        time.sleep(0.5)
        i = (i + 1) % len(spinner)
        print(f"\r   {spinner[i]} Downloading {model_name}...", end="", flush=True)

    print()
    if proc.returncode == 0:
        p(f"{model_name} ready!", "ok")
        return True
    else:
        p(f"Failed to download {model_name}", "error")
        return False

def manage_models(ollama_bin):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    installed = get_installed_models(ollama_bin)
    if installed:
        p(f"{len(installed)} model(s) already installed:", "ok")
        for m in installed:
            print(f"   • {m}")
        print()
        return

    p("No AI models found on USB.", "warn")
    print()
    print(f"{C['bold']}   Recommended models to download:{C['reset']}")
    total = 0
    for i, m in enumerate(RECOMMENDED_MODELS, 1):
        print(f"   {i}) {C['cyan']}{m['name']}{C['reset']} ({m['size_gb']} GB) — {m['desc']}")
        total += m["size_gb"]
    print(f"\n   Total: ~{round(total, 1)} GB")
    print()

    if not confirm("Download recommended models now?", default=True):
        p("Skipping model download. Run 'ollama pull <model>' later.", "warn")
        return

    print()
    for m in RECOMMENDED_MODELS:
        if not download_model(ollama_bin, m["name"]):
            p(f"Skipping {m['name']}", "warn")
        print()

    installed = get_installed_models(ollama_bin)
    p(f"{len(installed)} model(s) now installed.", "ok")


# ── Step 4: Start Services ─────────────────────────────────
class LocalMindLauncher:
    def __init__(self):
        self.ollama_bin = None
        self.ollama_proc = None
        self.dashboard_proc = None
        self.running = False
        self.ollama_port = OLLAMA_PORT

    def _cleanup_stale_runners(self):
        """Kill stale Ollama runner processes from previous sessions."""
        try:
            if IS_MAC or IS_LINUX:
                result = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    if "ollama runner" in line and "minimax-m2.7:cloud" not in line:
                        parts = line.split()
                        if len(parts) > 1:
                            pid = parts[1]
                            try:
                                subprocess.run(["kill", "-9", pid], capture_output=True, timeout=2)
                                p(f"Cleaned up stale runner PID {pid}", "warn")
                            except:
                                pass
            elif IS_WIN:
                subprocess.run(["taskkill", "/f", "/im", "ollama.exe"], capture_output=True, timeout=5)
        except Exception as e:
            pass  # Best effort

    def start_ollama(self):
        p("Starting AI engine...", "info")

        # Clean any stale runners from previous sessions first
        self._cleanup_stale_runners()

        # Check if default port 11434 is already in use by another Ollama
        if self.ollama_port == 11434 and not is_port_free(11434):
            p("Port 11434 is in use — checking for conflict...", "warn")
            try:
                req = urllib.request.Request(f"http://127.0.0.1:11434/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    existing_models = json.loads(resp.read()).get("models", [])
                    if existing_models:
                        # Check if USB models are available on this Ollama
                        usb_model_names = set()
                        try:
                            env = os.environ.copy()
                            env["OLLAMA_MODELS"] = str(MODELS_DIR)
                            env["HOME"] = str(DATA_DIR)
                            out = subprocess.run(
                                [str(self.ollama_bin), "list"],
                                capture_output=True, text=True, timeout=10, env=env
                            )
                            for line in out.stdout.splitlines():
                                if line.strip() and not line.startswith("NAME"):
                                    usb_model_names.add(line.strip().split()[0])
                        except:
                            pass

                        # If existing Ollama doesn't have our USB models, use alternate port
                        if not usb_model_names:
                            p("System Ollama detected but USB models not available.", "warn")
                            p("Starting USB Ollama on alternate port...", "warn")
                            alt = find_free_port(11435, 11500)
                            if alt:
                                self.ollama_port = alt
                                p(f"Using port {alt}", "warn")
                            else:
                                p("Could not find free port.", "error")
                                return False
                        else:
                            # Use the existing Ollama (it already has our models loaded)
                            p(f"Using existing Ollama on port 11434 ({len(existing_models)} model(s))", "ok")
                            return True
            except Exception as e:
                p(f"Port 11434 in use but not responding: {e}", "warn")
                # Try alternate port anyway
                alt = find_free_port(11435, 11500)
                if alt:
                    self.ollama_port = alt
                    p(f"Using alternate port {alt}", "warn")

        env = os.environ.copy()
        env["OLLAMA_MODELS"] = str(MODELS_DIR)
        env["OLLAMA_HOST"] = "127.0.0.1"
        env["OLLAMA_PORT"] = str(self.ollama_port)
        env["OLLAMA_ORIGINS"] = "*"
        env["HOME"] = str(DATA_DIR)

        self.ollama_proc = run_bg(
            [str(self.ollama_bin), "serve"],
            env=env,
        )

        p("Waiting for AI engine to start...", "info")
        url = f"http://127.0.0.1:{self.ollama_port}/api/tags"
        if wait_for_url(url, timeout=180):
            p("AI engine is running!", "ok")
            return True
        else:
            p("AI engine failed to start.", "error")
            return False

    def start_dashboard(self):
        p("Starting dashboard...", "info")

        server_py = DASHBOARD_DIR / "server.py"
        if not server_py.exists():
            p(f"Dashboard not found: {server_py}", "error")
            return False

        # Let server.py find its own port (it does this)
        env = os.environ.copy()
        env["LOCALMIND_ROOT"] = str(USB_ROOT)
        env["LOCALMIND_DATA"] = str(DATA_DIR)
        env["LOCALMIND_PORT"] = str(DASHBOARD_PORT)
        env["LOCALMIND_OLLAMA_HOST"] = "127.0.0.1"
        env["LOCALMIND_OLLAMA_PORT"] = str(self.ollama_port)
        env["OLLAMA_HOST"] = "127.0.0.1"
        env["OLLAMA_PORT"] = str(self.ollama_port)

        self.dashboard_proc = run_bg(
            [sys.executable, str(server_py)],
            env=env,
            cwd=str(DASHBOARD_DIR),
        )

        time.sleep(2)

        # Find actual port
        for port in range(DASHBOARD_PORT, DASHBOARD_PORT + 20):
            if not is_port_free(port):
                self.dashboard_port = port
                break
        else:
            self.dashboard_port = DASHBOARD_PORT

        p(f"Dashboard running at http://localhost:{self.dashboard_port}", "ok")
        return True

    def open_browser(self):
        url = f"http://localhost:{self.dashboard_port}"
        p(f"Opening browser: {url}", "info")
        try:
            webbrowser.open(url)
        except:
            print(f"   Please open: {url}")

    def show_menu(self, auto=False):
        url = f"http://localhost:{self.dashboard_port}"
        print()
        print(f"{C['green']}{C['bold']}═══════════════════════════════════════════════════════════{C['reset']}")
        print(f"{C['green']}   ✅ LocalMind is running!{C['reset']}")
        print()
        print(f"{C['green']}   📊 Dashboard:  {url}{C['reset']}")
        print(f"{C['green']}   🤖 Ollama API: http://localhost:{self.ollama_port}{C['reset']}")
        print()

        # Auto-mode (beginner): skip menu, just open Local Chat
        if auto:
            print(f"{C['cyan']}   🔗 Local Chat is open in your browser!{C['reset']}")
            print()
            print(f"{C['dim']}   To use OpenClaw terminal chat, open a terminal and run:{C['reset']}")
            if IS_WIN:
                print(f"{C['dim']}      openclaw chat{C['reset']}")
            else:
                print(f"{C['dim']}      openclaw chat{C['reset']}")
            print()
            print(f"   Press Ctrl+C to stop LocalMind.")
            return

        print(f"{C['yellow']}   Choose your interface:{C['reset']}")
        print()
        print(f"   {C['cyan']}1){C['reset']} Local Chat (web browser) — Already open")
        print(f"   {C['cyan']}2){C['reset']} OpenClaw Chat (terminal AI assistant)")
        print(f"   {C['cyan']}3){C['reset']} Continue without chat")
        print()
        print(f"{C['green']}{C['bold']}═══════════════════════════════════════════════════════════{C['reset']}")
        print()

        choice = ask("Enter choice (1-3):", "1")

        if choice == "2":
            self.start_openclaw()
        elif choice == "3":
            print(f"\n   Dashboard running at {url}")
            print("   Press Ctrl+C to stop.")
        else:
            print(f"\n   ✅ Dashboard is open in your browser!")
            print("   Press Ctrl+C to stop LocalMind.")

    def start_openclaw(self):
        print()
        p("Starting OpenClaw Chat...", "info")

        node = shutil.which("node")
        if not node:
            p("Node.js not found.", "warn")
            if IS_MAC and shutil.which("brew"):
                p("Installing Node.js via Homebrew...")
                subprocess.run(["brew", "install", "node"])
                node = shutil.which("node")
            else:
                print("   Install from: https://nodejs.org/")
                return

        if OPENCLAW_DIR.exists() and (OPENCLAW_DIR / "openclaw.mjs").exists():
            p("Found OpenClaw on USB.", "ok")
            oc_cmd = [node, str(OPENCLAW_DIR / "openclaw.mjs"), "chat"]
        elif shutil.which("openclaw"):
            p("Using system OpenClaw.", "ok")
            oc_cmd = ["openclaw", "chat"]
        else:
            p("OpenClaw not found.", "error")
            return

        try:
            subprocess.run(oc_cmd)
        except KeyboardInterrupt:
            pass

    def shutdown(self, signum=None, frame=None):
        if not self.running:
            return
        self.running = False
        print()
        p("Shutting down LocalMind...", "warn")
        kill_proc(self.dashboard_proc)
        kill_proc(self.ollama_proc)
        p("Goodbye! 👋", "ok")
        sys.exit(0)

    def run(self):
        header()

        python_exe = check_python()
        if python_exe != sys.executable:
            os.execv(python_exe, [python_exe, str(Path(__file__).resolve())])

        self.ollama_bin = find_ollama()
        manage_models(self.ollama_bin)

        print()
        if not self.start_ollama():
            sys.exit(1)

        if not self.start_dashboard():
            p("Dashboard failed, but AI engine is running.", "warn")

        self.open_browser()
        self.show_menu(auto=getattr(self, 'auto_mode', False))

        self.running = True
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        if IS_WIN:
            try:
                signal.signal(signal.SIGBREAK, self.shutdown)
            except:
                pass

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()

# ── Entry ──────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        # Auto mode (beginner/autorun): skip menu, open Local Chat directly
        auto_mode = "--auto" in sys.argv or "-y" in sys.argv
        launcher = LocalMindLauncher()
        launcher.auto_mode = auto_mode
        launcher.run()
    except KeyboardInterrupt:
        print(f"\n{C['yellow']}LocalMind stopped.{C['reset']}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{C['red']}[✗] Fatal error: {e}{C['reset']}")
        raise
