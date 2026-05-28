#!/usr/bin/env python3
"""
LocalMind AI — Unified Setup & Launcher
=======================================
Plug-and-play USB AI launcher. Cross-platform: macOS, Windows, Linux.

What this does:
  1. Detects system RAM → selects appropriate model tier
  2. Checks / installs Python
  3. Starts Ollama AI engine (bundled binary)
  4. Starts web dashboard with RAM-tier-appropriate models
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

# ── RAM Detection & Model Tiers ───────────────────────────
def get_system_ram_gb():
    """Detect total system RAM in GB."""
    try:
        if IS_MAC or IS_LINUX:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=5
            )
            return int(result.stdout.strip()) / (1024**3)
        elif IS_WIN:
            result = subprocess.run(
                ["powershell", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"],
                capture_output=True, text=True, timeout=5
            )
            return int(result.stdout.strip().replace(",", "")) / (1024**3)
    except Exception:
        pass
    # Fallback via os.sysconf
    try:
        return int(os.sysconf("SC_PHYSMEM")) / (1024**3)
    except Exception:
        return None

RAM_TIER_16GB = 15.5  # machines with 16GB+ get premium models
RAM_TIER_8GB = 7.5    # machines with 8GB+ get standard models

def get_ram_tier():
    """Return '16gb' or '8gb' based on detected RAM."""
    ram = get_system_ram_gb()
    if ram is None:
        return "8gb"  # safe default
    if ram >= RAM_TIER_16GB:
        return "16gb"
    return "8gb"

# ── Model Tiers ───────────────────────────────────────────
# All models that can be on the USB
ALL_MODELS = [
    # 8GB tier — runs on most laptops
    {"name": "qwen2.5:7b",    "size_gb": 4.7, "tier": "8gb",
     "desc": "Fast all-purpose. Great coding, reasoning, and general chat. ⚡ FASTEST"},
    {"name": "gemma4:e4b",    "size_gb": 2.6, "tier": "8gb",
     "desc": "Efficient and smart. Good for creative writing and quick tasks."},
    {"name": "qwen2.5-coder:7b", "size_gb": 4.8, "tier": "8gb",
     "desc": "Code-specialized. Built for programming and debugging."},
    # 16GB tier — needs more headroom
    {"name": "qwen3:8b",        "size_gb": 5.5, "tier": "16gb",
     "desc": "Latest Qwen. Smarter chat, better reasoning."},
    {"name": "qwen2.5-coder:14b", "size_gb": 9.0, "tier": "16gb",
     "desc": "Premium coding. 14B params for complex programming tasks."},
    # mistral:7b goes in BOTH tiers — solid fallback, good speed
    {"name": "mistral:7b",       "size_gb": 4.1, "tier": "both",
     "desc": "Reliable fallback. Good speed and quality on all machines."},
]

def get_models_for_tier(tier):
    """Return list of model names for the given RAM tier."""
    return [m["name"] for m in ALL_MODELS if m["tier"] == tier or m["tier"] == "both"]

# Default/fastest model per tier (used by preload)
TIER_FASTEST = {
    "8gb":  "qwen2.5:7b",
    "16gb": "qwen2.5:7b",
}

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

def header(tier=None):
    tier_label = ""
    if tier == "16gb":
        tier_label = f"{C['yellow']} ⚡ 16GB TIER{C['reset']}"
    elif tier == "8gb":
        tier_label = f"{C['cyan']} ◆ 8GB TIER{C['reset']}"
    print()
    if tier_label:
        print(f"   {tier_label}")
        print()
    print(f"{C['cyan']}{C['bold']}    ╔═══════════════════════════════════════════════════════════╗{C['reset']}")
    print(f"{C['cyan']}{C['bold']}    ║                                                           ║{C['reset']}")
    print(f"{C['cyan']}{C['bold']}    ║              🤖  LOCALMIND AI - USB LAUNCHER               ║{C['reset']}")
    print(f"{C['cyan']}{C['bold']}    ║                                                           ║{C['reset']}")
    print(f"{C['cyan']}{C['bold']}    ║      Run AI models completely offline - No internet       ║{C['reset']}")
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
        import ctypes
        try:
            dll_path = str(OLLAMA_DIR / "windows" / "lib")
            k32 = ctypes.CDLL("kernel32.dll")
            k32.AddDllDirectory(dll_path)
            env = dict(env or os.environ)
            env["PATH"] = dll_path + os.pathsep + env.get("PATH", "")
            kw["env"] = env
        except Exception:
            pass
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

# ── Step 3: Model Management ─────────────────────────────
def get_installed_models(ollama_bin):
    try:
        env = os.environ.copy()
        env["OLLAMA_MODELS"] = str(MODELS_DIR)
        env["HOME"] = str(DATA_DIR)
        out = subprocess.run(
            [str(ollama_bin), "list"],
            capture_output=True, text=True, timeout=10, env=env
        )
        lines = []
        for l in out.stdout.splitlines():
            l = l.strip()
            if not l or l.startswith("NAME"):
                continue
            # Extract just the model name (first whitespace-delimited field)
            model_name = l.split()[0] if l.split() else ""
            if model_name:
                lines.append(model_name)
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

def manage_models(ollama_bin, ram_tier):
    """Ensure models for the detected RAM tier are installed."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    tier_models = get_models_for_tier(ram_tier)
    installed = get_installed_models(ollama_bin)

    # Check which tier models are missing
    missing = [m for m in tier_models if m not in installed]
    present = [m for m in tier_models if m in installed]

    if present:
        p(f"{len(present)}/{len(tier_models)} {ram_tier.upper()} models already on USB:", "ok")
        for m in present:
            print(f"   • {m}")
    else:
        p(f"No {ram_tier.upper()} models found on USB.", "warn")

    if missing:
        print()
        p(f"Models to download for {ram_tier.upper()} tier:", "info")
        tier_all_models = [m for m in ALL_MODELS if m["tier"] == ram_tier]
        total_gb = sum(m["size_gb"] for m in tier_all_models)
        for m_def in tier_all_models:
            mark = " (missing)" if m_def["name"] in missing else ""
            print(f"   • {m_def['name']} ({m_def['size_gb']} GB){mark}")
        print(f"   Total: ~{round(total_gb, 1)} GB")
        print()
        if confirm("Download now?", default=True):
            for m_name in missing:
                download_model(ollama_bin, m_name)
                print()

    # Final status
    installed = get_installed_models(ollama_bin)
    tier_now = [m for m in installed if m in tier_models]
    p(f"{len(tier_now)} {ram_tier.upper()} models ready.", "ok")

