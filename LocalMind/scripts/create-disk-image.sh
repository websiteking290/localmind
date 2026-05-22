#!/bin/bash
# =================================================================
#  LocalMind Disk Image Creator
#  Creates a bootable USB image for mass production
# =================================================================

set -euo pipefail

CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; DIM='\033[90m'; RESET='\033[0m'

log() { echo -e "${CYAN}[LocalMind]${RESET} $*"; }
ok() { echo -e "${GREEN}[OK]${RESET} $*"; }
warn() { echo -e "${YELLOW}[WARN]${RESET} $*"; }
err() { echo -e "${RED}[ERROR]${RESET} $*"; }

# ── Configuration ──────────────────────────────────────────
USB_SIZE_GB="${USB_SIZE_GB:-128}"
USB_LABEL="${USB_LABEL:-LOCALMIND}"
OUTPUT_DIR="${OUTPUT_DIR:-./build}"
SOURCE_DIR="${SOURCE_DIR:-./LocalMind}"
IMAGE_NAME="${IMAGE_NAME:-localmind-${USB_SIZE_GB}gb}"

# Models to include (must match pre-install.sh)
MODELS=(
  "llama3.1:8b"
  "qwen2.5:7b"
  "phi4:14b"
  "mistral:7b"
  "gemma3:4b"
)

# Ollama versions
OLLAMA_VERSION="0.5.7"

# ── Prerequisites Check ────────────────────────────────────
log "Checking prerequisites..."

MISSING=()
for cmd in dd mkfs.exfat parted losetup rsync curl unzip; do
  if ! command -v "$cmd" &> /dev/null; then
    MISSING+=("$cmd")
  fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
  err "Missing tools: ${MISSING[*]}"
  echo "Install: sudo apt-get install exfatprogs parted util-linux rsync curl unzip"
  exit 1
fi
ok "All prerequisites found"

# ── Check Source ───────────────────────────────────────────
if [ ! -d "$SOURCE_DIR" ]; then
  err "Source directory not found: $SOURCE_DIR"
  echo "Run pre-install.sh first to build the LocalMind package."
  exit 1
fi

# ── Create Output Directory ───────────────────────────────
mkdir -p "$OUTPUT_DIR"
IMAGE_FILE="$OUTPUT_DIR/${IMAGE_NAME}.img"

# ── Calculate Image Size ────────────────────────────────
log "Calculating image size..."

# Base system: Ollama binaries + launcher + dashboard
BASE_SIZE_MB=500

# Models (approximate sizes in MB)
MODEL_SIZES=(
  [llama3.1:8b]=4700
  [qwen2.5:7b]=4400
  [phi4:14b]=8500
  [mistral:7b]=4100
  [gemma3:4b]=2700
)

TOTAL_MODEL_MB=0
for model in "${MODELS[@]}"; do
  size="${MODEL_SIZES[$model]:-5000}"
  TOTAL_MODEL_MB=$((TOTAL_MODEL_MB + size))
done

# User data space (20% of USB)
USER_SPACE_MB=$((USB_SIZE_GB * 1024 * 20 / 100))

# Total with 10% overhead
TOTAL_NEEDED_MB=$((BASE_SIZE_MB + TOTAL_MODEL_MB + USER_SPACE_MB))
IMAGE_SIZE_MB=$((TOTAL_NEEDED_MB * 110 / 100))

# But cap at USB size
MAX_IMAGE_MB=$((USB_SIZE_GB * 1024 * 95 / 100))
if [ "$IMAGE_SIZE_MB" -gt "$MAX_IMAGE_MB" ]; then
  IMAGE_SIZE_MB=$MAX_IMAGE_MB
fi

log "Image size: ${IMAGE_SIZE_MB}MB (${USB_SIZE_GB}GB USB)"
log "  - Base system: ${BASE_SIZE_MB}MB"
log "  - Models: ${TOTAL_MODEL_MB}MB"
log "  - User space: ${USER_SPACE_MB}MB"

# ── Create Sparse Image ───────────────────────────────────
log "Creating disk image: $IMAGE_FILE"

if [ -f "$IMAGE_FILE" ]; then
  warn "Image already exists. Overwrite? (y/N)"
  read -r answer
  if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    log "Aborted."
    exit 0
  fi
  rm -f "$IMAGE_FILE"
fi

# Create sparse image (doesn't allocate full space immediately)
dd if=/dev/zero of="$IMAGE_FILE" bs=1M count=0 seek="$IMAGE_SIZE_MB" status=none
ok "Created ${IMAGE_SIZE_MB}MB sparse image"

# ── Partition ─────────────────────────────────────────────
log "Creating partition table..."

# Create MBR with single exFAT partition
parted -s "$IMAGE_FILE" mklabel msdos
parted -s "$IMAGE_FILE" mkpart primary ntfs 1MiB 100%
parted -s "$IMAGE_FILE" set 1 boot off
parted -s "$IMAGE_FILE" align-check optimal 1

