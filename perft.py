# perft.py
from move_gen import GenerateAllMoves, MoveList
from make_mov import MakeMove, TakeMove
from move_io import PrMove
from misc import GetTimeMs

# This is the core recursive function
def Perft(depth, board):
    assert board.check_board()

    # Base case: if we reach depth 0, we've found 1 leaf node
    if depth == 0:
        return 1
    
    nodes = 0
    move_list = MoveList()
    GenerateAllMoves(board, move_list)
    
    for i in range(move_list.count):
        move = move_list.moves[i].move
        
        if not MakeMove(board, move):
            continue
            
        # Recursively call Perft for the next depth
        nodes += Perft(depth - 1, board)
        
        # Always take back the move to keep the board state consistent
        TakeMove(board)
        assert board.check_board()
        
    return nodes

# This is the 'Divide' version to help debug specific move branches
def PerftTest(depth, board, expected_nodes=None, label=""):
    print(f"\n--- Starting Perft Test: Depth {depth} ---")
    if label:
        print(f"Position: {label}")
    start_ms = GetTimeMs()
    
    move_list = MoveList()
    GenerateAllMoves(board, move_list)
    
    total_nodes = 0
    
    # Loop through each move at the root individually
    for i in range(move_list.count):
        move = move_list.moves[i].move
        
        if not MakeMove(board, move):
            continue
            
        # Get nodes for this specific branch
        branch_nodes = Perft(depth - 1, board)
        TakeMove(board)
        assert board.check_board()
        
        total_nodes += branch_nodes
        print(f"Move {i+1:2}: {PrMove(move)} : {branch_nodes}")
        
    elapsed_ms = GetTimeMs() - start_ms
    elapsed_s = elapsed_ms / 1000.0
    
    print(f"\nTest Complete: {total_nodes} nodes visited.")
    print(f"Time: {elapsed_ms}ms ({elapsed_s:.2f}s)")
    if elapsed_ms > 0:
        print(f"Nodes per second: {int((total_nodes * 1000) / elapsed_ms)}")

    if expected_nodes is not None:
        if total_nodes == expected_nodes:
            print(f"Result: PASS (expected {expected_nodes})")
        else:
            print(f"Result: FAIL (expected {expected_nodes}, got {total_nodes})")

    return total_nodes

def PerftBenchmark(depth, board, expected_nodes=None, label=""):
    assert board.check_board()

    print(f"\n--- Perft Benchmark: Depth {depth} ---")
    if label:
        print(f"Position: {label}")

    start_ms = GetTimeMs()
    total_nodes = Perft(depth, board)
    elapsed_ms = GetTimeMs() - start_ms
    elapsed_s = elapsed_ms / 1000.0

    print(f"Nodes: {total_nodes}")
    print(f"Time: {elapsed_ms}ms ({elapsed_s:.2f}s)")
    if elapsed_ms > 0:
        print(f"Nodes per second: {int((total_nodes * 1000) / elapsed_ms)}")

    if expected_nodes is not None:
        if total_nodes == expected_nodes:
            print(f"Result: PASS (expected {expected_nodes})")
        else:
            print(f"Result: FAIL (expected {expected_nodes}, got {total_nodes})")

    return total_nodes
