# hydra.py
from defs import *

def main():
    AllInit()
'''------------------------------TEST FEN PARSING--------------------------
    board = Board()
    
    # 3. Test Case: Starting Position
    START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print(f"\nParsing FEN: {START_FEN}")
    board.parse_fen(START_FEN)
    
    # 4. Print the Board for Visual Verification
    # (Assuming you added the print_board method to your Board class)
    board.print_board()

    # 5. Diagnostic Data Check
    print("\n--- Diagnostic Check ---")
    
    # Check Side to Move
    print(f"Side to move: {'White' if board.side == Side.WHITE else 'Black'}")
    assert board.side == Side.WHITE, "Error: Side should be White"
    
    # Check Castling Permissions (15 = 1111 in binary, all sides can castle)
    print(f"Castling Permissions (Hex): {board.castle_perm:X}")
    assert board.castle_perm == 15, "Error: Castling permissions should be 15"
    
    # Check Hash Key (Should not be 0)
    print(f"Position Hash Key: {board.pos_key:X}")
    assert board.pos_key != 0, "Error: Hash key was not generated"

    # 6. Piece Count Verification (The Part 16 Logic)
    # White: 8 Pawns, 8 Big (K, Q, 2R, 2B, 2N), 4 Major (K, Q, 2R), 4 Minor (2B, 2N)
    print(f"White Pieces - Big: {board.big_pce[Side.WHITE]}, Maj: {board.maj_pce[Side.WHITE]}, Min: {board.min_pce[Side.WHITE]}")
    
    assert board.pce_num[Pieces.wP] == 8, f"Expected 8 White Pawns, got {board.pce_num[Pieces.wP]}"
    assert board.big_pce[Side.WHITE] == 8, f"Expected 8 White Big Pieces, got {board.big_pce[Side.WHITE]}"
    assert board.maj_pce[Side.WHITE] == 4, f"Expected 4 White Major Pieces, got {board.maj_pce[Side.WHITE]}"
    assert board.min_pce[Side.WHITE] == 4, f"Expected 4 White Minor Pieces, got {board.min_pce[Side.WHITE]}"

    # 7. Piece List Verification
    # Check if White King is actually on E1
    wK_sq = board.p_list[Pieces.wK][0]
    print(f"White King found at square: {wK_sq} (E1 is {Square.E1})")
    assert wK_sq == Square.E1, "Error: White King not found on E1 in Piece List"

    print("\n[COMPLETE] All internal structures synchronized successfully!")
'''

'''
------------------------TEST RESET BOARD--------------------------
    board = Board()
    
    # Manually mess up the board to test the reset
    board.side = Side.BLACK
    board.pieces[Square.E2] = Pieces.wP
    
    # Perform the reset
    board.reset_board()
    
    print(f"Engine: {ENGINE_NAME}")
    print(f"Board Side after reset (should be 2): {board.side}")
    print(f"Square E2 after reset (should be 0): {board.pieces[Square.E2]}")
'''

"""
-------------------------TEST BITBOARD------------------------------

    play_bitboard = 0
    
    # Adding a pawn to D2
    sq_d2_64 = Sq120to64[Square.D2]
    play_bitboard |= (1 << sq_d2_64) # Bitwise OR to set the bit
    
    # Adding a pawn to G2
    sq_g2_64 = Sq120to64[Square.G2]
    play_bitboard |= (1 << sq_g2_64)
    
    # Visualize the result
    print_bitboard(play_bitboard)

    for index in range(BOARD_SQ_NUM):
        if index % 10 == 0:
            print()

        print(f"{Sq120to64[index]:5}", end="")

    print("\n\n")
    for index in range(64):
        if index % 8 == 0:
            print()
            
        print(f"{Sq64to120[index]:5}", end="")
    
    print()
"""

if __name__ == "__main__":
    main()