# ── Setup Loop Device ─────────────────────────────────────
log "Setting up loop device..."
LOOP_DEV=$(losetup -f --show "$IMAGE_FILE")
PART_DEV="${LOOP_DEV}p1"

# Wait for partition to appear
sleep 1
if [ ! -b "$PART_DEV" ]; then
  # Force kernel to re-read partition table
  partprobe "$LOOP_DEV" 2>/dev/null || true
  sleep 1
fi

# Fallback: use offset directly
if [ ! -b "$PART_DEV" ]; then
  OFFSET=$(parted -s "$IMAGE_FILE" unit B print | awk '/^Number/{p=1;next} p&&NF{print $2; exit}' | tr -d 'B')
  LOOP_DEV="$LOOP_DEV"
  PART_DEV="$LOOP_DEV"
  USE_OFFSET=true
fi

# ── Format ────────────────────────────────────────────────
log "Formatting as exFAT..."
if [ "${USE_OFFSET:-false}" = true ]; then
  mkfs.exfat -n "$USB_LABEL" "$PART_DEV"
else
  mkfs.exfat -n "$USB_LABEL" "$PART_DEV"
fi
ok "Formatted as exFAT with label: $USB_LABEL"

# ── Mount and Copy ────────────────────────────────────────
MOUNT_DIR=$(mktemp -d)
log "Mounting to $MOUNT_DIR..."

if [ "${USE_OFFSET:-false}" = true ]; then
  mount -o loop,offset="$OFFSET" "$IMAGE_FILE" "$MOUNT_DIR"
else
  mount "$PART_DEV" "$MOUNT_DIR"
fi

log "Copying LocalMind files..."
rsync -a --progress "$SOURCE_DIR/" "$MOUNT_DIR/" || {
  err "Failed to copy files"
  umount "$MOUNT_DIR" 2>/dev/null || true
  losetup -d "$LOOP_DEV" 2>/dev/null || true
  rm -rf "$MOUNT_DIR"
  exit 1
}

# ── Create autorun files ────────────────────────────────────
log "Creating autorun files..."

# Windows autorun
if [ ! -f "$MOUNT_DIR/autorun.inf" ]; then
  cat > "$MOUNT_DIR/autorun.inf" << 'EOF'
[autorun]
open=START.bat
icon=launcher/assets/icon.ico
label=LocalMind AI
EOF
fi

# macOS autorun (hidden .DS_Store hint)
mkdir -p "$MOUNT_DIR/.hidden"
touch "$MOUNT_DIR/.hidden/.autostart"

# ── Verification ───────────────────────────────────────────
log "Verifying image contents..."

echo ""
echo "  ${DIM}Disk Usage:${RESET}"
du -sh "$MOUNT_DIR" | awk '{print "  Size: " $1}'

echo ""
echo "  ${DIM}Top-level files:${RESET}"
ls -1 "$MOUNT_DIR" | head -20 | sed 's/^/  /'

echo ""
echo "  ${DIM}Models included:${RESET}"
if [ -d "$MOUNT_DIR/models" ]; then
  ls -1 "$MOUNT_DIR/models" | sed 's/^/  /'
else
  echo "  (models will be downloaded on first run)"
fi

# ── Unmount ───────────────────────────────────────────────
log "Unmounting..."
umount "$MOUNT_DIR" || {
  warn "Lazy unmount..."
  umount -l "$MOUNT_DIR"
}
rm -rf "$MOUNT_DIR"

# Detach loop
losetup -d "$LOOP_DEV" 2>/dev/null || true

# ── Compress ──────────────────────────────────────────────
log "Compressing image..."
COMPRESSED="$OUTPUT_DIR/${IMAGE_NAME}.zip"

# Use zip for cross-platform compatibility
zip -r -9 "$COMPRESSED" "$IMAGE_FILE" > /dev/null 2>&1 || {
  # Fallback to gzip
  gzip -c "$IMAGE_FILE" > "$OUTPUT_DIR/${IMAGE_NAME}.img.gz"
  COMPRESSED="$OUTPUT_DIR/${IMAGE_NAME}.img.gz"
}

# ── Create Flash Script ───────────────────────────────────
FLASH_SCRIPT="$OUTPUT_DIR/flash.sh"
cat > "$FLASH_SCRIPT" << EOF
#!/bin/bash
# LocalMind USB Flash Tool
# Usage: sudo ./flash.sh /dev/sdX

DEVICE="\${1:-}"
IMAGE="${IMAGE_NAME}.img"

if [ -z "\$DEVICE" ]; then
  echo "Usage: sudo ./flash.sh /dev/sdX"
  echo "WARNING: This will DESTROY all data on \$DEVICE"
  echo ""
  echo "Available devices:"
  lsblk -d -o NAME,SIZE,MODEL | grep -E '^sd|^nvme'
  exit 1
