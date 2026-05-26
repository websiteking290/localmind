#!/usr/bin/env python3
"""
LocalMind Dashboard Server
==========================
Lightweight web server for the LocalMind AI dashboard.
Serves static files and proxies chat requests to Ollama.

No Node.js required — pure Python with built-in http.server.
"""

import sys
import os
import json
import time
import socket
import subprocess
import threading
import urllib.request
import urllib.error
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs

# ── Configuration ───────────────────────────────────────
USB_ROOT = Path(os.environ.get("LOCALMIND_ROOT", ".")).resolve()
DATA_DIR = Path(os.environ.get("LOCALMIND_DATA", str(USB_ROOT / "data"))).resolve()
PORT = int(os.environ.get("LOCALMIND_PORT", "3000"))

OLLAMA_HOST = os.environ.get("LOCALMIND_OLLAMA_HOST", "127.0.0.1")
OLLAMA_PORT = int(os.environ.get("LOCALMIND_OLLAMA_PORT", "11434"))
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
_CHAT_LOCK = threading.Lock()  # Serialize concurrent chat requests — Ollama handles one at a time
_SPEED_CACHE_FILE = DATA_DIR / "speed_model.json"

MANIFEST_FILE = USB_ROOT / ".localmind" / "manifest.json"
CONFIG_FILE = DATA_DIR / "localmind.json"
CHATS_DIR = DATA_DIR / "chats"

# ── RAM Tier Detection ─────────────────────────────────
# Passed in from setup.py if available, otherwise auto-detect
def _get_ram_tier():
    # Check env first (setup.py passes this)
    env_tier = os.environ.get("LOCALMIND_RAM_TIER", "").strip().lower()
    if env_tier in ("8gb", "16gb"):
        return env_tier
    # Auto-detect system RAM
    try:
        if sys.platform == "darwin" or sys.platform.startswith("linux"):
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=5
            )
            gb = int(result.stdout.strip()) / (1024**3)
        elif sys.platform == "win32":
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"],
                capture_output=True, text=True, timeout=5
            )
            gb = int(result.stdout.strip().replace(",", "")) / (1024**3)
        else:
            return "8gb"
        return "16gb" if gb >= 15.5 else "8gb"
    except Exception:
        return "8gb"

RAM_TIER = _get_ram_tier()

# Model tier definitions
TIER_MODELS = {
    "8gb":  ["gemma4:e4b", "qwen2.5:7b", "qwen2.5-coder:7b"],
    "16gb": ["qwen3:8b", "qwen2.5-coder:14b", "gemma3:12b"],
}

# Fastest model per tier
TIER_FASTEST = {
    "8gb":  "qwen2.5:7b",
    "16gb": "qwen3:8b",
}

# ── Ensure directories ──────────────────────────────────
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHATS_DIR.mkdir(parents=True, exist_ok=True)

# ── Static HTML ─────────────────────────────────────────
DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LocalMind — Your AI, Offline</title>
<style>
:root{--bg:#0f172a;--surface:#1e293b;--surface2:#334155;--text:#f1f5f9;--text2:#94a3b8;--accent:#3b82f6;--accent2:#60a5fa;--success:#22c55e;--warning:#f59e0b;--danger:#ef4444;--border:#334155;}
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;}
body{background:var(--bg);color:var(--text);height:100vh;display:flex;overflow:hidden;}

/* Sidebar */
.sidebar{width:260px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;}
.brand{padding:20px;border-bottom:1px solid var(--border);}
.brand h1{font-size:20px;font-weight:700;color:var(--accent);}
.brand p{font-size:12px;color:var(--text2);margin-top:4px;}

.models{padding:16px;flex:1;overflow-y:auto;}
.models h3{font-size:11px;text-transform:uppercase;color:var(--text2);letter-spacing:1px;margin-bottom:12px;}
.model-card{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:8px;cursor:pointer;transition:all .2s;}
.model-card:hover{border-color:var(--accent);}
.model-card.active{border-color:var(--accent);background:rgba(59,130,246,.1);}
.model-card .name{font-size:13px;font-weight:600;}
.model-card .size{font-size:11px;color:var(--text2);margin-top:2px;}
.model-card .desc{font-size:11px;color:var(--text2);margin-top:4px;line-height:1.4;}

