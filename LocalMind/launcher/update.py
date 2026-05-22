#!/usr/bin/env python3
"""
LocalMind Update System
=======================
Downloads new model packs and applies them to the USB drive.

Usage:
    python update.py --list          # Show available updates
    python update.py --download MODEL # Download a specific model
    python update.py --update        # Check for launcher/dashboard updates
"""

import os
import sys
import json
import hashlib
import zipfile
import argparse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

# ── Paths ───────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
USB_ROOT = SCRIPT_DIR.parent
DATA_DIR = USB_ROOT / "data"
MODELS_DIR = USB_ROOT / "models"
UPDATE_DIR = USB_ROOT / "update"
MANIFEST_FILE = USB_ROOT / ".localmind" / "manifest.json"
UPDATE_MANIFEST_URL = "https://updates.localmind.ai/manifest.json"

# ── Colors ────────────────────────────────────────────────
def c(code): return f"\033[{code}m"
RED, GREEN, YELLOW, CYAN, DIM, RESET = c(31), c(32), c(33), c(36), c(90), c(0)

def log(msg): print(f"{CYAN}[LocalMind]{RESET} {msg}")
def ok(msg): print(f"{GREEN}[OK]{RESET} {msg}")
def warn(msg): print(f"{YELLOW}[WARN]{RESET} {msg}")
def err(msg): print(f"{RED}[ERROR]{RESET} {msg}")

# ── Update Manifest ─────────────────────────────────────
def fetch_update_manifest() -> Optional[Dict]:
    """Fetch latest update manifest from server."""
    try:
        req = urllib.request.Request(UPDATE_MANIFEST_URL, timeout=10)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except Exception as e:
        warn(f"Could not check for updates: {e}")
        return None

def load_local_manifest() -> Dict:
    """Load current USB manifest."""
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE) as f:
            return json.load(f)
    return {"version": "0.0.0", "models": []}

# ── Model Management ────────────────────────────────────
def list_available_models(remote_manifest: Dict, local_manifest: Dict) -> List[Dict]:
    """List models available for download."""
    local_models = {m["name"] for m in local_manifest.get("models", [])}
    available = []
    
    for model in remote_manifest.get("models", []):
        status = "installed" if model["name"] in local_models else "available"
        available.append({**model, "status": status})
    
    return available

def download_model(model_name: str, url: str, dest: Path, progress_callback=None) -> bool:
    """Download a model file with progress."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 8192
            
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        progress_callback(downloaded, total_size)
        
        return True
    except Exception as e:
        err(f"Download failed: {e}")
        if dest.exists():
            dest.unlink()
        return False

def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """Verify file SHA-256 checksum."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest().lower() == expected_hash.lower()

def install_model(model_info: Dict) -> bool:
    """Download and install a model."""
    model_name = model_info["name"]
    url = model_info.get("download_url", "")
    checksum = model_info.get("checksum", "")
    size_gb = model_info.get("size_gb", 0)
    
    if not url:
        err(f"No download URL for {model_name}")
        return False
    
    # Check disk space
    free_space = shutil.disk_usage(USB_ROOT).free / (1024**3)  # GB
    if free_space < size_gb + 1:
        err(f"Not enough space. Need {size_gb + 1}GB, have {free_space:.1f}GB")
        return False
    
    log(f"Downloading {model_name} (~{size_gb}GB)...")
    
    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    download_path = UPDATE_DIR / f"{model_name.replace(':', '_')}.zip"
    
    # Download
    def progress(done, total):
        pct = (done / total) * 100
        mb = done / (1024**2)
        print(f"\r  {CYAN}Downloading:{RESET} {pct:.1f}% ({mb:.0f} MB)", end="", flush=True)
    
    if not download_model(model_name, url, download_path, progress):
        return False
    print()  # New line after progress
    
    # Verify checksum
    if checksum:
        log("Verifying checksum...")
        if not verify_checksum(download_path, checksum):
            err("Checksum mismatch! Download may be corrupted.")
            download_path.unlink()
            return False
        ok("Checksum verified")
    
    # Extract
    log("Extracting model...")
    try:
        with zipfile.ZipFile(download_path, "r") as z:
            z.extractall(MODELS_DIR)
        ok(f"{model_name} installed successfully")
        
        # Clean up download
        download_path.unlink()
        
        # Update manifest
        update_local_manifest(model_info)
        
        return True
    except Exception as e:
        err(f"Extraction failed: {e}")
        return False

