#!/bin/bash
# =================================================================
#  LocalMind Model Downloader
#  Download models DIRECTLY to USB using USB Ollama binary
#  NEVER use system 'ollama' command — it ignores OLLAMA_MODELS
# =================================================================

CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; RESET='\033[0m'

# USB paths
USB_ROOT="/Volumes/LocalMind/LocalMind"
OLLAMA_BIN="${USB_ROOT}/ollama/ollama"
MODELS_DIR="${USB_ROOT}/models"

# Verify USB is mounted
if [ ! -d "$USB_ROOT" ]; then
    echo -e "${RED}❌ USB not mounted at /Volumes/LocalMind/${RESET}"
    exit 1
fi

# Verify USB Ollama binary exists
if [ ! -f "$OLLAMA_BIN" ]; then
    echo -e "${RED}❌ USB Ollama binary not found:${RESET} $OLLAMA_BIN"
    exit 1
fi

# Kill any running Ollama to prevent conflicts
echo -e "${YELLOW}🧹 Stopping any running Ollama...${RESET}"
pkill -f "ollama" 2>/dev/null || true
sleep 2

# Set environment to force USB storage
export OLLAMA_MODELS="$MODELS_DIR"
export OLLAMA_HOST="127.0.0.1"
export OLLAMA_PORT="11434"
export OLLAMA_ORIGINS="*"

# Start USB Ollama server
echo -e "${CYAN}🚀 Starting USB Ollama server...${RESET}"
nohup "$OLLAMA_BIN" serve > /tmp/usb_ollama_download.log 2>&1 &
OLLAMA_PID=$!
sleep 3

# Verify server is running
echo -e "${CYAN}🔍 Verifying server...${RESET}"
if ! curl -s --max-time 5 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo -e "${RED}❌ USB Ollama failed to start!${RESET}"
    echo "Check: /tmp/usb_ollama_download.log"
    exit 1
fi
echo -e "${GREEN}✓ USB Ollama running on port 11434${RESET}"
echo ""

# Models to download
MODELS=(
    "llama3.1:70b"
    "qwen2.5:32b"
    "deepseek-r1:14b"
    "gemma4"
    "phi4"
    "mistral-nemo"
)

echo -e "${CYAN}📦 Downloading ${#MODELS[@]} models to USB...${RESET}"
echo -e "${YELLOW}   This will take 2-3 hours. Do not unplug USB.${RESET}"
echo ""

# Download each model
for model in "${MODELS[@]}"; do
    echo -e "${CYAN}⬇ Downloading $model...${RESET}"
    "$OLLAMA_BIN" pull "$model"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $model complete${RESET}"
    else
        echo -e "${RED}✗ $model failed${RESET}"
    fi
    echo ""
done

# Verify all models
echo -e "${CYAN}🔍 Verifying downloads...${RESET}"
DOWNLOADED_MODELS=$($OLLAMA_BIN list 2>/dev/null | grep -v "^NAME" | grep -v "^$" | wc -l | tr -d ' ')
echo -e "${GREEN}✓ $DOWNLOADED_MODELS models on USB${RESET}"

# Check disk usage
echo ""
echo -e "${CYAN}📊 USB Disk Usage:${RESET}"
du -sh "$MODELS_DIR"
df -h /Volumes/LocalMind/ | tail -1 | awk '{print "  Total: " $2 ", Used: " $3 ", Free: " $4}'

# Stop server
kill $OLLAMA_PID 2>/dev/null || true

echo ""
echo -e "${GREEN}✅ All models downloaded to USB!${RESET}"
echo ""
echo "Next: Run final-cleanup.sh to update manifest"
