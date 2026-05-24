#!/bin/bash
# =================================================================
#  LocalMind AI — macOS Plug-and-Play Launcher
#  Double-click this file on your Mac to start LocalMind.
# =================================================================

# ANSI colors (safe fallback)
C='\033[36m'; G='\033[32m'; Y='\033[33m'; R='\033[31m'; X='\033[0m'

# Get USB root directory (where THIS script lives)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SETUP_PY="${SCRIPT_DIR}/LocalMind/setup.py"

echo ""
echo -e "${C}    ╔═══════════════════════════════════════════════════════════╗${X}"
echo -e "${C}    ║              🤖  LOCALMIND AI - macOS LAUNCHER           ║${X}"
echo -e "${C}    ╚═══════════════════════════════════════════════════════════╝${X}"
echo ""

# ── Find Python ───────────────────────────────────────────
PYTHON=""

# Try bundled Python first (if we ever bundle it)
if [ -f "${SCRIPT_DIR}/LocalMind/launcher/python/bin/python3" ]; then
    PYTHON="${SCRIPT_DIR}/LocalMind/launcher/python/bin/python3"
# Then system Python
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    # Check version is 3.9+
    VER=$(python --version 2>&1 | awk '{print $2}')
    MAJOR=$(echo "$VER" | cut -d. -f1)
    MINOR=$(echo "$VER" | cut -d. -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 9 ]; then
        PYTHON="python"
    fi
fi

if [ -z "$PYTHON" ]; then
    echo -e "${R}⚠ Python 3.9+ is required.${X}"
    echo ""
    echo "   Install it with one of these methods:"
    echo ""
    echo "   1) Homebrew:     brew install python3"
    echo "   2) Official:     https://www.python.org/downloads/macos/"
    echo ""
    echo -e "${Y}   After installing, double-click this file again.${X}"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

echo -e "${G}✓ Python ready:${X} $($PYTHON --version)"
echo ""

# ── Run Setup ───────────────────────────────────────────
echo -e "${C}🚀 Starting LocalMind setup...${X}"
echo ""

if [ ! -f "$SETUP_PY" ]; then
    echo -e "${R}❌ Setup file not found:${X} $SETUP_PY"
    read -p "Press Enter to close..."
    exit 1
fi

cd "${SCRIPT_DIR}/LocalMind"
exec "$PYTHON" "$SETUP_PY"
