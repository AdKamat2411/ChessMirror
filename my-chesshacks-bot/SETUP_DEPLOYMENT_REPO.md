# Setting Up a Separate Deployment Repository

## Why a Separate Repo?

ChessHacks recommends separating training from deployment:
- ✅ Lightweight repo (fast to clone)
- ✅ Focused on inference only
- ✅ Clean version control
- ✅ No training dependencies

## Recommended Structure

Create a new repository (e.g., `chesshacks-bot-deploy`) with only:

```
chesshacks-bot-deploy/
├── Dockerfile              # Container build config
├── .dockerignore           # Docker build exclusions
├── .gitignore              # Git exclusions
├── README.md               # Deployment instructions
├── src/                    # Bot code
│   ├── main.py
│   └── utils/
├── serve.py                # FastAPI server
├── requirements.txt        # Python dependencies
├── MCTS/                   # C++ MCTS source (for building)
│   ├── src/
│   ├── include/
│   ├── Chess/
│   └── Makefile
└── chessnet_new_ts.pt      # Model file (via Git LFS)
```

## Setup Steps

### Option 1: Create New Repo from Scratch (Recommended)

1. **Create new directory:**
   ```bash
   cd ~/Desktop/Projects
   mkdir chesshacks-bot-deploy
   cd chesshacks-bot-deploy
   git init
   ```

2. **Copy necessary files:**
   ```bash
   # From ChessMirror directory
   cp -r my-chesshacks-bot/src ./src
   cp my-chesshacks-bot/serve.py ./
   cp my-chesshacks-bot/requirements.txt ./
   cp -r MCTS ./MCTS
   cp Dockerfile ./
   cp .dockerignore ./
   cp chessnet_new_ts.pt ./
   ```

3. **Create .gitignore:**
   ```bash
   cat > .gitignore << EOF
   # Python
   __pycache__/
   *.py[cod]
   .venv/
   venv/

   # Logs
   logs/
   *.log

   # Build artifacts
   MCTS/*.o
   MCTS/*.dSYM
   MCTS/mcts_bridge
   MCTS/chess_play
   MCTS/chess_mcts

   # IDE
   .vscode/
   .idea/
   .DS_Store
   EOF
   ```

4. **Set up Git LFS for model:**
   ```bash
   git lfs install
   git lfs track "chessnet_new_ts.pt"
   ```

5. **Initial commit:**
   ```bash
   git add .
   git commit -m "Initial deployment repo for ChessHacks bot"
   ```

6. **Create GitHub repo and push:**
   ```bash
   # Create repo on GitHub first, then:
   git remote add origin https://github.com/yourusername/chesshacks-bot-deploy.git
   git push -u origin main
   ```

### Option 2: Use the Setup Script

Run the provided script (see below) to automate the setup.

## What NOT to Include

❌ **Don't copy:**
- Training code (`colab_training_template.ipynb`, `config.py`, etc.)
- Training data (`data/`)
- Other model files (only `chessnet_new_ts.pt`)
- Devtools (`devtools/`)
- Logs (`logs/`)
- Build artifacts (`*.o`, `mcts_bridge`, etc.)

## After Setup

1. **Test locally** (if you have Docker):
   ```bash
   docker build -t chesshacks-bot .
   docker run -p 5058:5058 chesshacks-bot
   ```

2. **Connect to ChessHacks:**
   - Link your GitHub repo in ChessHacks dashboard
   - Assign to a slot
   - Deploy!

## Updating the Deployment Repo

When you update your bot:

1. **Update in main repo** (`ChessMirror`)
2. **Copy changes to deployment repo:**
   ```bash
   # From ChessMirror directory
   cp -r my-chesshacks-bot/src/* ../chesshacks-bot-deploy/src/
   cp my-chesshacks-bot/serve.py ../chesshacks-bot-deploy/
   cp my-chesshacks-bot/requirements.txt ../chesshacks-bot-deploy/
   # If MCTS code changed:
   cp -r MCTS/* ../chesshacks-bot-deploy/MCTS/
   ```
3. **Commit and push:**
   ```bash
   cd ../chesshacks-bot-deploy
   git add .
   git commit -m "Update bot logic"
   git push
   ```

## Alternative: Keep Everything in One Repo

If you prefer to keep everything together:

1. **Structure your main repo better:**
   ```
   ChessMirror/
   ├── training/          # All training code
   ├── deployment/        # Clean deployment files
   │   ├── Dockerfile
   │   ├── src/
   │   └── ...
   └── ...
   ```

2. **Point ChessHacks to a subdirectory** (if they support it)

However, **separate repo is cleaner** and follows ChessHacks best practices.




