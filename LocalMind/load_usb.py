#!/usr/bin/env python3
"""
LocalMind USB Loader
====================
Downloads all required models onto any USB drive and sets it up as a LocalMind unit.

Usage:
    python load_usb.py                        # Interactive
    python load_usb.py --tier 16gb           # Auto-load 16GB tier
    python load_usb.py --tier 8gb            # Auto-load 8GB tier
    python load_usb.py --tier both           # Both tiers (requires ~47GB)
    python load_usb.py --drive D:            # Target specific drive letter

Supports: Windows (cmd), macOS, Linux
"""
import sys
import os
import shutil
import json
import time
import subprocess
from pathlib import Path

# ── Model Definitions ────────────────────────────────────

ALL_MODELS = [
    {"name": "gemma4:e4b",          "size_gb": 2.6, "tier": "8gb",
     "desc": "Fast, efficient. Great for quick tasks and creative writing."},
    {"name": "qwen2.5:7b",          "size_gb": 4.7, "tier": "8gb",
     "desc": "Strong all-purpose. Great coding, reasoning, and general chat."},
    {"name": "qwen2.5-coder:7b",     "size_gb": 4.8, "tier": "8gb",
     "desc": "Code-specialized. Built for programming and debugging."},
    {"name": "qwen3:8b",             "size_gb": 5.5, "tier": "16gb",
     "desc": "Latest Qwen. Smarter chat, better reasoning. Requires 16GB RAM."},
    {"name": "qwen2.5-coder:14b",    "size_gb": 9.0, "tier": "16gb",
     "desc": "Premium coding. 14B params for complex programming tasks."},
    {"name": "gemma3:12b",           "size_gb": 8.0, "tier": "16gb",
     "desc": "Vision model. Analyzes images, reads screenshots, describes photos."},
    # mistral:7b goes in BOTH tiers — universal fastest model (0.5-2s per message)
    {"name": "mistral:7b",           "size_gb": 4.1, "tier": "both",
     "desc": "Universal fastest. Instant responses once loaded. Works on all machines."},
]

# ── ANSI Colors ──────────────────────────────────────────

C = {
    "cyan":   "\033[36m", "green":  "\033[32m", "yellow": "\033[33m",
    "red":    "\033[31m", "blue":   "\033[34m", "dim":    "\033[90m",
    "bold":   "\033[1m",  "reset":  "\033[0m",
}
P = {
    "ok":    f"{C['green']}[✓]{C['reset']}",
    "info":  f"{C['cyan']}[i]{C['reset']}",
    "warn":  f"{C['yellow']}[!]{C['reset']}",
    "error": f"{C['red']}[✗]{C['reset']}",
    "done":  f"{C['green']}[✔]{C['reset']}",
}

def p(msg, level="ok"):
    print(f"{P.get(level, P['ok'])} {msg}")

def banner():
    print(f"""
{C['cyan']}{C['bold']}
    ╔═══════════════════════════════════════════╗
    ║      LocalMind USB Loader  v1.0           ║
    ║      Setup any USB as a LocalMind unit     ║
    ╚═══════════════════════════════════════════╝
{C['reset']}
""")

# ── Ollama Helpers ────────────────────────────────────────

def get_ollama_bin():
    """Find ollama binary."""
    # Try system PATH
    path = shutil.which("ollama")
    if path:
        return Path(path)
    
    # Try common macOS locations
    for candidate in [Path("/usr/local/bin/ollama"), Path("/opt/homebrew/bin/ollama")]:
        if candidate.exists():
            return candidate
    
    return None

def get_installed_models(ollama_bin):
    """Return list of installed model names. Parses text output (works on Ollama 0.24+)."""
    try:
        env = os.environ.copy()
        result = subprocess.run(
            [str(ollama_bin), "list"],
            capture_output=True, text=True, timeout=15, env=env
        )
        if result.returncode == 0:
            models = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or line.startswith("NAME") or line.startswith("-"):
                    continue
                # First whitespace-delimited field is the model name
                name = line.split()[0] if line.split() else ""
                if name:
                    models.append(name)
            return models
    except Exception as e:
        print(f"    {P['warn']} Could not list models: {e}")
    return []

