# Deployment Guide

This bot uses a C++ MCTS engine with neural network evaluation. This guide explains how to deploy it to ChessHacks.

## ⚠️ Important: ChessHacks Platform

**ChessHacks handles deployment automatically** but your bot has **C++ dependencies** (libtorch) which requires special handling.

**The platform expects:**
- Python code in `/src`
- `serve.py` backend
- `requirements.txt` for Python dependencies
- Build scripts (if supported) for C++ compilation

## Deployment Options

### Option 1: Build Script (Recommended)

If ChessHacks supports build scripts, use the provided `build.sh`:

1. **Include `build.sh` in your repo** (in `my-chesshacks-bot/`)
2. **The platform should run it** before starting your bot
3. **The script will:**
   - Download libtorch (if needed)
   - Build the C++ executable (`MCTS/mcts_bridge`)
   - Install Python dependencies

**To test locally:**
```bash
cd my-chesshacks-bot
./build.sh
python serve.py
```

**Note:** This only works if ChessHacks supports build scripts. Check their documentation or contact support.

### Option 2: Pre-built Binary (If Platform is Linux)

If the deployment platform is Linux and matches your build environment:

1. **Build locally for Linux:**
   ```bash
   cd MCTS
   LIBTORCH_PATH=/path/to/libtorch make Bridge
   ```

2. **Include the binary in your repo:**
   - Add `MCTS/mcts_bridge` to git (remove from .gitignore)
   - Include libtorch libraries or use static linking

3. **Update .gitignore** to allow the binary:
   ```
   # Allow mcts_bridge for deployment
   !MCTS/mcts_bridge
   ```

### Option 3: Contact ChessHacks Support

Ask ChessHacks support if they can:
- Run build scripts during deployment
- Compile C++ code automatically
- Provide libtorch in their environment

## Important Files for Deployment

### Must Include:
- `src/main.py` - Your bot's brain
- `serve.py` - Backend server
- `requirements.txt` - Python dependencies
- `build.sh` - Build script (if supported)
- `MCTS/src/` - C++ source code
- `MCTS/include/` - C++ headers
- `MCTS/Chess/` - Chess-specific C++ code
- `MCTS/Makefile` - Build configuration
- Model file (`sobe_model.pt`) - Neural network weights

### Should Exclude:
- `devtools/` - Development tools (not needed in production)
- `.venv/` - Virtual environment
- `logs/` - Log files
- `*.o`, `*.dSYM` - Build artifacts (will be rebuilt)
- `MCTS/mcts_bridge` - Will be built during deployment (unless using pre-built binary)

## Model File Handling

The model file (`sobe_model.pt`) is large (~223MB). Options:

1. **Use Git LFS** (recommended for large files):
   ```bash
   git lfs install
   git lfs track "sobe_model.pt"
   git add .gitattributes
   git add sobe_model.pt
   ```

2. **Download during deployment** (if build script supported):
   - Store on external storage (GitHub Releases, S3, etc.)
   - Download in `build.sh`
   - Update `MODEL_PATH` in `main.py` accordingly

3. **Include in repo** (if < 100MB, not recommended):
   - Add to git
   - Update .gitignore to allow it

## LibTorch Dependencies

The C++ executable requires libtorch at runtime. Options:

1. **Download in build script** (recommended):
   - `build.sh` downloads libtorch automatically
   - Sets `LIBTORCH_PATH` and `LD_LIBRARY_PATH`

2. **Static linking** (if possible):
   - Modify Makefile to use static libs
   - Single binary, no external dependencies

3. **Use system libtorch** (if available on platform):
   - Install via package manager
   - Link against system libraries

## Testing Deployment Locally

Before deploying, test the build setup:

```bash
# Build
cd my-chesshacks-bot
./build.sh

# Run
python serve.py

# Test
curl http://localhost:5058/api/bot -X POST -H "Content-Type: application/json" \
  -d '{"pgn": "1. e4 e5"}'
```

## ChessHacks Platform Notes

Based on the documentation:
- **Push to GitHub** - Include `/src`, `serve.py`, `requirements.txt`
- **Platform builds/runs** - They handle the Python environment
- **Build scripts** - Check if they support `build.sh` or similar

**⚠️ Problem:** Your bot needs C++ compilation and libtorch, which the standard deployment doesn't cover.

**Solutions:**
1. **Contact ChessHacks support** - Ask if they support:
   - Build scripts (`build.sh`)
   - C++ compilation during deployment
   - Custom build commands
   
2. **Check their documentation** - Look for:
   - Build step configuration
   - Custom build commands
   - C++ support

3. **Use pre-built binary** - If platform is Linux:
   - Build `mcts_bridge` locally
   - Include in repo
   - Ensure libtorch libraries are available

## Alternative: Pure Python Solution

If C++ deployment is problematic, consider:
- Rewriting MCTS in Python (slower but easier to deploy)
- Using PyTorch directly in Python (no C++ needed)
- Using a Python MCTS library

## Next Steps

1. ✅ **Check ChessHacks documentation** for C++ build support
2. ✅ **Test build script** locally (`./build.sh`)
3. ✅ **Contact support** if you need help with C++ dependencies
4. ✅ **Set up Git LFS** for model file
5. ✅ **Push to GitHub** and connect in ChessHacks dashboard
