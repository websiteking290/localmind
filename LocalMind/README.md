# LocalMind USB AI Product — Final Setup Guide

## Product Overview
**LocalMind** is a 128GB USB drive containing 6 premium offline AI models.
Customer plugs it in, double-clicks the launcher, and starts chatting immediately — no setup, no internet required.

---

## 📦 What's on the USB

```
LocalMind/
├── START-macOS.command      ← macOS launcher (double-click)
├── START-Windows.bat        ← Windows launcher (double-click)  
├── .localmind/
│   └── manifest.json          ← Model list & metadata
├── launcher/
│   ├── setup-openclaw.py      ← OpenClaw auto-installer
│   ├── install-python.bat     ← Windows Python installer
│   ├── launcher.py            ← Python launcher (legacy)
│   ├── start.sh               ← macOS startup script
│   └── final-cleanup.sh       ← Post-transfer cleanup
├── dashboard/
│   └── server.py              ← Web dashboard (port 3000)
├── models/
│   ├── blobs/                 ← Model weights (~90GB)
│   └── manifests/             ← Model metadata
├── ollama/
│   ├── ollama                 ← macOS binary (v0.24.0)
│   └── windows/
│       ├── ollama.exe         ← Windows binary
│       ├── lib/               ← Required libraries
│       └── vc_redist.x64.exe  ← Visual C++ redistributable
├── data/                      ← User data, chats, config
└── openclaw/                  ← Full OpenClaw AI assistant
```

---

## 🤖 Models Included (90.4GB)

| Model | Size | Purpose |
|-------|------|---------|
| **llama3.1:70b** | 39.6GB | General purpose, reasoning, writing |
| **qwen2.5:32b** | 18.5GB | Math, logic, coding specialist |
| **deepseek-r1:14b** | 8.4GB | Programming tasks |
| **gemma4** | 8.9GB | Creative writing, analysis |
| **phi4** | 8.4GB | Fast responses, general tasks |
| **mistral-nemo** | 6.6GB | Balanced speed & quality |

---

## 🚀 Quick Start (Customer)

### macOS
1. Plug in USB
2. Double-click `START-macOS.command`
3. Choose chat interface:
   - **Option 1:** Web dashboard (browser)
   - **Option 2:** OpenClaw terminal chat
   - **Option 3:** Just the dashboard
4. Start chatting!

### Windows
1. Plug in USB
2. Double-click `START-Windows.bat`
3. If Python not installed → auto-installs
4. Choose chat interface
5. Start chatting!

---

## ⚠️ Important: System Ollama Conflict

**Problem:** If customer already has Ollama installed, it auto-starts on port 11434 and saves models to their computer instead of USB.

**Solution:** Launchers now:
1. Detect system Ollama on port 11434
2. Stop it gracefully (or force-kill)
3. Also stops Windows service / macOS launchd
4. Verify port is free
5. Start USB Ollama with USB model path
6. Use ONLY USB binary for all commands

**This ensures models download to USB, never customer's machine.**

---

## 🔧 For Developers (Model Setup)

Models must be downloaded directly to USB using the USB Ollama binary:

```bash
# macOS
export OLLAMA_MODELS=/Volumes/LocalMind/LocalMind/models
/Volumes/LocalMind/LocalMind/ollama/ollama pull llama3.1:70b

# Windows
set OLLAMA_MODELS=E:\LocalMind\models
E:\LocalMind\ollama\windows\ollama.exe pull llama3.1:70b
```

**NEVER use system `ollama` command — it ignores OLLAMA_MODELS.**

---

## 📊 GitHub Repository

**Repo:** https://github.com/websiteking290/localmind

**Commits (May 23, 2026):**
- `121a2b4` — Bundled Ollama v0.24.0
- `bc02f16` — Dashboard fix + launchers
- `a4c7811` — Conversation log
- `32ec56b` — OpenClaw integration
- `2c91e47` — Final manifest
- `16ab4e3` — macOS system Ollama fix
- `bfc6e8d` — Windows system Ollama fix

---

## ✅ Testing Checklist (Use Clean Computer)

- [ ] USB mounts correctly
- [ ] Double-click launcher works
- [ ] If no Python → auto-installs
- [ ] If system Ollama → stops it
- [ ] USB Ollama starts on port 11434
- [ ] Dashboard loads on port 3000
- [ ] `/api/models` shows all 6 models
- [ ] Chat works with at least 1 model
- [ ] OpenClaw option installs & works (optional)
- [ ] Shutdown cleans up processes

---

## 📝 Notes

- **macOS:** Python usually pre-installed. If not, Homebrew installs it.
- **Windows:** Python 3.11.9 auto-downloaded (27MB) if missing.
- **Models:** Downloaded directly to USB, never touch customer's disk.
- **Offline:** After initial download, works without internet.
- **Space:** 90.4GB models + 5GB system files = ~96GB used, 32GB free.

---

*LocalMind v1.1 — May 23, 2026*
