#!/usr/bin/env python3
"""
LocalMind Launcher — Cross-Platform USB AI Launcher
====================================================
Runs from USB drive. Auto-detects pre-installed models,
starts Ollama server, opens web dashboard.

Supported: Windows 10+, macOS 12+, Linux
"""

import os
import sys
import json
import time
import signal
import socket
import subprocess
import webbrowser
import threading
from pathlib import Path
from typing import Optional, Dict, List

# ── Platform Detection ──────────────────────────────────
IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform == "linux"
PLATFORM = "windows" if IS_WINDOWS else "macos" if IS_MACOS else "linux"

# ── Paths ───────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
USB_ROOT = SCRIPT_DIR.parent  # launcher is in /launcher/, USB root is parent
DATA_DIR = USB_ROOT / "data"
MODELS_DIR = USB_ROOT / "models"
OLLAMA_DIR = USB_ROOT / "ollama"
DASHBOARD_DIR = USB_ROOT / "dashboard"
CONFIG_FILE = DATA_DIR / "localmind.json"

# Ollama paths
OLLAMA_PORT = 11434
OLLAMA_HOST = "127.0.0.1"
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

# Dashboard
DASHBOARD_PORT = 3000
DASHBOARD_URL = f"http://localhost:{DASHBOARD_PORT}"

# ── Logging ─────────────────────────────────────────────
def log(msg: str, level: str = "info"):
    """Print to console with color codes."""
    colors = {
        "info": "\033[36m",      # cyan
        "ok": "\033[32m",        # green
        "warn": "\033[33m",      # yellow
        "error": "\033[31m",     # red
        "dim": "\033[90m",       # gray
        "reset": "\033[0m",
    }
    prefix = {"info": "[i]", "ok": "[✓]", "warn": "[!]", "error": "[✗]"}
    c = colors.get(level, colors["info"])
    p = prefix.get(level, "[i]")
    print(f"{c}{p}{colors['reset']} {msg}")

# ── Splash Screen (GUI) ─────────────────────────────────
class SplashScreen:
    """Simple splash screen showing load progress."""
    
    def __init__(self):
        try:
            import tkinter as tk
            from tkinter import ttk
            self.root = tk.Tk()
            self.root.title("LocalMind AI")
            self.root.geometry("480x320")
            self.root.resizable(False, False)
            
            # Center window
            self.root.update_idletasks()
            x = (self.root.winfo_screenwidth() - 480) // 2
            y = (self.root.winfo_screenheight() - 320) // 2
            self.root.geometry(f"+{x}+{y}")
            
            # Branding
            tk.Label(self.root, text="LocalMind", font=("Helvetica", 28, "bold"), fg="#2563eb").pack(pady=(30, 0))
            tk.Label(self.root, text="Your AI, Offline", font=("Helvetica", 12), fg="#6b7280").pack(pady=(0, 20))
            
            # Progress bar
            self.progress = ttk.Progressbar(self.root, length=400, mode="determinate")
            self.progress.pack(pady=20)
            
            # Status text
            self.status = tk.Label(self.root, text="Initializing...", font=("Helvetica", 10), fg="#374151")
            self.status.pack(pady=10)
            
            # Details
            self.details = tk.Label(self.root, text="", font=("Helvetica", 9), fg="#9ca3af")
            self.details.pack(pady=5)
            
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
            self.closed = False
            
            # Non-blocking updates
            self.root.update()
        except ImportError:
            self.root = None
            log("tkinter not available — running in console mode", "warn")
    
    def update_status(self, text: str, detail: str = "", progress: int = 0):
        if self.root is None:
            log(f"{text} — {detail}" if detail else text)
            return
        self.status.config(text=text)
        if detail:
            self.details.config(text=detail)
        self.progress["value"] = progress
        self.root.update_idletasks()
    
    def on_close(self):
        self.closed = True
    
    def close(self):
        if self.root:
            self.root.destroy()
    
    def run_async(self):
        """Start main loop in background thread."""
        if self.root:
            threading.Thread(target=self.root.mainloop, daemon=True).start()

