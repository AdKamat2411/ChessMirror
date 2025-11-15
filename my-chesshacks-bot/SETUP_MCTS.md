# MCTS + CNN Integration Setup

This bot uses the C++ MCTS engine with neural network evaluation. Follow these steps to set it up:

## Prerequisites

1. **LibTorch**: The C++ MCTS engine requires LibTorch. Download it from [PyTorch's website](https://pytorch.org/get-started/locally/).
   - Extract it to `~/libtorch` or `~/Downloads/libtorch`
   - Or set `LIBTORCH_PATH` environment variable to your LibTorch location

2. **Neural Network Model**: Ensure you have a trained model file (`.pt` format) in the project root.
   - Default path: `../aznet_traced.pt` (relative to `my-chesshacks-bot/`)
   - You can change this in `src/main.py` by modifying `MODEL_PATH`

## Building the MCTS Bridge

The MCTS bridge is a C++ executable that connects the Python bot to the C++ MCTS engine.

1. Navigate to the MCTS directory:
   ```bash
   cd ../MCTS
   ```

2. Build the bridge executable:
   ```bash
   make Bridge
   ```

   This will create `mcts_bridge` in the `MCTS/` directory.

3. Verify the build:
   ```bash
   ./mcts_bridge ../aznet_traced.pt "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
   ```
   
   This should output a UCI move (e.g., `e2e4`).

## Configuration

You can adjust MCTS parameters in `src/main.py`:

```python
MAX_ITERATIONS = 5000  # Maximum MCTS iterations per move
MAX_SECONDS = 2        # Maximum time per move (seconds)
CPUCT = 2.0            # PUCT exploration constant
```

## Troubleshooting

### "MCTS bridge executable not found"
- Make sure you've built the bridge: `cd MCTS && make Bridge`
- Check that `mcts_bridge` exists in the `MCTS/` directory

### "Neural network model not found"
- Ensure your model file exists at the path specified in `MODEL_PATH`
- Default path is `../aznet_traced.pt` (relative to `my-chesshacks-bot/`)

### LibTorch errors
- Make sure LibTorch is installed and `LIBTORCH_PATH` is set correctly
- Check the Makefile in `MCTS/` for LibTorch path detection

### Build errors
- Ensure you have a C++17 compatible compiler (g++ or clang++)
- Check that all dependencies are installed (see `MCTS/LIBTORCH_SETUP.md`)

## How It Works

1. The Python bot (`main.py`) receives a board position from ChessHacks
2. It converts the board to FEN format
3. It calls the C++ MCTS bridge via subprocess
4. The bridge loads the neural network, runs MCTS search, and returns the best move
5. The Python bot converts the UCI move string to a python-chess Move object
6. The move is returned to ChessHacks

## Next Steps

- Adjust MCTS parameters for your use case (speed vs. strength tradeoff)
- Consider caching the MCTS tree between moves for better performance
- Enhance the bridge to return move probabilities for better visualization

