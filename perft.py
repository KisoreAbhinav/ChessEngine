# perft.py
from move_gen import GenerateAllMoves, MoveList
from make_mov import MakeMove, TakeMove
from move_io import PrMove
import time

# This is the core recursive function
def Perft(depth, board):
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
        
    return nodes

# This is the 'Divide' version to help debug specific move branches
def PerftTest(depth, board):
    print(f"\n--- Starting Perft Test: Depth {depth} ---")
    start_time = time.time()
    
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
        
        total_nodes += branch_nodes
        print(f"Move {i+1:2}: {PrMove(move)} : {branch_nodes}")
        
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nTest Complete: {total_nodes} nodes visited.")
    print(f"Time: {duration:.2f}s")
    if duration > 0:
        print(f"Nodes per second: {int(total_nodes / duration)}")