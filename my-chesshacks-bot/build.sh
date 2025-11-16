#!/bin/bash
# Build script for ChessHacks deployment
# This script builds the C++ MCTS bridge and sets up the environment
# Run from: my-chesshacks-bot/ directory

set -e  # Exit on error

echo "=== Building ChessHacks Bot ==="

# Determine project root (parent of my-chesshacks-bot)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Step 1: Download LibTorch if not present (in project root)
cd "$PROJECT_ROOT"
if [ ! -d "libtorch" ]; then
    echo "Downloading LibTorch..."
    wget -q https://download.pytorch.org/libtorch/cpu/libtorch-cxx11-abi-shared-with-deps-2.1.0%2Bcpu.zip
    unzip -q libtorch-cxx11-abi-shared-with-deps-2.1.0+cpu.zip
    rm libtorch-cxx11-abi-shared-with-deps-2.1.0+cpu.zip
    echo "LibTorch downloaded successfully"
else
    echo "LibTorch already present"
fi

# Step 2: Set environment variables
export LIBTORCH_PATH="$PROJECT_ROOT/libtorch"
export LD_LIBRARY_PATH=$LIBTORCH_PATH/lib:$LD_LIBRARY_PATH

# Step 3: Build MCTS bridge
echo "Building MCTS bridge..."
cd "$PROJECT_ROOT/MCTS"
LIBTORCH_PATH=$LIBTORCH_PATH make Bridge
cd "$PROJECT_ROOT"

# Step 4: Verify build
if [ -f "$PROJECT_ROOT/MCTS/mcts_bridge" ]; then
    echo "✓ MCTS bridge built successfully"
    chmod +x "$PROJECT_ROOT/MCTS/mcts_bridge"
else
    echo "✗ MCTS bridge build failed"
    exit 1
fi

# Step 5: Install Python dependencies
echo "Installing Python dependencies..."
cd "$SCRIPT_DIR"
pip install --no-cache-dir -r requirements.txt

echo "=== Build Complete ==="