.sidebar-footer{padding:16px;border-top:1px solid var(--border);}
.status{display:flex;align-items:center;gap:8px;font-size:12px;}
.status-dot{width:8px;height:8px;border-radius:50%;background:var(--success);animation:pulse 2s infinite;}
@keyframes spin{to{transform:rotate(360deg)}}
.quick-btn{transition:all .2s}
.quick-btn.active{background:var(--accent)!important;color:#fff!important;border-color:var(--accent)!important}
.quick-badge{background:var(--accent);color:#fff;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:700;margin-left:6px;vertical-align:middle;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}

/* Main */
.main{flex:1;display:flex;flex-direction:column;}
.header{height:56px;background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:0 20px;}
.header h2{font-size:16px;font-weight:600;}
.header .model-badge{background:var(--accent2);color:var(--bg);padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;}

.chat-area{flex:1;display:flex;flex-direction:column;padding:20px;overflow:hidden;}
.messages{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:12px;padding-bottom:20px;}
.message{max-width:80%;padding:12px 16px;border-radius:12px;font-size:14px;line-height:1.6;}
.message.user{align-self:flex-end;background:var(--accent);color:#fff;}
.message.assistant{align-self:flex-start;background:var(--surface2);border:1px solid var(--border);}
.message .role{font-size:10px;text-transform:uppercase;letter-spacing:1px;opacity:.7;margin-bottom:4px;}

.input-area{display:flex;gap:12px;padding-top:16px;border-top:1px solid var(--border);}
.input-area input{flex:1;background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px 16px;color:var(--text);font-size:14px;outline:none;}
.input-area input:focus{border-color:var(--accent);}
.input-area input:disabled{opacity:.5;}
.input-area button{background:var(--accent);color:#fff;border:none;border-radius:8px;padding:12px 24px;font-size:14px;font-weight:600;cursor:pointer;transition:opacity .2s;}
.input-area button:hover{opacity:.9;}
.input-area button:disabled{opacity:.5;cursor:not-allowed;}

/* System panel */
.system-panel{position:fixed;top:56px;right:0;width:300px;height:calc(100vh - 56px);background:var(--surface);border-left:1px solid var(--border);padding:20px;transform:translateX(100%);transition:transform .3s;z-index:100;}
.system-panel.open{transform:translateX(0);}
.system-panel h3{font-size:14px;margin-bottom:16px;}
.info-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px;}
.info-row span:first-child{color:var(--text2);}

/* Loading */
.typing{display:flex;gap:4px;padding:12px 16px;}
.typing span{width:8px;height:8px;background:var(--accent);border-radius:50%;animation:typing 1.4s infinite ease-in-out;}
.typing span:nth-child(2){animation-delay:.2s;}
.typing span:nth-child(3){animation-delay:.4s;}
@keyframes typing{0%,80%,100%{transform:scale(0);}40%{transform:scale(1);}}

/* Scrollbar */
::-webkit-scrollbar{width:6px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:var(--surface2);border-radius:3px;}

/* Mobile */
@media(max-width:768px){.sidebar{width:200px;}.system-panel{width:100%;}}
</style>
</head>
<body>
<div class="sidebar">
  <div class="brand">
    <h1>LocalMind</h1>
    <p id="tier-label">Your AI, Offline</p>
  </div>
  <div class="models" id="models">
    <h3>AI Models</h3>
    <div id="model-list"></div>
  </div>
  <div class="sidebar-footer">
    <div class="status">
      <div class="status-dot"></div>
      <span id="status-text">AI Ready</span>
    </div>
    <div id="quick-info" style="display:none;margin-top:8px;font-size:11px;color:var(--text2);line-height:1.4;"></div>
    <button id="quick-btn" onclick="toggleQuickMode()" style="margin-top:10px;width:100%;background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:8px;border-radius:8px;cursor:pointer;font-size:12px;font-weight:600;">
      ⚡ Quick Mode: AUTO
    </button>
  </div>
</div>

<div class="main">
  <div class="header">
    <h2>Chat</h2>
    <div style="display:flex;gap:12px;align-items:center;">
      <span class="model-badge" id="current-model">Select Model</span>
      <button onclick="toggleSystem()" style="background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:6px 12px;border-radius:6px;cursor:pointer;font-size:12px;">System</button>
    </div>
  </div>

  <div class="chat-area">
    <div class="messages" id="messages"></div>
    <div class="input-area">
      <input type="text" id="user-input" placeholder="Ask anything..." onkeydown="if(event.key==='Enter')sendMessage()" disabled>
      <button id="send-btn" onclick="sendMessage()" disabled>Send</button>
    </div>
  </div>
</div>

<div class="system-panel" id="system-panel">
  <h3>System Info</h3>
  <div id="system-info"></div>
</div>

<script>
let selectedModel = null;
let messages = [];
let quickMode = false;
let detectedFastest = null;
let initialModelSet = false;  // Don't re-auto-select on refresh

function toggleQuickMode() {
  quickMode = !quickMode;
  const btn = document.getElementById("quick-btn");
  if (!btn) return;
  if (quickMode) {
    btn.classList.add("active");
    btn.textContent = "⚡ Quick Mode: ON";
    if (detectedFastest && selectedModel !== detectedFastest) {
      document.querySelectorAll(".model-card").forEach(c => c.classList.remove("active"));
      const cards = document.querySelectorAll(".model-card");
      cards.forEach(c => {
        if (c.querySelector(".name")?.textContent.includes(detectedFastest)) {
          c.classList.add("active");
          selectedModel = detectedFastest;
          document.getElementById("current-model").textContent = detectedFastest;
        }
      });
    }
  } else {
    btn.classList.remove("active");
    btn.textContent = "⚡ Quick Mode: AUTO";
  }
}

// Load models on page load
async function loadModels() {
  try {
    const res = await fetch('/api/models');
    const data = await res.json();
    const list = document.getElementById('model-list');
    list.innerHTML = '';
    
    // Show tier badge in sidebar
    if (data.ram_tier === '16gb') {
      const tl = document.getElementById('tier-label');
      if (tl) tl.innerHTML = '<span style="color:var(--warning);">⚡ 16GB MODE</span>';
    } else {
      const tl = document.getElementById('tier-label');
      if (tl) tl.textContent = 'Your AI, Offline — 8GB';
    }
    
    const fastest = data.fastest_model || null;
    let defaultModel = data.models[0] ? data.models[0].name : null;
    
    data.models.forEach(m => {
      const isFastest = m.name === fastest;
      const card = document.createElement('div');
      card.className = 'model-card' + (isFastest ? ' active' : '');
      const badge = isFastest ? '<span style="color:var(--accent);font-size:10px;"> ⚡ FASTEST</span>' : '';
      card.innerHTML = '<div class="name">' + m.name + badge + '</div><div class="size">' + (m.size || '') + '</div><div class="desc">' + (m.description || '') + '</div>';
      (function(name, cardEl){ card.onclick = function(){
        initialModelSet = true;
        selectModel(name, cardEl);
      }; })(m.name, card);
      list.appendChild(card);
    });
    
    // Auto-select fastest for this tier once
    if (fastest && !initialModelSet) {
      defaultModel = fastest;
      const info = document.getElementById('quick-info');
      if (info) {
        info.innerHTML = '\u26a1 <b>' + fastest + '</b> selected — ' + (data.ram_tier === '16gb' ? '16GB tier' : '8GB tier');
        info.style.display = 'block';
      }
    }
    
    selectModel(defaultModel, list.querySelector('.active') || list.firstChild);
  } catch (e) {
    console.error('Failed to load models:', e);
  }
}

function selectModel(name, card) {
  selectedModel = name;
  document.querySelectorAll('.model-card').forEach(c => c.classList.remove('active'));
  if (card) card.classList.add('active');
  document.getElementById('current-model').textContent = name;
  document.getElementById('user-input').disabled = false;
  document.getElementById('send-btn').disabled = false;
  // Only mark as user-initiated when card was actually clicked
  if (card !== null) initialModelSet = true;
}

async function sendMessage() {
  const input = document.getElementById('user-input');
  const btn = document.getElementById('send-btn');
  const text = input.value.trim();
  if (!text || !selectedModel) return;
  
  input.disabled = true;
  btn.disabled = true;
  input.value = '';
  
  // Add user message
  addMessage('user', text);
  messages.push({role:'user',content:text});
  
  // Show typing
  const typing = showTyping();
  
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({model:selectedModel,messages:messages})
    });
    
    typing.remove();
    
    if (!res.ok) throw new Error('Chat failed');
    
    const data = await res.json();
    const reply = data.message?.content || data.response || 'No response';
    addMessage('assistant', reply);
    messages.push({role:'assistant',content:reply});
  } catch (e) {
    typing.remove();
    addMessage('assistant', 'Error: ' + e.message);
  }
  
  input.disabled = false;
  btn.disabled = false;
  input.focus();
}

