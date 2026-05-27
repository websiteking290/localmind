#!/usr/bin/env python3
"""
LocalMind USB Cloner
====================
Clones a LocalMind USB to another USB drive.
No internet needed — copies everything directly from source to destination.

Usage:
    python clone_usb.py              # Interactive
    python clone_usb.py --source /Volumes/LOCALMIND   # Specify source
    python clone_usb.py --dest /dev/disk4            # Specify destination

Works on: macOS, Windows, Linux
"""
import sys
import os
import shutil
import time
import subprocess
from pathlib import Path

# ── ANSI Colors ─────────────────────────────────────────

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
}

def p(msg, level="ok"):
    print(f"{P.get(level, P['ok'])} {msg}")

def banner():
    print(f"""
{C['cyan']}{C['bold']}
    ╔═══════════════════════════════════════════╗
    ║    LocalMind USB Cloner  v1.0            ║
    ║    Clone your LocalMind USB drive         ║
    ╚═══════════════════════════════════════════╝
{C['reset']}
""")

# ── Drive Detection ───────────────────────────────────────

def get_mac_drives():
    """Get all mounted volumes on macOS."""
    drives = []
    try:
        result = subprocess.run(
            ["df", "-h"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 9 and "/Volumes/" in parts[-1]:
                mount = parts[-1]
                # Get device
                dev = None
                try:
                    r2 = subprocess.run(
                        ["df", "-l", mount],
                        capture_output=True, text=True, timeout=3
                    )
                    for l in r2.stdout.splitlines()[1:]:
                        if mount in l:
                            dev = l.split()[0]
                            break
                except:
                    pass
                try:
                    free_gb = float(parts[3].rstrip("GMGTP"))
                    unit = parts[3][-1]
                    if unit == "T": free_gb *= 1024
                    drives.append({
                        "path": mount,
                        "label": mount.split("/")[-1],
                        "free_gb": free_gb,
                        "dev": dev or "",
                    })
                except:
                    pass
    except Exception as e:
        print(f"    {P['warn']} Could not detect drives: {e}")
    return drives

def get_size_of_dir(path):
    """Get total size of a directory in GB."""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total += os.path.getsize(fp)
                except:
                    pass
    except:
        pass
    return total / (1024**3)

def is_localmind_drive(path):
    """Check if a volume contains a LocalMind installation."""
    check_files = [
        "LocalMind/setup.py",
        "START-Windows.bat",
        "START.html",
    ]
    for f in check_files:
        if os.path.exists(os.path.join(path, f)):
            return True
    return False

# ── Progress Copy ─────────────────────────────────────────

def copy_with_progress(src, dst, description=""):
    """Copy a directory tree with progress display."""
    total_size = get_size_of_dir(src)
    desc = description or os.path.basename(src)
    
    copied_size = [0]
    file_count = [0]
    
    def _copy_tree_progress(src, dst):
        """Recursively copy with progress."""
        if not os.path.exists(dst):
            os.makedirs(dst)
        
        for item in os.listdir(src):
            src_item = os.path.join(src, item)
            dst_item = os.path.join(dst, item)
            
            if os.path.isdir(src_item):
                _copy_tree_progress(src_item, dst_item)
            else:
                # Copy file
                size = os.path.getsize(src_item)
                shutil.copy2(src_item, dst_item)
                copied_size[0] += size
                file_count[0] += 1
                
                # Progress bar
                pct = min(100, (copied_size[0] / (total_size * 1024**3)) * 100) if total_size > 0 else 0
                bar_len = 30
                filled = int(bar_len * pct / 100)
                bar = "█" * filled + "░" * (bar_len - filled)
                gb_copied = copied_size[0] / (1024**3)
                sys.stdout.write(
                    f"\r  {desc}  {bar}  {pct:5.1f}%  ({gb_copied:.1f}/{total_size:.1f} GB)  {file_count[0]} files   "
                )
                sys.stdout.flush()
    
    _copy_tree_progress(src, dst)
    print()

# ── Main Clone Logic ───────────────────────────────────────

def detect_drives():
    """Find all drives and identify which one is LocalMind."""
    print(f"{C['bold']}Scanning drives...{C['reset']}")
    
    drives = get_mac_drives()
    source_drive = None
    dest_drives = []
    
    for d in drives:
        path = d["path"]
        label = d["label"]
        free = d["free_gb"]
        
        is_localmind = is_localmind_drive(path)
        is_system = path == "/" or "Macintosh HD" in path
        
        tag = ""
        if is_localmind:
            tag = f" {C['green']}[LOCALMIND SOURCE]{C['reset']}"
            source_drive = d
        elif not is_system and free > 2:
            tag = f" {C['cyan']}[USB DESTINATION]{C['reset']}"
            dest_drives.append(d)
        
        if not is_system:
            print(f"  {P['ok']} {path}  — {label} — {free:.1f} GB free{tag}")
    
    return source_drive, dest_drives, drives

def choose_source(source_drive, all_drives):
    """Let user choose source drive."""
    if source_drive:
        print(f"\n{C['green']}Source found: {source_drive['path']}{C['reset']}")
        confirm = input(f"  Use as source? (Y/n): ").strip().lower()
        if confirm != "n":
            return source_drive
    
    print(f"\n{C['bold']}Select SOURCE drive:{C['reset']}")
    usable = [d for d in all_drives if d["path"] != "/"]
    for i, d in enumerate(usable, 1):
        print(f"  {C['cyan']}{i}){C['reset']} {d['path']} — {d['label']} — {d['free_gb']:.1f} GB free")
    
    while True:
        choice = input(f"\n{C['bold']}Select source (number):{C['reset']} ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(usable):
                return usable[idx]
        except:
            pass
        print(f"  {P['warn']} Invalid choice.")

def choose_dest(source_drive, dest_drives):
    """Let user choose destination drive."""
    if len(dest_drives) == 0:
        print(f"\n{P['warn']} No empty USB drives detected.")
        print(f"  {P['info']} Please insert a blank USB drive and run again.")
        return None
    
    if len(dest_drives) == 1:
        d = dest_drives[0]
        print(f"\n{C['cyan']}Destination found: {d['path']}{C['reset']}")
        confirm = input(f"  Use as destination? (Y/n): ").strip().lower()
        if confirm != "n":
            return d
    
    print(f"\n{C['bold']}Select DESTINATION drive:{C['reset']}")
    for i, d in enumerate(dest_drives, 1):
        print(f"  {C['cyan']}{i}){C['reset']} {d['path']} — {d['label']} — {d['free_gb']:.1f} GB free")
    
    while True:
        choice = input(f"\n{C['bold']}Select destination (number):{C['reset']} ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(dest_drives):
                return dest_drives[idx]
        except:
            pass
        print(f"  {P['warn']} Invalid choice.")

def clone_drive(source, dest):
    """Clone source drive to destination drive."""
    source_path = Path(source["path"])
    dest_path = Path(dest["path"])
    
    # What we need to copy
    dirs_to_copy = ["LocalMind", "models", "data", "START.html", "START-Windows.bat", "START-macOS.command", "autorun.inf"]
    
    # Calculate total size
    print(f"\n{C['bold']}Calculating size...{C['reset']}")
    total_size = 0
    for dirname in dirs_to_copy:
        src_dir = source_path / dirname
        if src_dir.exists():
            size = get_size_of_dir(src_dir)
            total_size += size
            print(f"  {P['ok']} {dirname}: {size:.1f} GB")
    
    free_dest = dest["free_gb"]
    print(f"\n  Total to copy: {total_size:.1f} GB")
    print(f"  Destination free: {free_dest:.1f} GB")
    
    if total_size > free_dest * 0.95:
        print(f"\n  {P['error']} Not enough space on destination!")
        print(f"  {P['info']} Need at least {total_size:.1f} GB, have {free_dest:.1f} GB.")
        return False
    
    # Confirm
    print(f"\n{C['bold']}Ready to clone:{C['reset']}")
    print(f"  Source:      {source_path}")
    print(f"  Destination: {dest_path}")
    print(f"  Size:        {total_size:.1f} GB")
    
    confirm = input(f"\n{C['red']}{C['bold']}This will ERASE the destination drive!{C['reset']}\n  Type 'yes' to confirm: ").strip()
    if confirm != "yes":
        print(f"\n{P['ok']} Cancelled.")
        return False
    
    print(f"\n{C['bold']}Cloning...{C['reset']}")
    print(f"(This will take a few minutes — please wait)\n")
    
    start = time.time()
    copied = 0
    
    for dirname in dirs_to_copy:
        src_dir = source_path / dirname
        if not src_dir.exists():
            print(f"  {P['warn']} {dirname}: not found on source, skipping")
            continue
        
        print(f"\n  {C['bold']}Copying {dirname}...{C['reset']}")
        try:
            if src_dir.is_dir():
                copy_with_progress(src_dir, dest_path / dirname, dirname)
            else:
                # Single file
                shutil.copy2(src_dir, dest_path / dirname)
                print(f"  Copied {dirname}")
        except Exception as e:
            print(f"\n  {P['error']} Failed to copy {dirname}: {e}")
            retry = input("  Continue? (y/n): ").strip().lower()
            if retry != "y":
                return False
    
    elapsed = time.time() - start
    
    print(f"""
{C['green']}{C['bold']}
╔═══════════════════════════════════════════════════════╗
║  ✅ Clone complete!                                  ║
╚═══════════════════════════════════════════════════════╝
{C['reset']}
  Copied:    {total_size:.1f} GB
  Time:      {elapsed:.1f} seconds
  Source:    {source_path}
  Dest:      {dest_path}

  ✅ Your new LocalMind USB is ready!
  Plug it into any computer and enjoy.
""")
    return True

# ── CLI Entry Point ───────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Clone LocalMind USB to another drive.")
    parser.add_argument("--source", default=None, help="Source drive path")
    parser.add_argument("--dest", default=None, help="Destination drive path")
    args = parser.parse_args()

    banner()

    try:
        source_drive, dest_drives, all_drives = detect_drives()

        if not all_drives:
            print(f"\n{P['error']} No drives detected. Make sure your USB is plugged in.")
            sys.exit(1)

        # Choose source
        if args.source:
            source = next((d for d in all_drives if args.source in d["path"]), None)
            if not source:
                print(f"\n{P['error']} Source drive not found: {args.source}")
                sys.exit(1)
        else:
            source = choose_source(source_drive, all_drives)
            if not source:
                sys.exit(0)

        # Choose destination
        available_dests = [d for d in dest_drives if d["path"] != source["path"]]
        if args.dest:
            dest = next((d for d in available_dests if args.dest in d["path"]), None)
            if not dest:
                print(f"\n{P['error']} Destination drive not found: {args.dest}")
                sys.exit(1)
        else:
            dest = choose_dest(source, available_dests)
            if not dest:
                sys.exit(0)

        success = clone_drive(source, dest)
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print(f"\n\n{P['ok']} Interrupted.")
        sys.exit(130)
