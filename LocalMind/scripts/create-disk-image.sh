#!/bin/bash
# =================================================================
#  LocalMind Disk Image Creator
#  =============================
#  Burns the complete LocalMind product to a USB drive.
#
#  Usage:
#    sudo ./create-disk-image.sh              # Auto-detect USB
#    sudo ./create-disk-image.sh /dev/disk2   # Target specific disk
#    ./create-disk-image.sh --dry-run         # Create image without USB
# =================================================================

set -euo pipefail

# ── Colors ──────────────────────────────────────────────
CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; DIM='\033[90m'; RESET='\033[0m'
log()  { echo -e "${CYAN}[LocalMind]${RESET} $*"; }
ok()   { echo -e "${GREEN}[OK]${RESET} $*"; }
warn() { echo -e "${YELLOW}[WARN]${RESET} $*"; }
err()  { echo -e "${RED}[ERROR]${RESET} $*"; }

# ── Paths ───────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USB_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$USB_ROOT/build"
CACHE_DIR="$BUILD_DIR/cache"
MASTER_DIR="$BUILD_DIR/master-image"
TMP_DIR="$BUILD_DIR/tmp"
LOCALMIND_DIR="$USB_ROOT/LocalMind"

# ── Settings ────────────────────────────────────────────
USB_LABEL="LocalMind"
USB_SIZE_GB=128
MODELS="llama3.1 qwen2.5 phi4 mistral gemma3"
OLLAMA_VERSION="0.6.5"

# ── Parse args ──────────────────────────────────────────
TARGET_DISK=""
DRY_RUN=false
SKIP_OLLAMA=false
SKIP_MODELS=false