def update_local_manifest(new_model: Dict):
    """Add new model to local manifest."""
    manifest = load_local_manifest()
    models = manifest.get("models", [])
    
    # Remove if already exists
    models = [m for m in models if m["name"] != new_model["name"]]
    models.append(new_model)
    
    manifest["models"] = models
    manifest["updated_at"] = datetime.now().isoformat()
    
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)

# ── Launcher Update ─────────────────────────────────────
def check_launcher_update(remote_manifest: Dict) -> bool:
    """Check if launcher/dashboard need updating."""
    local = load_local_manifest()
    local_ver = local.get("version", "0.0.0")
    remote_ver = remote_manifest.get("version", "0.0.0")
    
    return remote_ver > local_ver

def download_update_package(url: str, dest: Path) -> bool:
    """Download update package."""
    log("Downloading update package...")
    return download_model("update", url, dest)

def apply_update_package(package_path: Path) -> bool:
    """Apply update package to USB."""
    log("Applying update...")
    try:
        with zipfile.ZipFile(package_path, "r") as z:
            # Extract to temp first
            temp_dir = UPDATE_DIR / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            z.extractall(temp_dir)
            
            # Copy files to USB root (backup first)
            backup_dir = UPDATE_DIR / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # TODO: Implement safe file replacement with rollback
            log("Update applied (simulation — implement actual file replacement)")
        
        return True
    except Exception as e:
        err(f"Update failed: {e}")
        return False

# ── CLI ─────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="LocalMind Update System")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--download", metavar="MODEL", help="Download a specific model")
    parser.add_argument("--update", action="store_true", help="Check for launcher/dashboard updates")
    parser.add_argument("--offline", action="store_true", help="Work offline (use cached manifests)")
    args = parser.parse_args()
    
    local_manifest = load_local_manifest()
    
    if args.list:
        if args.offline:
            log("Offline mode — showing installed models only")
            for m in local_manifest.get("models", []):
                print(f"  {m['name']} ({m.get('size_gb', '?')}GB) — {m.get('description', '')}")
        else:
            remote = fetch_update_manifest()
            if remote:
                models = list_available_models(remote, local_manifest)
                print(f"\n  {CYAN}Available Models:{RESET}\n")
                for m in models:
                    status_icon = f"{GREEN}✓{RESET}" if m["status"] == "installed" else f"{YELLOW}○{RESET}"
                    print(f"  {status_icon} {m['name']} ({m.get('size_gb', '?')}GB)")
                    print(f"    {DIM}{m.get('description', '')}{RESET}")
                print()
    
    elif args.download:
        remote = fetch_update_manifest()
        if not remote:
            err("Cannot download — no internet connection")
            sys.exit(1)
        
        model_info = None
        for m in remote.get("models", []):
            if m["name"] == args.download:
                model_info = m
                break
        
        if not model_info:
            err(f"Model '{args.download}' not found in update catalog")
            sys.exit(1)
        
        if install_model(model_info):
            ok(f"{args.download} is ready to use!")
        else:
            err(f"Failed to install {args.download}")
            sys.exit(1)
    
    elif args.update:
        remote = fetch_update_manifest()
        if not remote:
            err("Cannot check for updates — no internet connection")
            sys.exit(1)
        
        if check_launcher_update(remote):
            log(f"Update available: {local_manifest.get('version', '0.0.0')} → {remote.get('version')}")
            # TODO: Implement actual update download/apply
            log("Update download not yet implemented")
        else:
            ok("LocalMind is up to date!")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    import shutil
    from datetime import datetime
    main()
