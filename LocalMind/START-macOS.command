#!/bin/bash
# =================================================================
#  LocalMind AI — macOS Standalone Launcher
#  Updated for new dashboard fixes and better model support
# =================================================================

# ANSI colors
CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; BLUE='\033[34m'; RESET='\033[0m'

# Get USB root directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USB_ROOT="${SCRIPT_DIR}/LocalMind"
LAUNCHER_DIR="${USB_ROOT}/launcher"
OLLAMA_DIR="${USB_ROOT}/ollama"
MODELS_DIR="${USB_ROOT}/models"
DASHBOARD_DIR="${USB_ROOT}/dashboard"
DATA_DIR="${USB_ROOT}/data"

OLLAMA_HOST="127.0.0.1"
OLLAMA_PORT="11434"
OLLAMA_URL="http://${OLLAMA_HOST}:${OLLAMA_PORT}"
DASHBOARD_PORT="3000"
DASHBOARD_URL="http://localhost:${DASHBOARD_PORT}"

echo ""
echo -e "${CYAN}    ╔═══════════════════════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}    ║                                                           ║${RESET}"
echo -e "${CYAN}    ║              🤖  LOCALMIND AI - USB LAUNCHER               ║${RESET}"
echo -e "${CYAN}    ║                                                           ║${RESET}"
echo -e "${CYAN}    ║      Run AI models completely offline - No internet       ║${RESET}"
echo -e "${CYAN}    ║                                                           ║${RESET}"
echo -e "${CYAN}    ╚═══════════════════════════════════════════════════════════╝${RESET}"
echo ""

# ── Check Python ─────────────────────────────────────────────
PYTHON_EXE=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_EXE="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_EXE="python"
fi

if [ -z "$PYTHON_EXE" ]; then
    echo -e "${RED}⚠ Python is not installed on this Mac.${RESET}"
    echo ""
    echo -e "${YELLOW}Installing Python automatically...${RESET}"
    echo ""
    
    # Check if Homebrew is installed
    if command -v brew >/dev/null 2>&1; then
        echo "⬇ Installing Python via Homebrew..."
        brew install python3
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Homebrew install failed.${RESET}"
            echo "Please install Python manually from https://www.python.org/downloads/"
            exit 1
        fi
        PYTHON_EXE="python3"
    else
        echo -e "${RED}❌ Python not found and Homebrew is not installed.${RESET}"
        echo ""
        echo "Please install Python 3.9+ from:"
        echo "https://www.python.org/downloads/macos/"
        echo ""
        echo "Or install Homebrew first:"
        echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        exit 1
    fi
fi

echo -e "${GREEN}✓ Python is ready:${RESET}"
$PYTHON_EXE --version
echo ""

# ── Verify USB Structure ──────────────────────────────────────
echo -e "${BLUE}📍 USB Drive:${RESET} ${USB_ROOT}"
echo ""

if [ ! -d "$USB_ROOT" ]; then
    echo -e "${RED}❌ LocalMind folder not found at:${RESET} ${USB_ROOT}"
    echo "Make sure the USB is properly mounted."
    exit 1
fi

# Check key directories
for dir in "$OLLAMA_DIR" "$MODELS_DIR" "$DASHBOARD_DIR"; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}❌ Missing directory:${RESET} ${dir}"
        exit 1
    fi
done

echo -e "${GREEN}✓ USB structure verified${RESET}"
echo ""

# ── Kill Existing Processes ──────────────────────────────────
echo -e "${YELLOW}🧹 Cleaning up existing processes...${RESET}"

# Kill existing Ollama
OLLAMA_PIDS=$(pgrep -f "ollama serve" 2>/dev/null)
if [ -n "$OLLAMA_PIDS" ]; then
    echo "  Stopping existing Ollama server..."
    kill $OLLAMA_PIDS 2>/dev/null
    sleep 2
fi

# Kill existing dashboard
DASHBOARD_PIDS=$(pgrep -f "${DASHBOARD_DIR}/server.py" 2>/dev/null)
if [ -n "$DASHBOARD_PIDS" ]; then
    echo "  Stopping existing dashboard..."
    kill $DASHBOARD_PIDS 2>/dev/null
    sleep 1
fi

echo -e "${GREEN}✓ Cleanup complete${RESET}"
echo ""

# ── Find Ollama Binary ─────────────────────────────────────
OLLAMA_BIN=""
if [ -f "${OLLAMA_DIR}/ollama" ]; then
    OLLAMA_BIN="${OLLAMA_DIR}/ollama"
elif [ -f "${OLLAMA_DIR}/macos/ollama" ]; then
    OLLAMA_BIN="${OLLAMA_DIR}/macos/ollama"
fi

if [ -z "$OLLAMA_BIN" ]; then
    # Check system PATH
    OLLAMA_BIN=$(which ollama 2>/dev/null)
fi

if [ -z "$OLLAMA_BIN" ] || [ ! -f "$OLLAMA_BIN" ]; then
    echo -e "${RED}❌ Ollama binary not found!${RESET}"
    echo "Expected at: ${OLLAMA_DIR}/ollama"
    exit 1
fi

echo -e "${GREEN}✓ Ollama binary:${RESET} ${OLLAMA_BIN}"

# Check Ollama version
OLLAMA_VERSION=$($OLLAMA_BIN --version 2>/dev/null | head -1)
echo -e "${GREEN}✓ Version:${RESET} ${OLLAMA_VERSION}"
echo ""

