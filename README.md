# LocalMind — Offline AI on a USB Stick

> **Plug in. Launch. Think.** — Your personal AI assistant that works entirely offline.

LocalMind is a 128GB USB-C drive pre-loaded with 5 powerful open-source AI models. Plug it into any Windows or Mac, click the launcher, and start chatting — no internet required, no subscriptions, no data mining.

## 🚀 Quick Start

### Windows
1. Plug in the LocalMind USB drive
2. Open File Explorer → select the USB drive
3. Double-click `START.bat`
4. Wait 30 seconds for AI to load
5. Your browser opens automatically

### macOS
1. Plug in the LocalMind USB drive
2. Open Finder → select the USB drive
3. Double-click `LocalMind.app`
4. Wait 30 seconds for AI to load
5. Your browser opens automatically

## 💻 System Requirements

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| OS | Windows 10 / macOS 12 | Windows 11 / macOS 14 |
| RAM | 8 GB | 16 GB |
| CPU | Intel i3 / Apple M1 | Intel i5 / Apple M3 |
| USB | USB 3.0 | USB 3.2 Gen 2 |
| Storage | 128GB free on USB | 256GB for extra models |

**No GPU required** — everything runs on CPU.

## 🧠 Included AI Models

| Model | Size | Best For |
|-------|------|----------|
| **LLaMA 3.1 8B** | 4.7 GB | General chat, coding, creative writing |
| **Qwen 2.5 7B** | 4.4 GB | Coding, reasoning, multilingual tasks |
| **Phi-4 14B** | 8.5 GB | Complex reasoning, math, instructions |
| **Mistral 7B** | 4.1 GB | Fast general-purpose queries |
| **Gemma 3 4B** | 2.7 GB | Lightweight tasks, basic vision |

**Total: ~24 GB** — leaving ~100GB free for your data and additional models.

## 📁 Project Structure

```
LocalMind/
├── launcher/              # Cross-platform launcher
│   ├── launcher.py        # Main Python launcher
│   ├── update.py          # Model update system
│   ├── START.bat          # Windows entry point
│   └── start.sh           # macOS/Linux entry point
├── dashboard/             # Web UI
│   └── server.py          # Python HTTP server + Ollama proxy
├── models/                # Pre-installed AI models (GGUF)
├── ollama/                # Ollama engine binaries
├── data/                  # User data, chats, settings
├── website/               # Sales landing page
└── .localmind/
    └── manifest.json      # Product metadata
```

## 🛠️ For Developers

### Building from Source

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/localmind.git
cd localmind

# Build the USB image (downloads Ollama + all models)
./scripts/pre-install.sh

# Output: build/usb-image/
```

### Adding New Models

```bash
# Use the update system
cd launcher
python update.py --list          # Show available models
python update.py --download MODEL_NAME
```

## 🔒 Security & Privacy

- **Zero data exfiltration** — everything stays on the USB
- **No telemetry** — no usage tracking or analytics
- **No cloud dependency** — works fully offline
- **Open source** — audit the code yourself

## 📝 License

MIT License — use it, fork it, ship it.

---

**Questions?** support@localmind.ai

**© 2026 LocalMind**
