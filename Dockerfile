# Multi-stage build for ChessHacks bot with C++ MCTS engine
# Build from project root: docker build -t chesshacks-bot -f Dockerfile .

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download and extract LibTorch (CPU version for Linux)
WORKDIR /tmp
RUN wget https://download.pytorch.org/libtorch/cpu/libtorch-cxx11-abi-shared-with-deps-2.1.0%2Bcpu.zip \
    && unzip -q libtorch-cxx11-abi-shared-with-deps-2.1.0+cpu.zip \
    && mv libtorch /opt/libtorch \
    && rm libtorch-cxx11-abi-shared-with-deps-2.1.0+cpu.zip

# Copy MCTS source code
WORKDIR /app
COPY MCTS/ /app/MCTS/

# Build the MCTS bridge executable
WORKDIR /app/MCTS
RUN LIBTORCH_PATH=/opt/libtorch make Bridge

# Final stage - runtime
FROM python:3.11-slim

# Install runtime dependencies for libtorch
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy LibTorch libraries
COPY --from=builder /opt/libtorch /opt/libtorch

# Copy built executable
COPY --from=builder /app/MCTS/mcts_bridge /app/mcts_bridge
RUN chmod +x /app/mcts_bridge

# Copy Python bot code
WORKDIR /app
COPY my-chesshacks-bot/requirements.txt /app/requirements.txt
COPY my-chesshacks-bot/src/ /app/src/
COPY my-chesshacks-bot/serve.py /app/serve.py

# Copy model file
# IMPORTANT: The model file must be available in the build context.
# Options:
# 1. Use Git LFS: git lfs track "sobe_model.pt" && git add sobe_model.pt
# 2. Download during build: Uncomment the RUN wget line below and provide URL
# 3. Host on GitHub Releases and download in build
COPY sobe_model.pt /app/model.pt
# Verify model file is not corrupted (PyTorch models are zip archives)
RUN python3 -c "import zipfile; z = zipfile.ZipFile('/app/model.pt', 'r'); z.testzip()" || \
    (echo "ERROR: Model file appears corrupted. Check file size and integrity." && exit 1)
# Alternative: Download from URL (uncomment and update):
# RUN wget -O /app/model.pt https://github.com/yourusername/yourrepo/releases/download/v1.0/sobe_model.pt || \
#     (echo "ERROR: Model file not found. Please configure model download in Dockerfile." && exit 1)

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV LIBTORCH_PATH=/opt/libtorch
ENV LD_LIBRARY_PATH=/opt/libtorch/lib:$LD_LIBRARY_PATH
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5058

# Run the bot server
CMD ["python", "serve.py"]

