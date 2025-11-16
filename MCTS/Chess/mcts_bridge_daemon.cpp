/**
 * MCTS Bridge Daemon: Persistent process that keeps model loaded
 * Usage: ./mcts_bridge_daemon <model_path> [max_iterations] [max_seconds] [cpuct]
 * Reads FEN strings from stdin, outputs moves to stdout
 * Format: One FEN per line, outputs move on same line
 */

#include "Chess.h"
#include "../include/mcts.h"
#include "../include/neural_network.h"
#include "../include/chess.hpp"
#include <iostream>
#include <string>
#include <fstream>
#include <chrono>
#include <iomanip>

using namespace std;
using namespace chess;

int main(int argc, char* argv[]) {
    // Parse arguments
    if (argc < 2) {
        cerr << "Usage: " << argv[0] << " <model_path> [max_iterations] [max_seconds] [cpuct]" << endl;
        cerr << "Example: " << argv[0] << " ../aznet_traced.pt" << endl;
        cerr << "Then send FEN strings via stdin, one per line" << endl;
        return 1;
    }
    
    string model_path = argv[1];
    
    // Default MCTS parameters
    int max_iterations = 15000;
    int max_seconds = 5;
    double cpuct = 2.0;
    
    if (argc >= 3) {
        max_iterations = stoi(argv[2]);
    }
    if (argc >= 4) {
        max_seconds = stoi(argv[3]);
    }
    if (argc >= 5) {
        cpuct = stod(argv[4]);
    }
    
    // Load neural network ONCE at startup
    cerr << "[DAEMON] Loading model..." << endl;
    auto load_start = chrono::high_resolution_clock::now();
    NeuralNetwork* nn = new NeuralNetwork();
    bool nn_loaded = false;
    if (!model_path.empty() && model_path != "none") {
        nn_loaded = nn->load_model(model_path);
        if (!nn_loaded) {
            cerr << "ERROR: Failed to load neural network from: " << model_path << endl;
            delete nn;
            return 1;
        }
    }
    auto load_end = chrono::high_resolution_clock::now();
    double load_time = chrono::duration<double>(load_end - load_start).count();
    cerr << "[DAEMON] Model loaded in " << fixed << setprecision(3) << load_time << "s" << endl;
    cerr << "[DAEMON] Ready for FEN input (one per line)" << endl;
    
    // Process FEN strings from stdin
    string line;
    while (getline(cin, line)) {
        if (line.empty()) {
            continue;
        }
        
        string fen = line;
        
        // Create initial state from FEN
        Chess_state* initial_state = new Chess_state(fen);
        
        // Create engine agent
        MCTS_agent* engine = new MCTS_agent(
            initial_state,
            max_iterations,
            max_seconds,
            nn_loaded ? nn : nullptr,
            cpuct
        );
        
        // Generate move
        auto search_start = chrono::high_resolution_clock::now();
        const MCTS_move* engine_move = engine->genmove(nullptr);
        auto search_end = chrono::high_resolution_clock::now();
        double search_time = chrono::duration<double>(search_end - search_start).count();
        
        if (!engine_move) {
            cerr << "ERROR: Engine returned no move for FEN: " << fen << endl;
            delete engine;
            continue;
        }
        
        // Output move in UCI format to stdout
        const Chess_move* chess_move = static_cast<const Chess_move*>(engine_move);
        string move_str = chess_move->sprint();
        
        // Output to stdout (flush immediately)
        cout << move_str << endl;
        cout.flush();
        
        // Log timing to stderr
        cerr << "[TIMING] MCTS search: " << fixed << setprecision(3) << search_time << "s" << endl;
        
        // Cleanup (but keep model loaded)
        delete engine;
    }
    
    // Cleanup model on exit
    delete nn;
    return 0;
}