def pull_model(ollama_bin, model_name, progress_callback=None):
    """Pull a single model. Returns True on success."""
    print(f"    {P['info']} Pulling {model_name}...", end=" ", flush=True)
    try:
        proc = subprocess.Popen(
            [str(ollama_bin), "pull", model_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in proc.stdout:
            line = line.strip()
            # Show download progress (ollama 0.24 prints % lines)
            if progress_callback and "%" in line:
                progress_callback(line)
        proc.wait()
        success = proc.returncode == 0
        print(f"{P['done']}" if success else f"{P['error']}")
        return success
    except Exception as e:
        print(f"{P['error']} {e}")
        return False

# ── Drive Detection ───────────────────────────────────────

def detect_drives():
    """Return list of (drive_letter, label, free_gb) for available drives."""
    drives = []
    system = sys.platform

    if system == "win32":
        import subprocess
        try:
            result = subprocess.run(
                ["wmic", "logicaldisk", "get", "caption,size,freespace,volumename", "/format:csv"],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.strip().splitlines()[1:]:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4 and parts[1]:  # caption (e.g. D:)
                    letter = parts[0]  # e.g. D:
                    try:
                        free_gb = int(parts[2]) / (1024**3) if parts[2].isdigit() else 0
                        label = parts[3] if len(parts) > 3 else ""
                        if free_gb > 1:  # at least 1GB free
                            drives.append((letter, label, free_gb))
                    except:
                        pass
        except Exception as e:
            print(f"    {P['warn']} Could not detect drives: {e}")

    elif system == "darwin":
        import subprocess
        try:
            result = subprocess.run(
                ["df", "-h"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 9 and "/Volumes/" in parts[-1]:
                    mount = parts[-1]
                    if "LOCALMIND" in mount.upper() or "/Volumes/" in mount:
                        try:
                            free_gb = float(parts[3].rstrip("GMGTP"))
                            unit = parts[3][-1]
                            if unit == "T":
                                free_gb *= 1024
                            drives.append((mount, mount.split("/")[-1], free_gb))
                        except:
                            pass
        except Exception as e:
            print(f"    {P['warn']} Could not detect drives: {e}")

    else:  # linux
        import subprocess
        try:
            result = subprocess.run(
                ["df", "-h", "--output=target,size,avail"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 3 and "/media/" in parts[0]:
                    drives.append((parts[0], parts[0].split("/")[-1], 0))
        except:
            pass

    return drives

def get_models_for_tier(tier):
    """Return all model names for the given tier (including 'both' models)."""
    return [m["name"] for m in ALL_MODELS if m["tier"] == tier or m["tier"] == "both"]

def get_tier_size(tier):
    """Return total GB needed for a tier."""
    return sum(m["size_gb"] for m in ALL_MODELS if m["tier"] == tier or m["tier"] == "both")

def choose_drive():
    """Let user choose a drive to load."""
    print(f"\n{C['bold']}Available drives:{C['reset']}")
    drives = detect_drives()
    
    if not drives:
        print(f"    {P['error']} No drives detected.")
        print(f"    {P['info']} Make sure your USB is plugged in.")
        return None

    for i, (letter, label, free_gb) in enumerate(drives, 1):
        print(f"    {C['cyan']}{i}){C['reset']} {letter} {C['dim']}'{label}'{C['reset']} ({free_gb:.1f} GB free)")

    print(f"    {C['cyan']}q){C['reset']} Quit")

    while True:
        choice = input(f"\n{C['bold']}Select drive number:{C['reset']} ").strip()
        if choice.lower() == "q":
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(drives):
                return drives[idx]
        except:
            pass
        print(f"    {P['warn']} Invalid choice.")

def choose_tier(drive_free_gb):
    """Let user choose which tier to load."""
    print(f"\n{C['bold']}Which tier to load?{C['reset']}")
    print()
    print(f"    {C['cyan']}1){C['reset']} 8GB tier — ~16 GB total")
    print(f"          gemma4:e4b, qwen2.5:7b, qwen2.5-coder:7b, mistral:7b")
    print(f"          For machines with 8-12GB RAM")
    print()
    print(f"    {C['cyan']}2){C['reset']} 16GB tier — ~27 GB total {C['dim']}(recommended){C['reset']}")
    print(f"          qwen3:8b, qwen2.5-coder:14b, gemma3:12b, mistral:7b")
    print(f"          For machines with 16GB+ RAM")
    print()
    print(f"    {C['cyan']}3){C['reset']} Both tiers — ~47 GB total")
    print(f"          All models. Requires a very large drive.")

    while True:
        choice = input(f"\n{C['bold']}Select tier (1/2/3):{C['reset']} ").strip()
        if choice == "1":
            return "8gb"
        elif choice == "2":
            return "16gb"
        elif choice == "3":
            return "both"
        print(f"    {P['warn']} Invalid choice.")

def create_manifest(usb_root, tier):
    """Create the manifest file so the dashboard knows what models are on this USB."""
    manifest_dir = usb_root / ".localmind"
    manifest_dir.mkdir(parents=True, exist_ok=True)

    models_to_include = [m for m in ALL_MODELS if m["tier"] == tier or m["tier"] == "both"]
    manifest = {
        "version": "2.0",
        "name": "LocalMind",
        "description": "Offline AI on a USB stick",
        "ram_tier": tier,
        "ollama_version": "0.5+",
        "models": models_to_include,
    }

    manifest_path = manifest_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest_path

def load_usb(tier, drive_letter=None):
    """Main loader: detect drive, download models, set up USB."""
    banner()

    # Find ollama
    print(f"{C['bold']}Checking Ollama...{C['reset']}")
    ollama_bin = get_ollama_bin()
    if not ollama_bin:
        print(f"    {P['error']} Ollama not found.")
        print(f"    {P['info']} Install from https://ollama.com")
        print(f"    {P['info']} Or: brew install ollama (macOS)")
        return False

    print(f"    {P['ok']} Ollama found at {ollama_bin}")
    ollama_version = subprocess.run(
        [str(ollama_bin), "--version"],
        capture_output=True, text=True, timeout=5
    ).stdout.strip()
    print(f"    {P['ok']} Version: {ollama_version}")

    # Choose drive
    if not drive_letter:
        drive = choose_drive()
        if not drive:
            print(f"\n{P['ok']} Cancelled.")
            return False
        drive_letter, drive_label, drive_free = drive
    else:
        drive_letter = drive_letter.rstrip("\\/") + ("\\" if sys.platform == "win32" else "/")
        drive_free = 0

    # Choose tier
    if not tier:
        tier = choose_tier(drive_free)
        if not tier:
            print(f"\n{P['ok']} Cancelled.")
            return False

    # Calculate space needed
    size_needed = get_tier_size(tier)
    models_to_pull = get_models_for_tier(tier)

    print(f"\n{C['bold']}Setup Summary:{C['reset']}")
    print(f"    Drive: {drive_letter}")
    print(f"    Tier:  {tier.upper()}")
    print(f"    Space needed: {size_needed:.1f} GB")
    print(f"    Models to download: {len(models_to_pull)}")
    for m in models_to_pull:
        print(f"      • {m}")

    confirm = input(f"\n{C['bold']}Start loading? (y/n):{C['reset']} ").strip().lower()
    if confirm != "y":
        print(f"\n{P['ok']} Cancelled.")
        return False

    # Create directory structure
    usb_root = Path(drive_letter)
    if not usb_root.exists():
        print(f"    {P['error']} Drive {drive_letter} not found.")
        return False

    localmind_dir = usb_root / "LocalMind"
    models_dir = usb_root / "models"
    data_dir = usb_root / "data"

    print(f"\n{C['bold']}Creating directory structure...{C['reset']}")
    for d in [localmind_dir, models_dir, data_dir]:
        d.mkdir(parents=True, exist_ok=True)
        print(f"    {P['ok']} {d.relative_to(usb_root)}/")

    # Set OLLAMA_MODELS to USB
    env = os.environ.copy()
    env["OLLAMA_MODELS"] = str(models_dir)
    env["OLLAMA_HOST"] = "127.0.0.1"

    # Check which models are already installed
    print(f"\n{C['bold']}Checking existing models...{C['reset']}")
    installed = get_installed_models(ollama_bin)
    to_pull = [m for m in models_to_pull if m not in installed]

    if installed:
        already = [m for m in models_to_pull if m in installed]
        print(f"    {P['ok']} Already have {len(installed)}/{len(models_to_pull)} models:")
        for m in already:
            print(f"      {P['ok']} {m}")

    if not to_pull:
        print(f"    {P['ok']} All models already downloaded!")
    else:
        print(f"\n{C['bold']}Downloading {len(to_pull)} models...{C['reset']}")
        for i, model in enumerate(to_pull, 1):
            print(f"\n    {C['bold']}[{i}/{len(to_pull)}]{C['reset']} {model}")
            success = pull_model(ollama_bin, model)
            if not success:
                print(f"    {P['error']} Failed to download {model}.")
                retry = input(f"    Continue without {model}? (y/n): ").strip().lower()
                if retry != "y":
                    return False

    # Copy setup files
    print(f"\n{C['bold']}Setting up LocalMind structure...{C['reset']}")
    src_dir = Path(__file__).parent.resolve()
    
    # Check if we're running from repo or from a loaded USB
    setup_py = src_dir / "setup.py"
    if not setup_py.exists():
        print(f"    {P['warn']} setup.py not found — skipping config files.")
        print(f"    {P['info']} Copy LocalMind/ from repo to USB manually.")
    else:
        dest_localmind = usb_root / "LocalMind"
        files_to_copy = ["setup.py"]
        for fname in files_to_copy:
            src_f = setup_py.parent / fname
            dest_f = dest_localmind / fname
            if src_f.exists():
                shutil.copy2(src_f, dest_f)
                print(f"    {P['ok']} {fname}")

    # Create manifest
    manifest_path = create_manifest(usb_root, tier)
    print(f"    {P['ok']} Created manifest: {manifest_path.relative_to(usb_root)}")

    print(f"""
{C['green']}{C['bold']}
╔═══════════════════════════════════════════════════════╗
║  ✅ LocalMind USB is ready!                           ║
╚═══════════════════════════════════════════════════════╝
{C['reset']}

  Drive:  {drive_letter}
  Tier:   {tier.upper()}
  Models: {len(models_to_pull)}

  Next steps:
  1. Eject the USB safely
  2. Plug it into the target computer
  3. Run START-Windows.bat (Windows) or START-macOS.command (macOS)

{C['dim']}Note: First run will take ~20-60s to warm up mistral:7b.
   After that, chat is 0.5-2s per message.{C['reset']}
""")
    return True

# ── CLI Entry Point ──────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load LocalMind onto a USB drive.")
    parser.add_argument("--tier", choices=["8gb", "16gb", "both"], default=None,
                        help="Which tier to load (8gb, 16gb, or both)")
    parser.add_argument("--drive", default=None,
                        help="Target drive letter or mount point (e.g. D: or /Volumes/MyUSB)")
    args = parser.parse_args()

    try:
        success = load_usb(args.tier, args.drive)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{P['ok']} Interrupted.")
        sys.exit(130)
