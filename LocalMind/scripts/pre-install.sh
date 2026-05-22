#!/usr/bin/env bash
# =================================================================
#  LocalMind — Pre-Installation Script
#  Run this on the BUILD MACHINE to create a USB image with:
#    - Ollama engine (Windows + macOS)
#    - 5 pre-downloaded quantized models
#    - Branded launcher
#    - Web dashboard
# =================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$PROJECT_DIR/build"
USB_IMAGE_DIR="$BUILD_DIR/usb-image"
MODELS_DIR="$USB_IMAGE_DIR/models"
OLLAMA_DIR="$USB_IMAGE_DIR/ollama"
DASHBOARD_DIR="$USB_IMAGE_DIR/dashboard"
LAUNCHER_DIR="$USB_IMAGE_DIR/launcher"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; DIM='\033[0;90m'; RESET='\033[0m'

log() { echo -e "${CYAN}[LocalMind]${RESET} $1"; }
ok() { echo -e "${GREEN}[OK]${RESET} $1"; }
warn() { echo -e "${YELLOW}[WARN]${RESET} $1"; }
err() { echo -e "${RED}[ERROR]${RESET} $1"; }

# ── Configuration ─────────────────────────────────────────
OLLAMA_VERSION="0.6.5"

# Models to pre-install (Q4_K_M quantization — best speed/quality for CPU)
declare -A MODELS=(
    ["llama3.1:8b"]="LLaMA 3.1 8B — General chat, coding, reasoning"
    ["qwen2.5:7b"]="Qwen 2.5 7B — Coding, reasoning, multilingual"
    ["phi4:14b"]="Phi-4 14B — Best reasoning, math, instruction following"
    ["mistral:7b"]="Mistral 7B — Fast general-purpose"
    ["gemma3:4b"]="Gemma 3 4B — Lightweight, vision-ready"
)

# Estimated sizes (GB) for Q4_K_M quantization
# These are approximate — actual sizes vary by model version
declare -A MODEL_SIZES=(
    ["llama3.1:8b"]="4.7"
    ["qwen2.5:7b"]="4.4"
    ["phi4:14b"]="8.5"
    ["mistral:7b"]="4.1"
    ["gemma3:4b"]="2.7"
)

# ── Step 1: Setup ───────────────────────────────────────
log "Starting LocalMind USB image build..."
log "Project: $PROJECT_DIR"
log "Build: $BUILD_DIR"
log ""

# Clean previous build
if [ -d "$BUILD_DIR" ]; then
    warn "Cleaning previous build..."
    rm -rf "$BUILD_DIR"
fi

mkdir -p "$USB_IMAGE_DIR" "$MODELS_DIR" "$OLLAMA_DIR" "$DASHBOARD_DIR" "$LAUNCHER_DIR"

# Calculate total size
TOTAL_SIZE=0
for model in "${!MODELS[@]}"; do
    size="${MODEL_SIZES[$model]}"
    TOTAL_SIZE=$(echo "$TOTAL_SIZE + $size" | bc)
done
TOTAL_SIZE=$(echo "$TOTAL_SIZE + 0.5" | bc)  # + engine overhead

log "Models to install:"
for model in "${!MODELS[@]}"; do
    size="${MODEL_SIZES[$model]}"
    name="${MODELS[$model]}"
    log "  • $model (~${size}GB) — $name"
done
log ""
log "Estimated total: ~${TOTAL_SIZE}GB"
log "Recommended USB: 128GB+"
log ""

# ── Step 2: Download Ollama Engine ──────────────────────
log "Step 2/5: Downloading Ollama engines..."

# Download Ollama for each platform
PLATFORMS=("darwin" "linux" "windows")
for platform in "${PLATFORMS[@]}"; do
    if [ "$platform" = "windows" ]; then
        ext="zip"
    else
        ext="tgz"
    fi
    
    url="https://github.com/ollama/ollama/releases/download/v${OLLAMA_VERSION}/ollama-${platform}-${ext}"
    dest="$OLLAMA_DIR/ollama-${platform}.${ext}"
    
    if [ ! -f "$dest" ]; then
        log "  Downloading Ollama ${OLLAMA_VERSION} for ${platform}..."
        curl -L --fail --progress-bar "$url" -o "$dest" || {
            err "Failed to download Ollama for ${platform}"
            exit 1
        }
        ok "  Ollama ${platform} downloaded"
    else
        ok "  Ollama ${platform} already cached"
    fi
done

# ── Step 3: Download Models ─────────────────────────────
log ""
log "Step 3/5: Downloading AI models..."
log "This will take 20-60 minutes depending on internet speed."
log ""