FORCE=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)     DRY_RUN=true; shift ;;
    --skip-ollama) SKIP_OLLAMA=true; shift ;;
    --skip-models) SKIP_MODELS=true; shift ;;
    --force)       FORCE=true; shift ;;
    /dev/*)        TARGET_DISK="$1"; shift ;;
    *)             err "Unknown arg: $1"; exit 1 ;;
  esac
done

# ── Detect USB ──────────────────────────────────────────
detect_usb() {
  log "Scanning for USB drives..."
  local usbs
  usbs=$(diskutil list external physical 2>/dev/null | grep "^/dev/disk" | awk '{print $1}' || true)
  
  if [[ -z "$usbs" ]]; then
    err "No external USB drives found."
    err "Plug in your USB drive and try again."
    err "Or use --dry-run to create an image without a USB."
    exit 1
  fi
  
  local count
  count=$(echo "$usbs" | wc -l | tr -d ' ')
  
  if [[ "$count" -eq 1 ]]; then
    TARGET_DISK="$usbs"
    log "Found USB: $TARGET_DISK"
  else
    echo ""
    echo "Multiple USB drives found:"
    echo "$usbs" | while read -r disk; do
      local info
      info=$(diskutil info "$disk" 2>/dev/null | grep -E "(Device Identifier|Total Size|Device Node)" | head -3)
      echo "  $disk"
      echo "$info" | sed 's/^/    /'
    done
    echo ""
    err "Please specify which disk: sudo $0 /dev/diskX"
    exit 1
  fi
}

# ── Safety Check ────────────────────────────────────────
safety_check() {
  if [[ "$DRY_RUN" == true ]]; then
    log "DRY RUN mode — no USB will be written"
    return
  fi
  
  if [[ -z "$TARGET_DISK" ]]; then
    detect_usb
  fi
  
  # Verify it's external
  local is_internal
  is_internal=$(diskutil info "$TARGET_DISK" 2>/dev/null | grep "Protocol" | grep -i "PCI\|SATA\|NVMe" || true)
  if [[ -n "$is_internal" ]]; then
    err "$TARGET_DISK appears to be an INTERNAL drive."
    err "Refusing to erase internal storage."
    exit 1
  fi
  
  local disk_name
  disk_name=$(diskutil info "$TARGET_DISK" 2>/dev/null | grep "Device Identifier" | awk '{print $3}')
  local disk_size
  disk_size=$(diskutil info "$TARGET_DISK" 2>/dev/null | grep "Total Size" | awk '{print $3,$4}')
  
  echo ""
  echo -e "${RED}╔════════════════════════════════════════════════════════════╗${RESET}"
  echo -e "${RED}║  WARNING: This will ERASE ALL DATA on $TARGET_DISK${RESET}"
  echo -e "${RED}║  Size: $disk_size${RESET}"
  echo -e "${RED}╚════════════════════════════════════════════════════════════╝${RESET}"
  echo ""
  if [[ "$FORCE" != true ]]; then
    read -rp "Type ERASE to confirm: " confirm
    if [[ "$confirm" != "ERASE" ]]; then
      err "Aborted."
      exit 1
    fi
  else
    warn "Force mode — skipping confirmation"
  fi
}

# ── Prepare Directories ─────────────────────────────────
prepare_dirs() {
  log "Preparing build directories..."
  mkdir -p "$CACHE_DIR" "$MASTER_DIR" "$TMP_DIR"
  mkdir -p "$MASTER_DIR/LocalMind/launcher"
  mkdir -p "$MASTER_DIR/LocalMind/dashboard"
  mkdir -p "$MASTER_DIR/LocalMind/models"
  mkdir -p "$MASTER_DIR/LocalMind/data"
  mkdir -p "$MASTER_DIR/LocalMind/.localmind"
  ok "Directories ready"
}

# ── Copy Launcher Code ──────────────────────────────────
copy_launcher() {
  log "Copying launcher code..."
  
  cp "$LOCALMIND_DIR/launcher/launcher.py" "$MASTER_DIR/LocalMind/launcher/"
  cp "$LOCALMIND_DIR/launcher/update.py" "$MASTER_DIR/LocalMind/launcher/"
  cp "$LOCALMIND_DIR/launcher/START.bat" "$MASTER_DIR/LocalMind/launcher/"
  cp "$LOCALMIND_DIR/launcher/start.sh" "$MASTER_DIR/LocalMind/launcher/"
  cp "$LOCALMIND_DIR/dashboard/server.py" "$MASTER_DIR/LocalMind/dashboard/"
  
  ok "Launcher copied"
}

# ── Download Ollama ─────────────────────────────────────
download_ollama() {
  if [[ "$SKIP_OLLAMA" == true ]]; then
    warn "Skipping Ollama download (--skip-ollama)"
    return
  fi
  
  log "Downloading Ollama engines..."
  
  local ollama_dir="$MASTER_DIR/LocalMind/ollama"
  mkdir -p "$ollama_dir"
  
  # macOS (Apple Silicon + Intel universal)
  local macos_url="https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-darwin"
  local macos_bin="$ollama_dir/ollama-darwin"
  
  if [[ ! -f "$macos_bin" ]]; then
    log "Downloading macOS Ollama..."
    curl -L --progress-bar "$macos_url" -o "$macos_bin"
    chmod +x "$macos_bin"
    ok "macOS Ollama downloaded"
  else
    ok "macOS Ollama cached"
  fi
  
  # Windows
  local win_url="https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-windows-amd64.zip"
  local win_zip="$CACHE_DIR/ollama-windows.zip"
  local win_dir="$ollama_dir/windows"
  
  if [[ ! -d "$win_dir" ]]; then
    log "Downloading Windows Ollama..."
    curl -L --progress-bar "$win_url" -o "$win_zip"
    mkdir -p "$win_dir"
    unzip -q "$win_zip" -d "$win_dir"
    ok "Windows Ollama downloaded"
  else
    ok "Windows Ollama cached"
  fi
  
  # Linux
  local linux_url="https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-linux-amd64"
  local linux_bin="$ollama_dir/ollama-linux"
  
  if [[ ! -f "$linux_bin" ]]; then
    log "Downloading Linux Ollama..."
    curl -L --progress-bar "$linux_url" -o "$linux_bin"
    chmod +x "$linux_bin"
    ok "Linux Ollama downloaded"
  else
    ok "Linux Ollama cached"
  fi
}

# ── Download Models ─────────────────────────────────────
download_models() {
  if [[ "$SKIP_MODELS" == true ]]; then
    warn "Skipping model download (--skip-models)"
    return
  fi
  
  log "Downloading AI models (this will take 30-60 minutes)..."
  
  # Use system Ollama or download a temporary one
  local ollama_cmd
  if command -v ollama &> /dev/null; then
    ollama_cmd="ollama"
  elif [[ -f "$MASTER_DIR/LocalMind/ollama/ollama-darwin" ]]; then
    ollama_cmd="$MASTER_DIR/LocalMind/ollama/ollama-darwin"
  else
    err "Ollama not found. Install it first: brew install ollama"
    exit 1
  fi
  
  # Set models directory to our USB location
  export OLLAMA_MODELS="$MASTER_DIR/LocalMind/models"
  mkdir -p "$OLLAMA_MODELS"
  
  for model in $MODELS; do
    log "Pulling $model..."
    "$ollama_cmd" pull "$model"
    ok "$model downloaded"
  done
  
  # Calculate sizes
  local total_size
  total_size=$(du -sh "$OLLAMA_MODELS" | cut -f1)
  ok "All models downloaded. Total: $total_size"
}

# ── Generate Manifest ───────────────────────────────────
generate_manifest() {
  log "Generating manifest..."
  
  local models_json="[]"
  
  if [[ "$SKIP_MODELS" != true && -d "$MASTER_DIR/LocalMind/models" ]]; then
    # Build model info from actual files
    models_json="["
    local first=true
    for model in $MODELS; do
      local size_gb="unknown"
      local manifest_file="$MASTER_DIR/LocalMind/models/manifests/registry.ollama.ai/library/${model}/latest"
      if [[ -f "$manifest_file" ]]; then
        local size_bytes
        size_bytes=$(find "$MASTER_DIR/LocalMind/models/blobs" -name "*" -type f -exec stat -f%z {} + 2>/dev/null | awk '{s+=$1} END {print s}' || echo "0")
        size_gb=$(echo "scale=1; $size_bytes / 1024 / 1024 / 1024" | bc 2>/dev/null || echo "?")
      fi
      
      [[ "$first" == true ]] || models_json+=","
      first=false
      
      case $model in
        llama3.1)  desc="Meta's flagship. Best for general chat, coding, creative writing." ;;
        qwen2.5)   desc="Alibaba's best. Superior coding and multilingual support." ;;
        phi4)      desc="Microsoft's most capable. Complex reasoning and math." ;;
        mistral)   desc="Fast and efficient. Perfect for quick queries." ;;
        gemma3)    desc="Google's lightweight model. Ideal for older hardware." ;;
        *)         desc="General purpose AI model" ;;
      esac
      
      models_json+="{\"name\":\"${model}:latest\",\"size_gb\":\"${size_gb}\",\"description\":\"$desc\"}"
    done
    models_json+="]"
  fi
  
  cat > "$MASTER_DIR/LocalMind/.localmind/manifest.json" <<EOF
{
  "product": "LocalMind",
  "version": "1.0.0",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "ollama_version": "$OLLAMA_VERSION",
  "models": $models_json,
  "platforms": ["darwin", "windows", "linux"],
  "requirements": {
    "ram_gb": 8,
    "ram_gb_recommended": 16,
    "usb_size_gb": 128,
    "models_size_gb": 25
  }
}
EOF
  
  ok "Manifest generated"
}

# ── Create Root Launchers ─────────────────────────────────
create_root_launchers() {
  log "Creating root launchers..."
  
  # macOS: .app bundle (simplified)
  local app_dir="$MASTER_DIR/LocalMind.app"
  mkdir -p "$app_dir/Contents/MacOS"
  
  cat > "$app_dir/Contents/MacOS/LocalMind" <<'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USB_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$USB_ROOT/LocalMind/launcher"
exec ./start.sh
EOF
  chmod +x "$app_dir/Contents/MacOS/LocalMind"
  
  # Windows: autorun.inf
  cat > "$MASTER_DIR/autorun.inf" <<EOF
[AutoRun]
label=$USB_LABEL
icon=LocalMind.ico
open=LocalMind\launcher\START.bat
action=Start LocalMind AI
EOF
  
  # Root shortcuts
  cat > "$MASTER_DIR/START-Windows.bat" <<'EOF'
@echo off
cd /d "%~dp0LocalMind\launcher"
call START.bat
EOF
  
  cat > "$MASTER_DIR/START-macOS.command" <<'EOF'
#!/bin/bash
cd "$(dirname "$0")/LocalMind/launcher"
exec ./start.sh
EOF
  chmod +x "$MASTER_DIR/START-macOS.command"
  
  ok "Root launchers created"
}

# ── Copy Sales Website ──────────────────────────────────
copy_website() {
  log "Copying sales website..."
  
  if [[ -f "$LOCALMIND_DIR/website/index.html" ]]; then
    mkdir -p "$MASTER_DIR/website"
    cp "$LOCALMIND_DIR/website/index.html" "$MASTER_DIR/website/"
    ok "Website copied"
  else
    warn "No website found"
  fi
}

# ── Burn to USB ───────────────────────────────────────
burn_usb() {
  if [[ "$DRY_RUN" == true ]]; then
    log "Dry run — skipping USB burn"
    return
  fi
  
  log "Preparing to burn to $TARGET_DISK..."
  
  # Unmount disk
  log "Unmounting $TARGET_DISK..."
  diskutil unmountDisk "$TARGET_DISK" &>/dev/null || true
  
  # Format as exFAT (cross-platform compatible)
  log "Formatting as exFAT..."
  diskutil eraseDisk exFAT "$USB_LABEL" GPT "$TARGET_DISK"
  
  # Get mount point
  local mount_point
  mount_point=$(diskutil info "$TARGET_DISK" 2>/dev/null | grep "Mount Point" | sed 's/.*Mount Point: *//' || echo "/Volumes/$USB_LABEL")
  
  if [[ ! -d "$mount_point" ]]; then
    mount_point="/Volumes/$USB_LABEL"
  fi
  
  # Wait for mount
  local retries=0
  while [[ ! -d "$mount_point" && $retries -lt 30 ]]; do
    sleep 1
    ((retries++))
  done
  
  if [[ ! -d "$mount_point" ]]; then
    err "USB did not mount at expected location: $mount_point"
    exit 1
  fi
  
  log "USB mounted at: $mount_point"
  
  # Copy files
  log "Copying LocalMind to USB (this will take 10-30 minutes)..."
  
  # Use rsync if available
  if command -v rsync &> /dev/null; then
    rsync -a --progress "$MASTER_DIR/" "$mount_point/"
  else
    cp -R "$MASTER_DIR/"* "$mount_point/"
  fi
  
  ok "Files copied to USB"
  
  # Verify
  log "Verifying USB contents..."
  local usb_manifest
  usb_manifest="$mount_point/LocalMind/.localmind/manifest.json"
  if [[ -f "$usb_manifest" ]]; then
    ok "Manifest found on USB"
    local model_count
    model_count=$(grep -c '"name"' "$usb_manifest" || echo "0")
    ok "$model_count models in manifest"
  else
    warn "Manifest not found on USB"
  fi
  
  # Eject
  log "Ejecting USB..."
  diskutil eject "$TARGET_DISK" &>/dev/null || true
  
  ok "USB ejected safely"
}