# ── Config Management ─────────────────────────────────────
def load_config() -> Dict:
    """Load LocalMind configuration."""
    default = {
        "first_run": True,
        "selected_model": None,
        "last_model": None,
        "settings": {
            "auto_start": True,
            "show_splash": True,
            "dark_mode": True,
        }
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return {**default, **json.load(f)}
        except:
            pass
    return default

def save_config(config: Dict):
    """Save LocalMind configuration."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# ── Ollama Management ───────────────────────────────────
class OllamaManager:
    """Manages Ollama server lifecycle."""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.ollama_bin = self._find_ollama()
    
    def _find_ollama(self) -> Optional[Path]:
        """Find Ollama binary on USB or system."""
        # Check USB first
        candidates = [
            OLLAMA_DIR / "ollama.exe" if IS_WINDOWS else OLLAMA_DIR / "ollama",
            OLLAMA_DIR / f"ollama-{PLATFORM}" / "ollama",
        ]
        
        for c in candidates:
            if c.exists():
                return c
        
        # Check system PATH
        try:
            import shutil
            path = shutil.which("ollama")
            if path:
                return Path(path)
        except:
            pass
        
        return None
    
    def _is_port_free(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.bind((OLLAMA_HOST, port))
                return True
        except:
            return False
    
    def _wait_for_ollama(self, timeout: int = 60) -> bool:
        """Wait for Ollama server to be ready."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"{OLLAMA_BASE_URL}/api/tags",
                    method="GET",
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        return True
            except:
                time.sleep(0.5)
        return False
    
    def start(self) -> bool:
        """Start Ollama server from USB."""
        if self.ollama_bin is None:
            log("Ollama not found on USB or system", "error")
            return False
        
        # Check if already running
        if not self._is_port_free(OLLAMA_PORT):
            log("Ollama already running on port 11434", "ok")
            return True
        
        log(f"Starting Ollama from {self.ollama_bin}")
        
        env = os.environ.copy()
        env["OLLAMA_MODELS"] = str(MODELS_DIR)
        env["OLLAMA_HOST"] = OLLAMA_HOST
        env["OLLAMA_PORT"] = str(OLLAMA_PORT)
        
        # Start Ollama server
        try:
            if IS_WINDOWS:
                self.process = subprocess.Popen(
                    [str(self.ollama_bin), "serve"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                self.process = subprocess.Popen(
                    [str(self.ollama_bin), "serve"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            
            log("Waiting for Ollama to be ready...")
            if self._wait_for_ollama(timeout=60):
                log("Ollama server ready!", "ok")
                return True
            else:
                log("Ollama failed to start within timeout", "error")
                return False
                
        except Exception as e:
            log(f"Failed to start Ollama: {e}", "error")
            return False
    
    def stop(self):
        """Stop Ollama server."""
        if self.process:
            log("Stopping Ollama server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None
    
    def list_models(self) -> List[Dict]:
        """List available models from Ollama."""
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{OLLAMA_BASE_URL}/api/tags",
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                return data.get("models", [])
        except Exception as e:
            log(f"Failed to list models: {e}", "error")
            return []

# ── Dashboard Server ────────────────────────────────────
class DashboardManager:
    """Manages the web dashboard server."""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.server_file = DASHBOARD_DIR / "server.py"
    
    def _is_port_free(self, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.bind(("127.0.0.1", port))
                return True
        except:
            return False
    
    def start(self) -> bool:
        """Start the dashboard web server."""
        if not self._is_port_free(DASHBOARD_PORT):
            log("Dashboard already running on port 3000", "ok")
            return True
        
        if not self.server_file.exists():
            log(f"Dashboard server not found: {self.server_file}", "error")
            return False
        
        log("Starting LocalMind Dashboard...")
        
        try:
            env = os.environ.copy()
            env["LOCALMIND_ROOT"] = str(USB_ROOT)
            env["LOCALMIND_DATA"] = str(DATA_DIR)
            env["LOCALMIND_PORT"] = str(DASHBOARD_PORT)
            
            if IS_WINDOWS:
                self.process = subprocess.Popen(
                    [sys.executable, str(self.server_file)],
                    cwd=str(DASHBOARD_DIR),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                self.process = subprocess.Popen(
                    [sys.executable, str(self.server_file)],
                    cwd=str(DASHBOARD_DIR),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            
            # Wait a moment for server to start
            time.sleep(2)
            
            # Check if port is now in use
            if not self._is_port_free(DASHBOARD_PORT):
                log("Dashboard server ready!", "ok")
                return True
            else:
                log("Dashboard failed to start", "error")
                return False
                
        except Exception as e:
            log(f"Failed to start dashboard: {e}", "error")
            return False
    
    def stop(self):
        """Stop dashboard server."""
        if self.process:
            log("Stopping dashboard...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None

# ── Main Launcher ───────────────────────────────────────
class LocalMindLauncher:
    """Main launcher orchestrating startup sequence."""
    
    def __init__(self):
        self.config = load_config()
        self.splash = SplashScreen()
        self.ollama = OllamaManager()
        self.dashboard = DashboardManager()
        self.running = False
    
    def _update_splash(self, text: str, detail: str = "", progress: int = 0):
        self.splash.update_status(text, detail, progress)
        log(text, "info")
    
    def run(self):
        """Run the full startup sequence."""
        try:
            self.splash.run_async()
            
            # ── Step 1: Detect USB ──────────────────────────
            self._update_splash("Detecting LocalMind USB...", str(USB_ROOT), 10)
            time.sleep(0.5)
            
            if not USB_ROOT.exists():
                self._update_splash("ERROR: USB drive not detected", progress=0)
                time.sleep(3)
                return
            
            # ── Step 2: Verify Installation ───────────────────
            self._update_splash("Verifying installation...", f"USB: {USB_ROOT}", 20)
            
            manifest_file = USB_ROOT / ".localmind" / "manifest.json"
            if manifest_file.exists():
                with open(manifest_file) as f:
                    manifest = json.load(f)
                models = [m["name"] for m in manifest.get("models", [])]
                self._update_splash(
                    f"Found {len(models)} pre-installed models",
                    ", ".join(models[:3]) + ("..." if len(models) > 3 else ""),
                    30
                )
            else:
                self._update_splash("Warning: No manifest found", "Models may need download", 30)
            
            time.sleep(0.5)
            
            # ── Step 3: Start Ollama ──────────────────────────
            self._update_splash("Starting AI engine...", "This may take 30-60 seconds on first run", 40)
            
            if not self.ollama.start():
                self._update_splash("Failed to start AI engine", "Check that Ollama is installed", 0)
                time.sleep(5)
                return
            
            # ── Step 4: Load Models ───────────────────────────
            self._update_splash("Loading AI models...", "Please wait", 60)
            
            models = self.ollama.list_models()
            if models:
                model_names = [m["name"] for m in models]
                self._update_splash(
                    f"{len(models)} models ready",
                    ", ".join(model_names[:3]) + ("..." if len(model_names) > 3 else ""),
                    75
                )
            else:
                self._update_splash("No models found", "Models may need to be downloaded", 75)
            
            time.sleep(0.5)
            
            # ── Step 5: Start Dashboard ───────────────────────
            self._update_splash("Starting dashboard...", "Opening your AI interface", 85)
            
            if not self.dashboard.start():
                self._update_splash("Dashboard failed to start", "Try refreshing the page", 0)
                time.sleep(3)
                return
            
            # ── Step 6: Open Browser ──────────────────────────
            self._update_splash("Launching browser...", DASHBOARD_URL, 95)
            time.sleep(1)
            
            webbrowser.open(DASHBOARD_URL)
            
            self._update_splash("LocalMind is ready!", f"Open: {DASHBOARD_URL}", 100)
            
            # Update config
            self.config["first_run"] = False
            self.config["last_model"] = model_names[0] if models else None
            save_config(self.config)
            
            self.running = True
            
            # Keep splash visible for a moment
            time.sleep(3)
            self.splash.close()
            
            # Keep running until user closes
            log("LocalMind is running. Press Ctrl+C to stop.")
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown."""
        log("Shutting down LocalMind...")
        self.dashboard.stop()
        self.ollama.stop()
        self.splash.close()
        log("Goodbye!", "ok")

# ── Entry Point ─────────────────────────────────────────
def main():
    launcher = LocalMindLauncher()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        launcher.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    if IS_WINDOWS:
        signal.signal(signal.SIGTERM, signal_handler)
    
    launcher.run()

if __name__ == "__main__":
    main()
