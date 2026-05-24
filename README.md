# LocalMind — Offline AI on a USB Stick

> **Plug in. Launch. Think.** — Your personal AI assistant that works entirely offline.

LocalMind is a USB drive pre-loaded with Ollama AI engine and a web dashboard. Plug it into any Windows or Mac, double-click the launcher, and start chatting — no internet required.

## 🚀 Quick Start

### Windows
1. Plug in the LocalMind USB drive
2. Open File Explorer → double-click `START-Windows.bat`
3. If Python is missing, it auto-installs (one-time)
4. If AI models are missing, it offers to download them
5. Choose: **Local Chat** (web browser) or **OpenClaw** (terminal)

### macOS
1. Plug in the LocalMind USB drive
2. Open Finder → double-click `START-macOS.command`
3. If Python is missing, install it: `brew install python3`
4. If AI models are missing, it offers to download them
5. Choose: **Local Chat** (web browser) or **OpenClaw** (terminal)

## 💻 System Requirements

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| OS | Windows 10 / macOS 12 | Windows 11 / macOS 14 |
| RAM | 8 GB | 16 GB |
| CPU | Intel i3 / Apple M1 | Intel i5 / Apple M3 |
| USB | USB 3.0 | USB 3.2 Gen 2 |
| Storage | 128GB free on USB | 256GB for extra models |

**No GPU required** — everything runs on CPU.

## 🧠 AI Models (Downloadable)

| Model | Size | Best For |
|-------|------|----------|
| **LLaMA 3.1 8B** | 4.7 GB | General chat, coding, creative writing |
| **Qwen 2.5 7B** | 4.5 GB | Coding, reasoning, multilingual tasks |
| **Phi-4 14B** | 8.4 GB | Complex reasoning, math, instructions |
| **Mistral 7B** | 4.1 GB | Fast general-purpose queries |
| **Gemma 3 4B** | 3.0 GB | Lightweight tasks, quick responses |

**Total: ~24 GB** — leaving ~100GB free for your data and additional models.

Models are **downloaded on first run** — the USB ships with the AI engine and dashboard, models auto-install when you launch.

## 📁 Project Structure

```
LocalMind/                    # Everything on the USB
├── setup.py                  # ← Main launcher (double-click or run)
├── dashboard/
│   └── server.py             # Web UI (runs on localhost:3000)
├── models/                   # AI models (auto-downloaded on first run)
├── ollama/
│   ├── ollama                # macOS binary
│   ├── windows/ollama.exe    # Windows binary
│   └── windows/vc_redist.x64.exe  # Visual C++ redist
├── data/                     # User chats, settings (stays on USB)
├── .localmind/
│   └── manifest.json         # Product metadata
├── launcher/                 # Platform-specific helpers
│   └── install-python.bat    # Windows Python auto-installer
└── openclaw/                 # OpenClaw AI assistant (optional)

Root of USB:
├── START-macOS.command       # macOS double-click launcher
├── START-Windows.bat         # Windows double-click launcher
└── autorun.inf              # Windows auto-run (if enabled)
```

## 🛠️ How `setup.py` Works

The unified launcher handles everything:

1. **Python check** — verifies Python 3.9+ is installed
2. **Model check** — lists installed models, offers downloads if empty
3. **Ollama start** — launches the bundled Ollama binary, auto-finds a free port
4. **Dashboard start** — launches the Python web server
5. **Browser open** — opens the dashboard automatically
6. **Choice menu** — pick Local Chat (web) or OpenClaw (terminal)
7. **Graceful shutdown** — Ctrl+C kills everything cleanly

### Manual Model Download

```bash
cd LocalMind
python3 setup.py
# Choose "Y" when asked to download models
```

Or use Ollama directly:

```bash
./ollama/ollama pull llama3.1:8b
./ollama/ollama pull phi4
```

## 🔒 Security & Privacy

- **Zero data exfiltration** — everything stays on the USB
- **No telemetry** — no usage tracking or analytics
- **No cloud dependency** — works fully offline after model download
- **Open source** — audit the code yourself

## 📝 License

MIT License — use it, fork it, ship it.

---

**Questions?** support@localmind.ai

**© 2026 LocalMind**
