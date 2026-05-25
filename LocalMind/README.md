# LocalMind — Offline AI on a USB Stick

> **Plug in. Start. Chat.** — Your personal AI assistant that works entirely offline.

LocalMind is a USB drive pre-loaded with Ollama AI engine, 3 chat models, and a web dashboard. Plug it into any Windows or Mac, and it starts automatically — no internet required.

## 🚀 Quick Start

### macOS
1. Plug in the LocalMind USB drive
2. **Autorun opens LocalMind automatically** (or double-click `START-macOS.command` if needed)
3. Local Chat opens in your browser automatically
4. Pick a model from the sidebar and start chatting!

### Windows
1. Plug in the LocalMind USB drive
2. **Autorun starts LocalMind automatically** (or double-click `START-Windows.bat` if needed)
3. Local Chat opens in your browser automatically
4. Pick a model from the sidebar and start chatting!

## 🤖 AI Models (Pre-Loaded)

All models run entirely offline — no internet needed after first setup.

| Model | Size | RAM | Best For |
|-------|------|-----|----------|
| **gemma4:e4b** | 5.8 GB | ~5 GB | Google's latest. Fast, efficient. |
| **qwen2.5:7b** | 4.4 GB | ~6 GB | Strong coding & reasoning. |
| **mistral:7b** | 4.1 GB | ~5 GB | Fast, reliable all-purpose. |

**Works on 8GB RAM computers.** All 3 models fit on the USB (22GB total).

## 🖥️ Two Ways to Chat

### 1. Local Chat (Web Dashboard) — Default
- Opens automatically when you plug in
- Go to: `http://localhost:3000`
- Select a model from the sidebar
- Chat in the web interface

### 2. OpenClaw Chat (Terminal)
- Open a terminal on your computer
- Run: `openclaw chat`
- Works with Ollama models via OpenClaw
- Requires Node.js to be installed

## 💻 System Requirements

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| OS | Windows 10 / macOS 12 | Windows 11 / macOS 14 |
| RAM | 8 GB | 16 GB |
| CPU | Intel i3 / Apple M1 | Intel i5 / Apple M3 |
| USB | USB 3.0 | USB 3.2 Gen 2 |

## 🛠️ Troubleshooting

### "Python not found" on Windows
LocalMind will prompt you to download Python automatically. Requires internet for one-time setup.

### Dashboard doesn't open
1. Open a browser to `http://localhost:3000`
2. Or try `http://localhost:3001`

### Chat is slow
Models load into RAM. First message takes 10-30 seconds. Subsequent messages are fast. Use smaller models (gemma4 or mistral) for faster responses.

### Models not detected
If models aren't found, setup.py will ask if you want to download them. Your models are pre-loaded, so this shouldn't happen.

## 📁 USB Structure

```
LocalMind USB/
├── START-macOS.command    ← Launch (Mac)
├── START-Windows.bat      ← Launch (Windows)
├── LocalMind/
│   ├── setup.py           ← Main launcher
│   ├── ollama/ollama      ← AI engine
│   ├── models/            ← AI model files (22GB)
│   ├── dashboard/         ← Web dashboard
│   └── openclaw/          ← Terminal AI assistant
```

## 🔒 Privacy

Everything runs locally on YOUR computer. No data leaves the machine. No internet required after setup.

## 📋 What's Included

- **Ollama** — Local AI engine (runs models)
- **3 Pre-Loaded Models** — gemma4, qwen2.5, mistral (~22GB)
- **Web Dashboard** — Pure Python, no Node.js needed
- **OpenClaw** — Terminal AI assistant (requires Node.js)

## 🆘 Stopping LocalMind

Press `Ctrl+C` in the terminal window to stop LocalMind.