# ── Create Disk Image File ────────────────────────────────
create_dmg() {
  if [[ "$DRY_RUN" != true ]]; then
    return
  fi
  
  log "Creating disk image file..."
  
  local dmg_name="LocalMind-v1.0.dmg"
  local dmg_path="$BUILD_DIR/$dmg_name"
  
  # Calculate size needed
  local size_mb
  size_mb=$(du -sm "$MASTER_DIR" | cut -f1)
  size_mb=$((size_mb + 500))  # Add buffer
  
  # Create sparse bundle for efficiency
  log "Creating ${size_mb}MB sparse image..."
  hdiutil create -size "${size_mb}m" -fs exFAT -volname "$USB_LABEL" -type SPARSE "$dmg_path" &>/dev/null
  
  local sparse_path="${dmg_path}.sparseimage"
  local mount_point="/Volumes/$USB_LABEL"
  
  # Mount
  hdiutil attach "$sparse_path" &>/dev/null
  
  # Copy
  log "Copying to image..."
  cp -R "$MASTER_DIR/"* "$mount_point/"
  
  # Detach
  hdiutil detach "$mount_point" &>/dev/null
  
  # Convert to compressed DMG
  log "Compressing..."
  local final_dmg="$BUILD_DIR/LocalMind-v1.0-compressed.dmg"
  hdiutil convert "$sparse_path" -format UDZO -o "$final_dmg" &>/dev/null
  
  # Remove sparse
  rm "$sparse_path"
  
  ok "Disk image created: $final_dmg"
  ls -lh "$final_dmg"
}

