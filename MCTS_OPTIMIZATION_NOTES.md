# MCTS Performance Optimization Guide

## Current Bottlenecks (in order of impact)

### 1. **Neural Network Inference** ⚠️ **BIGGEST BOTTLENECK**
- **Impact**: ~80-90% of total time
- **Current**: Single inference per new node (~10-50ms each)
- **Location**: `neural_network.cpp::predict()`
- **Issues**:
  - No batching - one position at a time
  - Tensor creation overhead (`.clone()` on every call)
  - Board encoding happens every time

**Optimizations**:
1. **Batch Inference** (10-50x speedup potential)
   - Collect 8-32 positions before calling NN
   - Single forward pass for all positions
   - Requires refactoring `evaluate()` to support batched mode

2. **Tensor Reuse** (2-3x speedup)
   - Pre-allocate input tensor buffer
   - Reuse tensor memory instead of cloning
   - Use `torch::from_blob()` without `.clone()` if data persists

3. **Position Caching** (variable speedup)
   - Cache NN evaluations by position hash (Zobrist hash)
   - Skip re-evaluation of transpositions
   - Memory vs speed tradeoff

4. **Model Optimization**
   - Use TorchScript optimization: `torch.jit.optimize_for_inference()`
   - Quantization (INT8) - 2-4x speedup with minimal accuracy loss
   - Smaller model architecture

### 2. **Board Encoding** (5-10% of time)
- **Location**: `neural_network.cpp::encode_board()`
- **Issues**: Vector allocations, bit operations

**Optimizations**:
- Pre-allocate encoding buffer
- Use stack-allocated arrays instead of vectors
- SIMD optimizations for bit operations

### 3. **Dynamic Casts** (2-5% of time)
- **Location**: Multiple places in `mcts.cpp`
- **Issues**: Runtime type checking overhead

**Optimizations**:
- Replace `dynamic_cast<Chess_state*>` with `static_cast` where safe
- Cache cast results in node structure
- Use virtual functions instead of casting

### 4. **Memory Allocations** (2-5% of time)
- **Location**: `new MCTS_node()`, `new Chess_state()`
- **Issues**: Heap allocations are slow

**Optimizations**:
- Object pooling for nodes
- Use memory arena allocator
- Pre-allocate node pools

### 5. **Move Generation** (1-3% of time)
- **Location**: `movegen::legalmoves()` called multiple times
- **Issues**: Regenerating moves for same position

**Optimizations**:
- Cache legal moves in node
- Only generate once per position

### 6. **Tree Traversal** (1-2% of time)
- **Location**: `select_best_child()` iterates all children
- **Issues**: Linear scan through children

**Optimizations**:
- Early termination when score is clearly best
- Pre-sort children by PUCT score
- Use priority queue for top-k selection

## Quick Wins (Easy to implement)

### 1. Remove `.clone()` from tensor creation
```cpp
// Current (slow):
torch::Tensor input_tensor = torch::from_blob(...).clone();

// Optimized (faster):
// Pre-allocate once, reuse buffer
static thread_local torch::Tensor input_buffer = torch::empty({1, 18, 8, 8});
// Copy data into buffer without clone
```

### 2. Cache dynamic_cast results
```cpp
// Store Chess_state* directly in node instead of casting every time
class MCTS_node {
    Chess_state* chess_state_;  // Cached cast result
};
```

### 3. Pre-allocate encoding buffer
```cpp
// Use static thread-local buffer
thread_local std::vector<float> encoding_buffer(18 * 8 * 8);
```

### 4. Batch inference (requires more work)
- Modify `evaluate()` to accept batch of positions
- Collect positions during tree growth
- Call NN once per batch instead of once per position

## Expected Performance Gains

| Optimization | Difficulty | Speedup | Total Impact |
|-------------|------------|---------|--------------|
| Remove tensor clone | Easy | 1.5-2x | 10-15% |
| Cache dynamic casts | Easy | 1.1-1.2x | 2-3% |
| Pre-alloc buffers | Easy | 1.1-1.2x | 1-2% |
| Batch inference (8) | Medium | 5-8x | 40-60% |
| Batch inference (32) | Medium | 10-20x | 60-80% |
| Position caching | Medium | 1.5-3x | 10-20% |
| Model quantization | Hard | 2-4x | 15-30% |

## Implementation Priority

1. **Quick wins first** (1-2 hours):
   - Remove `.clone()`
   - Cache dynamic casts
   - Pre-allocate buffers

2. **Batch inference** (4-8 hours):
   - Most impactful optimization
   - Requires refactoring evaluation loop

3. **Position caching** (2-4 hours):
   - Good for positions with many transpositions
   - Memory overhead consideration

4. **Model optimization** (ongoing):
   - Quantization
   - Architecture changes

## Current Performance Baseline

From logs:
- **Iterations**: ~200-1000 per 2 seconds
- **Positions/s**: ~77-89
- **Time per iteration**: ~2-10ms

**Target after optimizations**:
- **Positions/s**: 500-2000+ (10-20x improvement)
- **Time per iteration**: 0.5-2ms