function addMessage(role, content) {
  const container = document.getElementById('messages');
  const msg = document.createElement('div');
  msg.className = `message ${role}`;
  msg.innerHTML = `<div class="role">${role}</div><div>${escapeHtml(content)}</div>`;
  container.appendChild(msg);
  container.scrollTop = container.scrollHeight;
}

function showTyping() {
  const container = document.getElementById('messages');
  const typing = document.createElement('div');
  typing.className = 'message assistant typing';
  typing.innerHTML = '<span></span><span></span><span></span>';
  container.appendChild(typing);
  container.scrollTop = container.scrollHeight;
  return typing;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function toggleSystem() {
  document.getElementById('system-panel').classList.toggle('open');
  loadSystemInfo();
}

async function loadSystemInfo() {
  try {
    const res = await fetch('/api/system');
    const data = await res.json();
    const container = document.getElementById('system-info');
    container.innerHTML = `
      <div class="info-row"><span>Platform</span><span>${data.platform}</span></div>
      <div class="info-row"><span>Ollama</span><span>${data.ollama_version || 'Unknown'}</span></div>
      <div class="info-row"><span>Models</span><span>${data.model_count}</span></div>
      <div class="info-row"><span>USB Path</span><span>${data.usb_path}</span></div>
      <div class="info-row"><span>Port</span><span>${data.port}</span></div>
    `;
  } catch (e) {
    console.error(e);
  }
}

loadModels();
</script>
</body>
</html>'''

# ── Request Handler ───────────────────────────────────────
def _detect_fastest_model():
    """Return the fastest model for this computer.
    
    Strategy:
    - Check /api/ps for what's currently loaded in RAM
    - Known speed order: gemma4:e4b (slowest) < mistral:7b < qwen2.5:7b (fastest)
    - qwen2.5:7b is always preferred because even if it needs loading,
      it loads faster than mistral/gemma and is fastest once loaded
    - Cache result for 24h
    """
    cache_file = _SPEED_CACHE_FILE

    # Satisfied? Cache valid 24h
    if cache_file.exists():
        try:
            with open(cache_file) as f:
                cached = json.load(f)
            if cached.get("timestamp"):
                age = time.time() - cached["timestamp"]
                if age < 86400:
                    return cached.get("model")
        except Exception:
            pass

    # Default to qwen2.5:7b (best-in-class speed, most capable for CPU-only)
    # Unless a clearly faster model is already loaded and we've measured it before
    preferred = ["qwen2.5:7b", "mistral:7b", "gemma4:e4b"]

    in_ram = []
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/ps", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            in_ram = [m.get("name") for m in data.get("models", [])]
    except Exception:
        pass

    # If qwen is in RAM, use it (it's the fastest)
    # If qwen NOT in RAM but mistral IS, return qwen (still faster to load/switch to)
    # Only fall back to loaded non-qwen model if nothing else is available
    if "qwen2.5:7b" in in_ram:
        result = "qwen2.5:7b"
    else:
        result = "qwen2.5:7b"  # Always prefer qwen — faster to load than other models

    # Cache
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump({"model": result, "timestamp": time.time()}, f)
    except Exception:
        pass

    return result

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silent logging
    
    def _set_no_cache(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self._set_no_cache()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self._set_no_cache()
        self.end_headers()
        self.wfile.write(html.encode())
    
    def _proxy_to_ollama(self, path, method="GET", body=None, headers=None, timeout=120):
        """Forward request to Ollama server."""
        url = f"{OLLAMA_URL}{path}"
        req = urllib.request.Request(url, method=method)
        
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        
        if body:
            req.data = body.encode() if isinstance(body, str) else body
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8')
            sys.stderr.write(f"[Ollama proxy] HTTPError {e.code} for {url}: {body[:200]}\n")
            return e.code, body
        except Exception as e:
            sys.stderr.write(f"[Ollama proxy] Error {type(e).__name__}: {e} for {url}\n")
            return 502, json.dumps({"error": str(e)})
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/" or path == "/index.html":
            self._send_html(DASHBOARD_HTML)
        
        elif path == "/api/models":
            # List models from Ollama filtered to the current RAM tier
            # Also include tier info so the JS can show appropriate badges
            tier_models = TIER_MODELS.get(RAM_TIER, TIER_MODELS["8gb"])
            fastest = TIER_FASTEST.get(RAM_TIER, TIER_FASTEST["8gb"])
            
            try:
                status, body = self._proxy_to_ollama("/api/tags", timeout=5)
                if status == 200:
                    data = json.loads(body)
                    # Filter to only models in this RAM tier
                    filtered = [m for m in data.get("models", []) if m.get("name") in tier_models]
                    data["models"] = filtered
                    data["ram_tier"] = RAM_TIER
                    data["fastest_model"] = fastest
                    for m in filtered:
                        if m.get("name") == fastest:
                            m["is_fastest"] = True
                    self._send_json(data)
                    return
            except Exception as e:
                pass
            
            # Fallback: build from manifest filtered to tier
            try:
                if MANIFEST_FILE.exists():
                    with open(MANIFEST_FILE) as f:
                        manifest = json.load(f)
                    models = []
                    for m in manifest.get("models", []):
                        if m.get("name") in tier_models:
                            models.append({
                                "name": m.get("name", "") + ":latest",
                                "model": m.get("name", "") + ":latest",
                                "size": int(m.get("size_gb", 0) * 1024 * 1024 * 1024),
                                "description": m.get("description", ""),
                                "size_gb": m.get("size_gb", ""),
                                "parameters": m.get("parameters", ""),
                            })
                    self._send_json({"models": models, "ram_tier": RAM_TIER, "fastest_model": fastest})
                    return
            except Exception:
                pass
            
            self._send_json({"models": [], "ram_tier": RAM_TIER, "fastest_model": fastest})
        
        elif path == "/api/system":
            # System info
            manifest = {}
            if MANIFEST_FILE.exists():
                with open(MANIFEST_FILE) as f:
                    manifest = json.load(f)
            
            self._send_json({
                "platform": sys.platform,
                "ollama_version": manifest.get("ollama_version", "Unknown"),
                "model_count": len(manifest.get("models", [])),
                "usb_path": str(USB_ROOT),
                "port": PORT,
                "version": "2.0",
                "ram_tier": RAM_TIER,
            })
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()
        
        if path == "/api/chat":
            # Check for speed mode hint
            parsed = urlparse(self.path)
            query_params = parse_qs(parsed.query)
            is_speed_mode = query_params.get("mode", [None])[0] == "speed"

            # Forward chat request to Ollama
            try:
                data = json.loads(body)
                model = data.get("model")
                messages = data.get("messages", [])
                
                # Build Ollama request
                # In speed mode, probe first response time and auto-select fastest model if needed
                ollama_body = json.dumps({
                    "model": model,
                    "messages": messages,
                    "stream": False,
                })
                
                # Serialize chat requests — Ollama processes models sequentially, not in parallel.
                # Without this lock, concurrent requests queue up inside Ollama's single-threaded
                # serve process, causing 502 errors and stalled responses.
                with _CHAT_LOCK:
                    status, resp_body = self._proxy_to_ollama(
                        "/api/chat",
                        method="POST",
                        body=ollama_body,
                        headers={"Content-Type": "application/json"},
                        timeout=120,
                    )
                
                if status == 200:
                    resp_data = json.loads(resp_body)
                    self._send_json({
                        "message": resp_data.get("message", {}),
                        "done": resp_data.get("done", True),
                    })
                else:
                    self._send_json({"error": f"Ollama error: {status}"}, status)
                
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

# ── Server Startup ──────────────────────────────────────
def find_free_port(start=3000):
    """Find an available port."""
    for port in range(start, start + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except:
            continue
    return start

# ── Threaded server so concurrent slow Ollama requests don't block each other ──
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def main():
    import sys

    # Find available port
    port = find_free_port(PORT)

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    
    print(f"\n  LocalMind Dashboard running at http://localhost:{port}")
    print(f"  USB Root: {USB_ROOT}")
    print(f"  Press Ctrl+C to stop\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        server.shutdown()

if __name__ == "__main__":
    main()
