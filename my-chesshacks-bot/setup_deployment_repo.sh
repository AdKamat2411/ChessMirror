#!/bin/bash
# Script to set up a clean deployment repository for ChessHacks
# Usage: ./setup_deployment_repo.sh [target_directory]

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TARGET_DIR="${1:-$HOME/Desktop/Projects/chesshacks-bot-deploy}"

echo "=== Setting up ChessHacks Deployment Repository ==="
echo "Source: $PROJECT_ROOT"
echo "Target: $TARGET_DIR"
echo ""

# Create target directory
if [ -d "$TARGET_DIR" ]; then
    echo "⚠️  Directory $TARGET_DIR already exists!"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    mkdir -p "$TARGET_DIR"
fi

cd "$TARGET_DIR"

# Initialize git repo if not already
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
fi

# Copy bot code
echo "Copying bot code..."
mkdir -p src/utils
cp -r "$PROJECT_ROOT/my-chesshacks-bot/src/"* src/
if [ -d "$PROJECT_ROOT/my-chesshacks-bot/src/utils" ]; then
    cp -r "$PROJECT_ROOT/my-chesshacks-bot/src/utils/"* src/utils/
fi

# Copy server and requirements
echo "Copying server files..."
cp "$PROJECT_ROOT/my-chesshacks-bot/serve.py" ./
cp "$PROJECT_ROOT/my-chesshacks-bot/requirements.txt" ./

# Copy MCTS source (needed for building)
echo "Copying MCTS source code..."
mkdir -p MCTS
cp -r "$PROJECT_ROOT/MCTS/src" MCTS/
cp -r "$PROJECT_ROOT/MCTS/include" MCTS/
cp -r "$PROJECT_ROOT/MCTS/Chess" MCTS/
cp "$PROJECT_ROOT/MCTS/Makefile" MCTS/

# Copy Docker files (use deployment-specific version if available)
echo "Copying Docker configuration..."
if [ -f "$PROJECT_ROOT/my-chesshacks-bot/Dockerfile.deploy" ]; then
    cp "$PROJECT_ROOT/my-chesshacks-bot/Dockerfile.deploy" ./Dockerfile
    echo "✓ Using deployment-specific Dockerfile"
else
    cp "$PROJECT_ROOT/Dockerfile" ./
    # Update paths for separate repo structure
    sed -i.bak 's|my-chesshacks-bot/requirements.txt|requirements.txt|g' Dockerfile
    sed -i.bak 's|my-chesshacks-bot/src/|src/|g' Dockerfile
    sed -i.bak 's|my-chesshacks-bot/serve.py|serve.py|g' Dockerfile
    rm -f Dockerfile.bak
    echo "✓ Updated Dockerfile for separate repo structure"
fi
cp "$PROJECT_ROOT/.dockerignore" ./

# Copy model file
echo "Copying model file..."
if [ -f "$PROJECT_ROOT/chessnet_new_ts.pt" ]; then
    cp "$PROJECT_ROOT/chessnet_new_ts.pt" ./
    echo "✓ Model file copied"
else
    echo "⚠️  Model file not found at $PROJECT_ROOT/chessnet_new_ts.pt"
    echo "   You'll need to add it manually or configure download in Dockerfile"
fi

# Create .gitignore
echo "Creating .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.pyc

# Logs
logs/
*.log

# Build artifacts (will be built in Docker)
MCTS/*.o
MCTS/*.dSYM
MCTS/mcts_bridge
MCTS/chess_play
MCTS/chess_mcts
MCTS/*.out

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Environment
.env
.env.local

# Git LFS pointer files (if not using LFS)
# Uncomment if not using Git LFS:
# *.pt
EOF

# Create README
echo "Creating README..."
cat > README.md << 'EOF'
# ChessHacks Bot - Deployment Repository

This is the deployment repository for the ChessHacks MCTS bot.

## Structure

- `src/` - Bot implementation
- `serve.py` - FastAPI server
- `requirements.txt` - Python dependencies
- `MCTS/` - C++ MCTS engine source (built in Docker)
- `Dockerfile` - Container build configuration
- `chessnet_new_ts.pt` - Neural network model (via Git LFS)

## Deployment

This repository is configured for ChessHacks deployment:

1. Push to GitHub
2. Connect in ChessHacks dashboard
3. ChessHacks will automatically:
   - Build the Docker container
   - Compile the C++ MCTS engine
   - Run your bot

## Local Testing

If you have Docker installed:

```bash
docker build -t chesshacks-bot .
docker run -p 5058:5058 chesshacks-bot
```

## Model File

The model file (`chessnet_new_ts.pt`) should be tracked with Git LFS:

```bash
git lfs install
git lfs track "chessnet_new_ts.pt"
git add .gitattributes chessnet_new_ts.pt
```

If the file is too large, configure the Dockerfile to download it during build.
EOF

# Set up Git LFS if available
if command -v git-lfs &> /dev/null; then
    echo ""
    echo "Setting up Git LFS for model file..."
    git lfs install
    git lfs track "chessnet_new_ts.pt"
    echo "✓ Git LFS configured"
else
    echo ""
    echo "⚠️  Git LFS not found. Install it for large model files:"
    echo "   brew install git-lfs  # macOS"
    echo "   Then run: git lfs install && git lfs track 'chessnet_new_ts.pt'"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Review the files in: $TARGET_DIR"
echo "2. Set up Git LFS if needed:"
echo "   cd $TARGET_DIR"
echo "   git lfs install"
echo "   git lfs track 'chessnet_new_ts.pt'"
echo "3. Initial commit:"
echo "   cd $TARGET_DIR"
echo "   git add ."
echo "   git commit -m 'Initial deployment repo'"
echo "4. Create GitHub repo and push:"
echo "   git remote add origin https://github.com/yourusername/chesshacks-bot-deploy.git"
echo "   git push -u origin main"
echo ""

