# ChessHacks Deployment Guide

## ✅ ChessHacks Supports C++!

ChessHacks supports C++ bots. They will automatically:
- Detect your build script or compile C++ during deployment
- Build the MCTS bridge executable
- Run your bot

## 📋 Deployment Checklist

### 1. Model File Handling

Your model (`sobe_model.pt`) needs to be accessible. Options:

**Option A: Use Git LFS (Recommended)**
```bash
# Install Git LFS if not already installed
git lfs install

# Track the model file
git lfs track "sobe_model.pt"
git add .gitattributes
git add sobe_model.pt
```

**Option B: Host on GitHub Releases or External Storage**
- Upload model to GitHub Releases, S3, or similar
- Download during build using `build.sh`

**Option C: Include in Repo (if < 100MB)**
- Add directly to git (not recommended for large files)

### 2. Files to Commit

**Must include:**
- ✅ `my-chesshacks-bot/src/` (your bot code)
- ✅ `my-chesshacks-bot/serve.py`
- ✅ `my-chesshacks-bot/requirements.txt`
- ✅ `my-chesshacks-bot/build.sh` (build script for C++ compilation)
- ✅ `MCTS/` (C++ source code - all of it)
- ✅ `MCTS/Makefile` (build configuration)
- ✅ `sobe_model.pt` (via Git LFS or download)

**Don't include:**
- ❌ `devtools/` (already gitignored)
- ❌ `.venv/` (already gitignored)
- ❌ `logs/` (already gitignored)
- ❌ `MCTS/mcts_bridge` (will be built during deployment)
- ❌ `*.o`, `*.dSYM` (build artifacts)

### 3. Build Script

Your `build.sh` should:
1. Download LibTorch (if not provided by platform)
2. Compile the MCTS bridge
3. Install Python dependencies

See `my-chesshacks-bot/build.sh` for reference.

### 4. Directory Structure

Your repo should look like:
```
ChessMirror/
├── MCTS/
│   ├── src/
│   ├── include/
│   ├── Chess/
│   └── Makefile
├── my-chesshacks-bot/
│   ├── src/
│   │   └── main.py
│   ├── serve.py
│   ├── requirements.txt
│   └── build.sh
└── sobe_model.pt
```

### 5. Deploy to ChessHacks

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add C++ MCTS bot"
   git push
   ```

2. **Connect in ChessHacks Dashboard:**
   - Link your GitHub repo
   - Assign to a slot
   - ChessHacks will automatically:
     - Run your build script (if provided)
     - Compile C++ code
     - Install Python dependencies
     - Run your bot

## 🔍 How It Works

1. **ChessHacks detects your repo structure**
2. **Runs build process:**
   - Executes `build.sh` (if present) or compiles C++ automatically
   - Downloads libtorch (if needed)
   - Compiles `mcts_bridge` from C++ source
   - Installs Python dependencies
3. **Runs your bot:**
   - Starts `serve.py` on port 5058
   - Your bot is ready to play!

## ⚠️ Troubleshooting

**Build fails:**
- Check that `MCTS/` directory is included
- Verify `Makefile` is present in `MCTS/`
- Ensure `build.sh` has correct paths
- Check that LibTorch is available or can be downloaded

**Runtime errors:**
- Check ChessHacks logs in dashboard
- Verify `mcts_bridge` was built successfully
- Ensure model file path is correct (should be `sobe_model.pt` in repo root)

**Model not found:**
- Make sure model is committed (Git LFS) or downloadable
- Verify model path in `main.py` matches actual location
- Check that Git LFS files are properly downloaded

**Path issues:**
- Ensure `main.py` path resolution works for your repo structure
- Check that `MCTS/mcts_bridge` is built and accessible
- Verify `sobe_model.pt` is in the expected location

## 📝 Next Steps

1. ✅ Set up Git LFS for model file (or configure download)
2. ✅ Ensure `build.sh` is correct
3. ✅ Commit all necessary files
4. ✅ Push to GitHub
5. ✅ Connect repo in ChessHacks dashboard
6. ✅ Deploy and test!
