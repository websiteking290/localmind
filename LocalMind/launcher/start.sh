#!/bin/bash
# =================================================================
#  LocalMind AI — macOS Launcher
#  Starts the LocalMind AI system from USB drive
# =================================================================

CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; RESET='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LAUNCHER_DIR="$USB_ROOT/launcher"
LAUNCHER_PY="$LAUNCHER_DIR/launcher.py"

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
echo -e "${CYAN}══════════════════════════════════════════════════${RESET}"
echo "  LocalMind AI — Your AI, Offline"
echo -e "${CYAN}══════════════════════════════════════════════════${RESET}"
echo ""

# Check Python
PYTHON_EXE=""
if [ -f "$LAUNCHER_DIR/python/bin/python3" ]; then
    PYTHON_EXE="$LAUNCHER_DIR/python/bin/python3"
elif command -v python3 &> /dev/null; then
    PYTHON_EXE="python3"
elif command -v python &> /dev/null; then
    PYTHON_EXE="python"
fi

if [ -z "$PYTHON_EXE" ]; then
    echo -e "${RED}[ERROR] Python not found.${RESET}"
    echo -e "${RED}        LocalMind requires Python 3.9+${RESET}"
    echo -e "${RED}        Install: brew install python3${RESET}"
    exit 1
fi

# Check launcher
if [ ! -f "$LAUNCHER_PY" ]; then
    echo -e "${RED}[ERROR] Launcher not found: $LAUNCHER_PY${RESET}"
    exit 1
fi

# Run launcher
echo -e "${GREEN}[✓] Starting LocalMind...${RESET}"
echo ""

exec "$PYTHON_EXE" "$LAUNCHER_PY"
