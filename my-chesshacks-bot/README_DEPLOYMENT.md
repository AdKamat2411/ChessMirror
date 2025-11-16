# Quick Deployment Guide

## The Problem

Your bot uses a **C++ executable** (`mcts_bridge`) that depends on **libtorch**. ChessHacks expects pure Python bots.

## What ChessHacks Expects

From their docs:
- Push to GitHub
- Include `/src`, `serve.py`, `requirements.txt`
- Platform runs it automatically

**But your bot needs:**
- C++ compilation
- libtorch libraries
- Pre-built executable

## Solutions

### 1. Contact ChessHacks Support First! ⚠️

**Ask them:**
- Do you support build scripts? (Can I include a `build.sh`?)
- Do you support Docker containers?
- Can you compile C++ during deployment?
- What's the deployment environment? (OS, architecture)

**This is the most important step** - they may have solutions we don't know about.

### 2. If They Support Build Scripts

Include `build.sh` in your repo. It will:
- Download libtorch
- Build the C++ executable
- Set up everything

### 3. If They Support Docker

Use the `Dockerfile` in the project root:
```bash
docker build -t chesshacks-bot -f Dockerfile .
docker push yourusername/chesshacks-bot
```

### 4. If Neither Works

**Consider rewriting in Python:**
- Use PyTorch directly (no C++ needed)
- Rewrite MCTS in Python (slower but works)
- Use existing Python MCTS libraries

## Files to Include in Git

**Must include:**
- `src/main.py`
- `serve.py`
- `requirements.txt`
- `MCTS/src/` (C++ source)
- `MCTS/include/` (C++ headers)
- `MCTS/Chess/` (Chess C++ code)
- `MCTS/Makefile` (build config)
- `build.sh` (if supported)

**Don't include:**
- `devtools/` (development only)
- `.venv/` (virtual env)
- `logs/` (log files)
- `*.o`, `*.dSYM` (build artifacts)
- `mcts_bridge` (will be built)

## Model File

Your model (`chessnet_new_ts.pt`) is large. Options:

1. **Git LFS** (if < 2GB):
   ```bash
   git lfs install
   git lfs track "*.pt"
   git add chessnet_new_ts.pt
   ```

2. **Download during build** (recommended):
   - Store on GitHub Releases, S3, etc.
   - Download in `build.sh` or Dockerfile
   - Update `MODEL_PATH` in `main.py`

3. **Include directly** (if < 100MB):
   - Just commit it
   - Update `.gitignore` to allow it

## Next Steps

1. ✅ **Read `DEPLOYMENT.md`** for detailed options
2. ✅ **Contact ChessHacks support** about C++ dependencies
3. ✅ **Test Docker build locally** (if applicable)
4. ✅ **Prepare build script** (if they support it)
5. ✅ **Have a Python fallback plan** (if C++ doesn't work)

## Testing Locally

Before deploying, test the Docker setup:

```bash
# From project root
docker build -t chesshacks-bot -f Dockerfile .
docker run -p 5058:5058 chesshacks-bot
```

Then test the API:
```bash
curl http://localhost:5058/api/bot -X POST \
  -H "Content-Type: application/json" \
  -d '{"pgn": "1. e4 e5"}'
```