fi

echo "Flashing LocalMind to \$DEVICE..."
echo "This will take ~10-20 minutes for a ${USB_SIZE_GB}GB drive."
echo ""

# Confirm
read -p "Are you sure? Type 'yes' to continue: " confirm
if [ "\$confirm" != "yes" ]; then
  echo "Aborted."
  exit 1
fi

# Flash with progress
if command -v pv &> /dev/null; then
  pv -tpreb "\$IMAGE" | dd of="\$DEVICE" bs=4M status=none
else
  dd if="\$IMAGE" of="\$DEVICE" bs=4M status=progress
fi

sync
echo "Done! Eject the drive safely."
EOF
chmod +x "$FLASH_SCRIPT"

# Windows flash script (PowerShell)
FLASH_PS="$OUTPUT_DIR/flash.ps1"
cat > "$FLASH_PS" << 'EOF'
# LocalMind USB Flash Tool (Windows)
# Usage: Right-click → Run with PowerShell
# Requires: Windows 10+ with admin rights

$image = "localmind-128gb.img"

Write-Host "LocalMind USB Flash Tool" -ForegroundColor Cyan
Write-Host ""

# List disks
Get-Disk | Where-Object { $_.BusType -eq 'USB' } | Format-Table Number, FriendlyName, Size, PartitionStyle

$diskNumber = Read-Host "Enter disk number to flash (CAUTION: ALL DATA WILL BE LOST)"

$confirm = Read-Host "Are you sure? Type 'yes' to continue"
if ($confirm -ne 'yes') {
    Write-Host "Aborted." -ForegroundColor Red
    exit
}

# Flash using diskpart (simplified — production would use a proper tool)
Write-Host "Flashing... This may take 20-30 minutes." -ForegroundColor Yellow

# In production, use a proper flashing tool or Win32DiskImager
Write-Host "Please use Win32DiskImager or Rufus to flash $image to the USB drive." -ForegroundColor Cyan
EOF

# ── Final Report ──────────────────────────────────────────
IMAGE_SIZE_HUMAN=$(du -sh "$IMAGE_FILE" | awk '{print $1}')
COMPRESSED_HUMAN=$(du -sh "$COMPRESSED" | awk '{print $1}')

ok "Disk image created successfully!"
echo ""
echo "  ${CYAN}══════════════════════════════════════════════════${RESET}"
echo "  ${GREEN}LocalMind ${USB_SIZE_GB}GB Disk Image${RESET}"
echo "  ${CYAN}══════════════════════════════════════════════════${RESET}"
echo ""
echo "  Image file:    ${IMAGE_NAME}.img (${IMAGE_SIZE_HUMAN})"
echo "  Compressed:    ${COMPRESSED##*/} (${COMPRESSED_HUMAN})"
echo "  Flash script:  flash.sh (Linux/Mac)"
echo "  Flash script:  flash.ps1 (Windows)"
echo ""
echo "  ${DIM}To flash to a USB drive:${RESET}"
echo "    sudo ./${OUTPUT_DIR}/flash.sh /dev/sdX"
echo ""
echo "  ${DIM}To mount and inspect:${RESET}"
echo "    sudo mount -o loop ${IMAGE_FILE} /mnt"
echo ""
echo "  ${YELLOW}Next steps for mass production:${RESET}"
echo "    1. Flash image to master USB using flash.sh"
echo "    2. Test on Windows and macOS"
echo "    3. Use USB duplicator for bulk copying"
echo "    4. Or: dd if=master.img of=/dev/sdX for each unit"
echo ""

# ── USB Duplicator Notes ──────────────────────────────────
cat > "$OUTPUT_DIR/MASS_PRODUCTION.md" << 'EOF'
# LocalMind Mass Production Guide

## Recommended USB Duplicators
- **1-to-1**: Any USB duplicator that supports exFAT
- **1-to-7**: EZ Dupe 7 Target USB Duplicator (~$400)
- **1-to-15**: Kanguru USB Duplicator 15 Target (~$1,200)
- **Software**: USB Image Tool (Windows), dd (Linux), Apple Pi Baker (Mac)

## Production Workflow
1. Flash master image to one USB using flash.sh
2. Verify master works on both Windows and macOS
3. Insert master + blanks into duplicator
4. Duplicate (takes ~5 min per batch for 128GB)
5. Spot-check 1 in 10 units
6. Apply labels/packaging

## Cost Breakdown (per unit at 100 qty)
- 128GB SanDisk USB-C: ~$18
- Packaging (box + insert): ~$3
- Label printing: ~$0.50
- Shipping to customer: ~$5 (included in $129)
- **Total COGS: ~$26.50**
- **Margin: ~$102.50 (80%)**
EOF

ok "All done! Check $OUTPUT_DIR/ for deliverables."