# ── Final Report ────────────────────────────────────────
report() {
  echo ""
  echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${RESET}"
  echo -e "${GREEN}║           LocalMind USB Image Complete!                    ║${RESET}"
  echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${RESET}"
  echo ""
  
  local total_size
  total_size=$(du -sh "$MASTER_DIR" 2>/dev/null | cut -f1 || echo "unknown")
  
  echo "  Product:      LocalMind v1.0"
  echo "  Size:         $total_size"
  echo "  Models:       $MODELS"
  echo "  Ollama:       v$OLLAMA_VERSION"
  echo ""
  
  if [[ "$DRY_RUN" == true ]]; then
    echo "  Disk image:   $BUILD_DIR/LocalMind-v1.0-compressed.dmg"
    echo ""
    echo "  To burn to USB:"
    echo "    sudo $0 /dev/diskX"
  else
    echo "  USB:          $TARGET_DISK"
    echo "  Label:        $USB_LABEL"
    echo ""
    echo "  Plug it in and:"
    echo "    Windows → Double-click START-Windows.bat"
    echo "    macOS   → Double-click START-macOS.command"
  fi
  echo ""
}

# ── Main ────────────────────────────────────────────────
main() {
  echo ""
  echo -e "${CYAN}    _       _       __  __             _   ${RESET}"
  echo -e "${CYAN}   | |     | |     |  \/  |           | |  ${RESET}"
  echo -e "${CYAN}   | | ___ | |_   _| \  / | __ _ _ __ | |_ ${RESET}"
  echo -e "${CYAN}   | |/ _ \| | | | | |\/| |/ _\` | '_ \| __|${RESET}"
  echo -e "${CYAN}   | | (_) | | |_| | |  | | (_| | | | | |_ ${RESET}"
  echo -e "${CYAN}   |_|\___/|_|\__, |_|  |_|\__,_|_| |_|\__|${RESET}"
  echo -e "${CYAN}               __/ |                        ${RESET}"
  echo -e "${CYAN}              |___/                         ${RESET}"
  echo ""
  
  safety_check
  prepare_dirs
  copy_launcher
  download_ollama
  download_models
  generate_manifest
  create_root_launchers
  copy_website
  burn_usb
  create_dmg
  report
}

main "$@"