# ── Step 4: Start Services ─────────────────────────────────
class LocalMindLauncher:
    def __init__(self, ram_tier="8gb"):
        self.ram_tier = ram_tier
        self.ollama_bin = None
        self.ollama_proc = None
        self.dashboard_proc = None
        self.dashboard_port = DASHBOARD_PORT
        self.running = False
        self.ollama_port = OLLAMA_PORT

    def _preload_model(self):
        """Load the fastest model for this RAM tier. Blocks until model is warm.
        
        Only ONE model loaded at a time — keeps RAM free for fast switching.
        keep_alive="5m" keeps it in RAM for 5 min, then auto-unloads.
        """
        import urllib.request, json
        model = TIER_FASTEST.get(self.ram_tier, "qwen2.5:7b")
        print(f"  Loading {model}... (first load takes ~5-10s)")
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{self.ollama_port}/api/generate",
                data=json.dumps({"model": model, "prompt": ".", "stream": False, "keep_alive": "5m"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=240) as resp:
                resp.read()
            print(f"  ✓ {model} warm — chat will be 0.3-0.6s per message")
        except Exception as e:
            print(f"  ⚠ First message will take ~5-10s to load model: {e}")

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
                            except:
                                pass
            elif IS_WIN:
                subprocess.run(["taskkill", "/f", "/im", "ollama.exe"], capture_output=True, timeout=5)
        except Exception:
            pass

    def start_ollama(self):
        p("Starting AI engine...", "info")

        self._cleanup_stale_runners()

        if self.ollama_port == 11434 and not is_port_free(11434):
            p("Port 11434 in use — checking for conflict...", "warn")
            try:
                req = urllib.request.Request(f"http://127.0.0.1:11434/api/tags", method="GET")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    existing_models = json.loads(resp.read()).get("models", [])
                    if existing_models:
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
                        if not usb_model_names:
                            alt = find_free_port(11435, 11500)
                            if alt:
                                self.ollama_port = alt
                                p(f"Using alternate port {alt}", "warn")
            except Exception:
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

        p("Waiting for AI engine...", "info")
        url = f"http://127.0.0.1:{self.ollama_port}/api/tags"
        if wait_for_url(url, timeout=180):
            p("AI engine is running!", "ok")
            self._preload_model()
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

        env = os.environ.copy()
        env["LOCALMIND_ROOT"] = str(USB_ROOT)
        env["LOCALMIND_DATA"] = str(DATA_DIR)
        env["LOCALMIND_PORT"] = str(DASHBOARD_PORT)
        env["LOCALMIND_OLLAMA_HOST"] = "127.0.0.1"
        env["LOCALMIND_OLLAMA_PORT"] = str(self.ollama_port)
        env["OLLAMA_HOST"] = "127.0.0.1"
        env["OLLAMA_PORT"] = str(self.ollama_port)
        env["LOCALMIND_RAM_TIER"] = self.ram_tier  # pass tier to dashboard

        self.dashboard_proc = run_bg(
            [sys.executable, str(server_py)],
            env=env,
            cwd=str(DASHBOARD_DIR),
        )

        time.sleep(2)

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
        tier_note = f" [{self.ram_tier.upper()} MODE]" if self.ram_tier == "16gb" else ""
        print()
        print(f"{C['green']}{C['bold']}═══════════════════════════════════════════════════════════{C['reset']}")
        print(f"{C['green']}   ✅ LocalMind is running!{tier_note}{C['reset']}")
        print()
        print(f"{C['green']}   📊 Dashboard:  {url}{C['reset']}")
        print(f"{C['green']}   🤖 Ollama API: http://localhost:{self.ollama_port}{C['reset']}")
        print()

        if auto:
            print(f"{C['cyan']}   🔗 Local Chat is open in your browser!{C['reset']}")
            print()
            print(f"{C['dim']}   Press Ctrl+C to stop LocalMind.{C['reset']}")
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
            print(f"\n   Dashboard at {url}")
            print("   Press Ctrl+C to stop.")
        else:
            print(f"\n   ✅ Dashboard is open in your browser!")
            print("   Press Ctrl+C to stop LocalMind.")

    def start_openclaw(self):
        print()
        p("Starting OpenClaw Chat...", "info")

        # Check for system node first
        node = shutil.which("node")

        # If no system node, try bundled node in openclaw directory
        if not node:
            bundled_node = OPENCLAW_DIR / "node" / "bin" / "node"
            if bundled_node.exists():
                node = str(bundled_node)
                p("Using bundled Node.js from USB.", "ok")

        # Still no node? Try to install via homebrew (macOS) or fail
        if not node:
            p("Node.js not found.", "warn")
            if IS_MAC and shutil.which("brew"):
                p("Installing Node.js via Homebrew...")
                subprocess.run(["brew", "install", "node"], check=False)
                node = shutil.which("node")
            else:
                print("   Node.js is required. Install from: https://nodejs.org/")
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
        ram = get_system_ram_gb()
        tier = get_ram_tier()
        tier_ram_label = f"{round(ram, 1)}GB" if ram else "unknown"
        print(f"\n{C['dim']}   Detected {tier_ram_label} RAM → {tier.upper()} tier{C['reset']}")

        header(tier)

        python_exe = check_python()
        if python_exe != sys.executable:
            os.execv(python_exe, [python_exe, str(Path(__file__).resolve())])

        self.ram_tier = tier  # override default with detected tier
        self.ollama_bin = find_ollama()
        manage_models(self.ollama_bin, tier)

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