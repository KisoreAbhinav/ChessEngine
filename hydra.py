# hydra.py
from defs import Board, AllInit
from perft import PerftTest

def main():
    print("Initializing Hydra 1.0")
    AllInit()
    
    board = Board()
    
    # Standard "Castle 2" test position
    test_fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    board.parse_fen(test_fen)
    board.print_board()
    
    # Run Perft to depth 3
    # Known nodes for Castle 2: 
    # Depth 1: 48
    # Depth 2: 2039
    # Depth 3: 97862
    PerftTest(3, board)

if __name__ == "__main__":
    main()