# ── Start Ollama Server ────────────────────────────────────
echo -e "${CYAN}🚀 Starting Ollama AI Engine...${RESET}"
echo -e "${CYAN}   Server will run at ${OLLAMA_URL}${RESET}"
echo ""

# Create data directory
mkdir -p "$DATA_DIR"

# Export environment variables
export OLLAMA_MODELS="$MODELS_DIR"
export OLLAMA_HOST="$OLLAMA_HOST"
export OLLAMA_PORT="$OLLAMA_PORT"
export OLLAMA_ORIGINS="*"

# Start Ollama in background
nohup "$OLLAMA_BIN" serve > /tmp/localmind_ollama.log 2>&1 &
echo $! > /tmp/localmind_ollama.pid
OLLAMA_PID=$(cat /tmp/localmind_ollama.pid)

# Wait for Ollama to be ready
echo -n "⏳ Waiting for Ollama to start"
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    sleep 1
    if curl -s --max-time 2 "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✓ Ollama is running!${RESET}"
        break
    fi
    WAITED=$((WAITED + 1))
    if [ $((WAITED % 5)) -eq 0 ]; then
        echo -n "."
    fi
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo ""
    echo -e "${RED}❌ Ollama failed to start within ${MAX_WAIT} seconds${RESET}"
    echo "Check logs: /tmp/localmind_ollama.log"
    exit 1
fi

# List available models
echo ""
echo -e "${BLUE}📦 Available Models:${RESET}"
MODELS_JSON=$(curl -s --max-time 5 "${OLLAMA_URL}/api/tags" 2>/dev/null)
echo "$MODELS_JSON" | $PYTHON_EXE -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('models', []):
    name = m.get('name', 'unknown')
    size_gb = m.get('size', 0) / (1024**3)
    print(f'  • {name} ({size_gb:.1f} GB)')
if not data.get('models'):
    print('  (No models found yet - they may still be downloading)')
" 2>/dev/null || echo "  (Could not retrieve model list)"
echo ""

# ── Start Dashboard ──────────────────────────────────────────
echo -e "${CYAN}🌐 Starting Dashboard Server...${RESET}"
echo -e "${CYAN}   Dashboard will be at ${DASHBOARD_URL}${RESET}"
echo ""

# Set environment for dashboard
export LOCALMIND_ROOT="$USB_ROOT"
export LOCALMIND_DATA="$DATA_DIR"
export LOCALMIND_PORT="$DASHBOARD_PORT"
export OLLAMA_HOST="$OLLAMA_URL"

# Start dashboard in background
nohup "$PYTHON_EXE" "${DASHBOARD_DIR}/server.py" > /tmp/localmind_dashboard.log 2>&1 &
echo $! > /tmp/localmind_dashboard.pid
DASHBOARD_PID=$(cat /tmp/localmind_dashboard.pid)

# Wait for dashboard
echo -n "⏳ Starting dashboard"
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    sleep 1
    if curl -s --max-time 2 "${DASHBOARD_URL}/api/status" >/dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✓ Dashboard is running!${RESET}"
        break
    fi
    WAITED=$((WAITED + 1))
    if [ $((WAITED % 3)) -eq 0 ]; then
        echo -n "."
    fi
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo ""
    echo -e "${RED}❌ Dashboard failed to start${RESET}"
    echo "Check logs: /tmp/localmind_dashboard.log"
    # Continue anyway - dashboard might start slowly
fi

# ── Open Browser ─────────────────────────────────────────────
echo ""
echo -e "${CYAN}🌍 Opening browser...${RESET}"
sleep 1
open "$DASHBOARD_URL" 2>/dev/null || echo "Please open: ${DASHBOARD_URL}"

# ── Status Display ───────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}   ✅ LocalMind is running!${RESET}"
echo ""
echo -e "${GREEN}   📊 Dashboard:${RESET}  ${DASHBOARD_URL}"
echo -e "${GREEN}   🤖 Ollama API:${RESET} ${OLLAMA_URL}"
echo ""
echo -e "${YELLOW}   Press Ctrl+C to stop LocalMind${RESET}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${RESET}"
echo ""

# ── Graceful Shutdown Handler ────────────────────────────────
shutdown_localmind() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down LocalMind...${RESET}"
    
    # Stop dashboard
    if [ -f /tmp/localmind_dashboard.pid ]; then
        DASHBOARD_PID=$(cat /tmp/localmind_dashboard.pid)
        if kill -0 "$DASHBOARD_PID" 2>/dev/null; then
            echo "  Stopping dashboard..."
            kill "$DASHBOARD_PID" 2>/dev/null
            sleep 1
        fi
        rm -f /tmp/localmind_dashboard.pid
    fi
    
    # Stop Ollama
    if [ -f /tmp/localmind_ollama.pid ]; then
        OLLAMA_PID=$(cat /tmp/localmind_ollama.pid)
        if kill -0 "$OLLAMA_PID" 2>/dev/null; then
            echo "  Stopping Ollama..."
            kill "$OLLAMA_PID" 2>/dev/null
            sleep 2
        fi
        rm -f /tmp/localmind_ollama.pid
    fi
    
    # Kill any remaining processes
    pkill -f "ollama serve" 2>/dev/null
    pkill -f "${DASHBOARD_DIR}/server.py" 2>/dev/null
    
    echo -e "${GREEN}✓ LocalMind stopped. Goodbye!${RESET}"
    echo ""
    exit 0
}

trap shutdown_localmind SIGINT SIGTERM

# ── Keep Running ─────────────────────────────────────────────
while true; do
    sleep 1
done