# Check if Ollama is installed locally for pulling models
if ! command -v ollama &> /dev/null; then
    err "Ollama not found on build machine. Installing..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Start Ollama server in background for model pulls
log "Starting Ollama server..."
export OLLAMA_MODELS="$MODELS_DIR"
ollama serve &
OLLAMA_PID=$!
sleep 5

# Pull each model
for model in "${!MODELS[@]}"; do
    size="${MODEL_SIZES[$model]}"
    name="${MODELS[$model]}"
    
    log "Pulling $model (~${size}GB)..."
    log "  $name"
    
    if ollama pull "$model" 2>&1; then
        ok "  $model pulled successfully"
    else
        err "  Failed to pull $model"
        kill $OLLAMA_PID 2>/dev/null
        exit 1
    fi
    log ""
done

# Stop Ollama server
log "Stopping Ollama server..."
kill $OLLAMA_PID 2>/dev/null || true
wait $OLLAMA_PID 2>/dev/null || true
ok "Ollama server stopped"

# ── Step 4: Copy Launcher & Dashboard ───────────────────
log ""
log "Step 4/5: Copying launcher and dashboard..."

# Copy dashboard files
cp -r "$PROJECT_DIR/dashboard/dist" "$DASHBOARD_DIR/" 2>/dev/null || {
    warn "Dashboard dist/ not found — will need to build separately"
}

# Copy launcher files
cp -r "$PROJECT_DIR/launcher" "$LAUNCHER_DIR/" 2>/dev/null || {
    warn "Launcher not found — will need to build separately"
}

# ── Step 5: Create USB Image ────────────────────────────
log ""
log "Step 5/5: Creating USB disk image..."

# Create a metadata file
mkdir -p "$USB_IMAGE_DIR/.localmind"
cat > "$USB_IMAGE_DIR/.localmind/manifest.json" <<EOF
{
  "product": "LocalMind",
  "version": "1.0.0",
  "build_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "ollama_version": "${OLLAMA_VERSION}",
  "models": [
$(for model in "${!MODELS[@]}"; do
    size="${MODEL_SIZES[$model]}"
    name="${MODELS[$model]}"
    echo "    {\"name\": \"$model\", \"size_gb\": $size, \"description\": \"$name\"},"
done | sed '$ s/,$//')
  ],
  "platforms": ["windows", "macos", "linux"],
  "total_size_gb": $TOTAL_SIZE
}
EOF

# Create README for the USB
cat > "$USB_IMAGE_DIR/README.txt" <<'EOF'
╔══════════════════════════════════════════════════════════════╗
║                    LocalMind AI USB                          ║
║                                                              ║
║  Plug-and-play offline AI. No internet required.             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

QUICK START:

Windows:
  1. Plug in the USB drive
  2. Open the USB drive in File Explorer
  3. Double-click "LocalMind.exe"
  4. Wait 30 seconds for AI to load
  5. Your browser will open automatically

macOS:
  1. Plug in the USB drive
  2. Open Finder → select the USB drive
  3. Double-click "LocalMind.app"
  4. Wait 30 seconds for AI to load
  5. Your browser will open automatically

SYSTEM REQUIREMENTS:
  • Windows 10+ or macOS 12+
  • 8GB RAM minimum (16GB recommended)
  • USB 3.0 port (USB 3.2 recommended for best speed)
  • No GPU required — runs on CPU

INCLUDED MODELS:
  • LLaMA 3.1 8B — General chat, coding
  • Qwen 2.5 7B — Coding, reasoning
  • Phi-4 14B — Best reasoning, math
  • Mistral 7B — Fast general-purpose
  • Gemma 3 4B — Lightweight, vision

SUPPORT:
  • Email: support@localmind.ai
  • Documentation: https://docs.localmind.ai

© 2026 LocalMind. All rights reserved.
EOF

# ── Final Summary ───────────────────────────────────────
log ""
log "═══════════════════════════════════════════════════════════"
ok "  USB IMAGE BUILD COMPLETE!"
log "═══════════════════════════════════════════════════════════"
log ""
log "Output: $USB_IMAGE_DIR"
log ""

# Calculate actual size
if command -v du &> /dev/null; then
    ACTUAL_SIZE=$(du -sh "$USB_IMAGE_DIR" | cut -f1)
    log "Actual size: $ACTUAL_SIZE"
fi

log ""
log "NEXT STEPS:"
log "  1. Test the image on a USB drive:"
log "     cp -r $USB_IMAGE_DIR/* /Volumes/YOUR_USB/"
log ""
log "  2. Run the launcher and verify models load"
log ""
log "  3. For mass production, create a disk image:"
log "     $PROJECT_DIR/scripts/create-disk-image.sh"
log ""
ok "Build complete!"
