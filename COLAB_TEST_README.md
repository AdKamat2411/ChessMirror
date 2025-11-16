# Testing MCTS on Google Colab with T4 GPU

## Quick Start

1. **Open the notebook:**
   - Upload `MCTS_COLAB_TEST.ipynb` to Google Colab
   - Or open it directly if it's in your GitHub repo

2. **Enable GPU:**
   - Runtime → Change runtime type → GPU (T4)

3. **Run the cells in order:**
   - Step 1: Installs build tools and checks GPU
   - Step 2: Downloads LibTorch with CUDA support
   - Step 3: Upload your MCTS source code
   - Step 4: Compiles the MCTS bridge
   - Step 5: Upload your model file
   - Step 6: Tests MCTS and shows stats
   - Step 7: Performance analysis

## What You'll See

The notebook will show:
- **MCTS Stats** from the debug output:
  - `[DEBUG] Iterations: <count>`
  - `[DEBUG] Time: <seconds>s`
  - `[DEBUG] Positions/s: <rate>`
- **Selected move** (UCI format)
- **Full debug output** from the C++ engine

## Uploading Files

### Option 1: Upload MCTS folder
1. Zip your `MCTS/` folder locally
2. In Step 3, uncomment the upload code
3. Upload the zip file when prompted

### Option 2: Clone from GitHub
If your repo is public:
```python
!git clone https://github.com/yourusername/ChessMirror.git /content/ChessMirror
MCTS_DIR = "/content/ChessMirror/MCTS"
```

### Option 3: Manual upload
Use Colab's file browser to upload individual files to `/content/MCTS/`

## Model File

Upload your `chessnet_new_ts.pt` model file in Step 5. The notebook will handle it automatically.

## GPU Acceleration

The notebook automatically:
- Downloads LibTorch with CUDA 11.8 support (for T4)
- Sets `CUDA_VISIBLE_DEVICES=0`
- Configures `LD_LIBRARY_PATH` for GPU libraries

Your C++ code will use GPU if `torch::cuda::is_available()` returns true (which it should on Colab T4).

## Performance Testing

The last cell parses MCTS stats and shows:
- Total iterations completed
- Time taken
- Positions evaluated per second
- Selected move

You can modify the MCTS parameters:
```python
max_iterations = 20000  # Increase for deeper search
max_seconds = 10        # More time per move
cpuct = 1.5            # Exploration constant
```

## Troubleshooting

**Compilation fails:**
- Check that all MCTS source files are uploaded
- Verify LibTorch downloaded correctly
- Check the error messages in the output

**GPU not detected:**
- Make sure GPU runtime is enabled (Runtime → Change runtime type)
- Check `torch.cuda.is_available()` in Step 1

**Model not found:**
- Upload the model file in Step 5
- Check the path is `/content/model.pt`

**MCTS stats not showing:**
- The stats are in `stderr` output
- Check the "STDERR (debug output)" section
- Make sure your C++ code is printing `[DEBUG]` messages

## Next Steps

After testing, you can:
- Adjust MCTS parameters for better performance
- Test different positions
- Compare CPU vs GPU performance
- Profile the neural network inference time




