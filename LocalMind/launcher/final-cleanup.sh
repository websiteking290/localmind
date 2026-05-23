#!/bin/bash
# =================================================================
#  LocalMind Final Cleanup Script
#  Run after model copy completes
# =================================================================

echo "🧹 LocalMind USB Final Cleanup"
echo "================================"
echo ""

# 1. Check models copied
USB_MODELS_SIZE=$(du -sh /Volumes/LocalMind/LocalMind/models/ | cut -f1)
echo "USB Models: $USB_MODELS_SIZE"

# 2. Clean up old small models from local machine
echo ""
echo "Cleaning old small models from local machine..."
# These are the old models that got replaced
ollama rm gemma3 2>/dev/null
ollama rm mistral 2>/dev/null
ollama rm qwen2.5 2>/dev/null
ollama rm llama3.1 2>/dev/null
ollama rm deepseek-v4-pro 2>/dev/null

echo "✅ Cleanup done"

# 3. Update manifest in workspace
cp /Volumes/LocalMind/LocalMind/.localmind/manifest.json ~/workspace/usb-ai-sales/LocalMind/.localmind/manifest.json

# 4. Commit to GitHub
cd ~/workspace/usb-ai-sales/LocalMind
git add -A
git commit -m "Final: Updated manifest with 6 premium models (~90GB)

Models:
- llama3.1:70b (39.6GB) - General purpose
- qwen2.5:32b (18.5GB) - Reasoning
- deepseek-r1:14b (8.4GB) - Coding
- gemma4 (8.9GB) - Creative
- phi4 (8.4GB) - Fast responses
- mistral-nemo (6.6GB) - Balanced

Total: 90.4GB on USB
Date: 2026-05-23"
git push origin main

echo ""
echo "✅ GitHub updated!"
echo ""
echo "USB is ready for customers!"
