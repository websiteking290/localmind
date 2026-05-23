#!/usr/bin/env python3
"""
LocalMind OpenClaw Setup Script
=================================
Integrates OpenClaw AI assistant with LocalMind USB models.

This script:
1. Checks if OpenClaw is installed, downloads if not
2. Configures OpenClaw to use local Ollama models
3. Makes all USB models available in OpenClaw
4. Starts OpenClaw chat interface
"""

import os
import sys
import json
import time
import shutil
import subprocess
import urllib.request
from pathlib import Path

# ── Paths ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
USB_ROOT = SCRIPT_DIR.parent
OLLAMA_DIR = USB_ROOT / "ollama"
MODELS_DIR = USB_ROOT / "models"
DATA_DIR = USB_ROOT / "data"
OPENCLAW_DIR = USB_ROOT / "openclaw"
OPENCLAW_CONFIG_DIR = DATA_DIR / ".openclaw"

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

# ── Colors ──────────────────────────────────────────────
CYAN = '\033[36m'; GREEN = '\033[32m'; YELLOW = '\033[33m'; RED = '\033[31m'; BLUE = '\033[34m'; RESET = '\033[0m'

def log(msg, level="info"):
    colors = {"info": CYAN, "ok": GREEN, "warn": YELLOW, "error": RED}
    prefix = {"info": "[i]", "ok": "[✓]", "warn": "[!]", "error": "[✗]"}
    c = colors.get(level, CYAN)
    p = prefix.get(level, "[i]")
    print(f"{c}{p}{RESET} {msg}")

def check_command(cmd):
    """Check if a command is available."""
    return shutil.which(cmd) is not None

def get_ollama_models():
    """Get list of models from local Ollama."""
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return [m.get("name", "").replace(":latest", "") for m in data.get("models", [])]
    except Exception as e:
        log(f"Could not fetch models from Ollama: {e}", "warn")
        return []

def install_openclaw():
    """Download and install OpenClaw."""
    log("OpenClaw not found. Installing...")
    
    # Check if we have Node.js
    if not check_command("node"):
        log("Node.js is required for OpenClaw.", "warn")
        if sys.platform == "darwin":
            log("Installing Node.js via Homebrew...")
            subprocess.run(["brew", "install", "node"], check=False)
        elif sys.platform == "win32":
            log("Please install Node.js from https://nodejs.org/", "error")
            return False
        else:
            log("Please install Node.js for your system", "error")
            return False
    
    # Install OpenClaw globally via npm
    log("Downloading OpenClaw (this may take a minute)...")
    result = subprocess.run(
        ["npm", "install", "-g", "openclaw"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        log(f"Failed to install OpenClaw: {result.stderr}", "error")
        return False
    
    log("OpenClaw installed successfully!", "ok")
    return True

def configure_openclaw_for_ollama(models):
    """Configure OpenClaw to use local Ollama models."""
    log("Configuring OpenClaw for local models...")
    
    # Create OpenClaw config directory
    OPENCLAW_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Build model config
    model_config = {
        "agents": {
            "defaults": {
                "model": {
                    "primary": f"ollama/{models[0]}" if models else "ollama/llama3.1",
                },
                "maxConcurrent": 4,
                "subagents": {
                    "maxConcurrent": 8
                }
            }
        },
        "gateway": {
            "mode": "local",
            "bind": "loopback",
            "port": 19000
        }
    }
    
    # Write config
    config_file = OPENCLAW_CONFIG_DIR / "config.yaml"
    try:
        import yaml
        with open(config_file, "w") as f:
            yaml.dump(model_config, f)
    except ImportError:
        # Write as JSON if no yaml
        with open(config_file.with_suffix(".json"), "w") as f:
            json.dump(model_config, f, indent=2)
    
    log(f"OpenClaw configured to use: {models[0] if models else 'llama3.1'}", "ok")
    return True

def setup_models_in_openclaw(models):
    """Register USB models with OpenClaw."""
    if not models:
        log("No models to register", "warn")
        return
    
    log(f"Registering {len(models)} models with OpenClaw...")
    
    for model in models:
        model_name = f"ollama/{model}"
        log(f"  Adding: {model_name}")
        # OpenClaw should auto-discover Ollama models, but we can set aliases
        subprocess.run(
            ["openclaw", "models", "aliases", "add", model, model_name],
            capture_output=True
        )
    
    log(f"All {len(models)} models registered!", "ok")

def start_openclaw_chat():
    """Start OpenClaw chat interface."""
    log("Starting OpenClaw chat...")
    log("")
    log(f"{GREEN}═══════════════════════════════════════════════════════════{RESET}")
    log(f"{GREEN}   🤖 OpenClaw is ready!{RESET}")
    log(f"{GREEN}   Type your messages below:{RESET}")
    log(f"{GREEN}═══════════════════════════════════════════════════════════{RESET}")
    log("")
    
    # Start OpenClaw chat in terminal
    try:
        subprocess.run(["openclaw", "chat"])
    except KeyboardInterrupt:
        log("\nChat closed.", "ok")

def main():
    """Main setup flow."""
    print("")
    print(f"{CYAN}╔═══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}║                                                           ║{RESET}")
    print(f"{CYAN}║            🤖  OPENCLAW SETUP FOR LOCALMIND              ║{RESET}")
    print(f"{CYAN}║                                                           ║{RESET}")
    print(f"{CYAN}║      Your AI assistant using local USB models               ║{RESET}")
    print(f"{CYAN}║                                                           ║{RESET}")
    print(f"{CYAN}╚═══════════════════════════════════════════════════════════╝{RESET}")
    print("")
    
    # Step 1: Check if Ollama is running
    log("Checking Ollama server...")
    models = get_ollama_models()
    
    if not models:
        log("Ollama not running or no models found!", "error")
        log("Please start LocalMind first (run START-macOS.command or START-Windows.bat)", "warn")
        input("\nPress Enter to exit...")
        return 1
    
    log(f"Found {len(models)} models: {', '.join(models[:3])}{'...' if len(models) > 3 else ''}", "ok")
    
    # Step 2: Check if OpenClaw is installed
    log("Checking OpenClaw installation...")
    if not check_command("openclaw"):
        log("OpenClaw not found.")
        choice = input(f"{YELLOW}Download and install OpenClaw? (y/n): {RESET}").strip().lower()
        if choice == 'y':
            if not install_openclaw():
                log("OpenClaw installation failed.", "error")
                return 1
        else:
            log("OpenClaw is required for this feature.", "warn")
            return 0
    else:
        log("OpenClaw is already installed", "ok")
    
    # Step 3: Configure OpenClaw
    configure_openclaw_for_ollama(models)
    
    # Step 4: Register models
    setup_models_in_openclaw(models)
    
    # Step 5: Start chat
    log("")
    log(f"{GREEN}Setup complete! Starting chat...{RESET}")
    time.sleep(1)
    
    start_openclaw_chat()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
