# hydra.py
from move_gen import *
from defs import *
from move_io import *

def main():
    print("Initializing Hydra 1.0")
    AllInit()
    print("Hydra 1.0 Initialized")

    board = Board()
    move_list = MoveList()

    # The specific FEN from Video 33
    test_fen = "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N w - - 0 1"
    
    print("\n--- TEST: Video 33 Non-Slider Pieces (Knights/Kings) ---")
    board.parse_fen(test_fen)
    
    # Generate moves
    GenerateAllMoves(board, move_list)
    
    print(f"Total Moves Generated: {move_list.count}")
    
    # To verify like the video, print the moves specifically for the pieces
    for i in range(move_list.count):
        move = move_list.moves[i].move
        print(f"Move {i+1}: {PrMove(move)}")


#--------------------------------------------------------------------------------------------------
'''
    board = Board()
    move_list = MoveList()

    # Mirror position from Part 31 (Black to move)
    fen_part_31 = "rnbqkbnr/p1p1p3/3p3p/1p1p4/2P1PpP2/8/PP1P1PpP/RNBQKB1R b KQkq e3 0 1"
    
    print("\n--- TEST: Part 31 Black Pawn Moves ---")
    board.parse_fen(fen_part_31)
    GenerateAllMoves(board, move_list)
    
    print(f"Expected: 26 Moves | Result: {move_list.count} Moves")
    
    for i in range(move_list.count):
        print(f"{i+1}: {PrMove(move_list.moves[i].move)}")
'''

'''----------------MOVE GEN AND COUNT TEST(HATE THIS PART, TOOK 2 HOURS OMG)-----------
    board = Board()
    move_list = MoveList()

    fen_part_30 = "rnbqkb1r/pp1p1pPp/8/2p1pP2/1P1P4/3P3P/P1P1P3/RNBQKBNR w KQkq e6 0 1"
    
    print("\n--- TEST: Part 30 White Pawn Moves ---")
    board.parse_fen(fen_part_30)
    board.print_board()
    
    GenerateAllMoves(board, move_list)
    
    print(f"Test Expected: 26 Moves")
    print(f"Test Result:   {move_list.count} Moves")
    
    print("\nMove List:")
    for i in range(move_list.count):
        move = move_list.moves[i].move
        print(f"{i+1}: {PrMove(move)}")
'''

'''--------------PRINT MOVE AND SQUARES TEST-----------------------------
    m = MOVE(31, 51, Pieces.EMPTY, Pieces.EMPTY, PAWN_START_FLAG)
    
    print(f"From Square 31: {PrSq(31)}")
    print(f"Full Move String: {PrMove(m)}")
    
    # Simulate a Promotion: a7 to a8 promoting to a Queen
    promo_move = MOVE(81, 91, Pieces.EMPTY, Pieces.wQ, 0)
    print(f"Promotion Move: {PrMove(promo_move)}")
'''

'''------------------------MOVE FORMAT AND BITS TEST--------------------
    from_sq = 22
    to_sq = 42
    captured = Pieces.bN # 8
    promoted = Pieces.wQ # 5
    flags = PAWN_START_FLAG
    
    # Pack the move
    my_move = MOVE(from_sq, to_sq, captured, promoted, flags)
    
    # Unpack and Print
    print(f"Test Move Integer: {my_move}")
    print(f"Unpacked From: {FROMSQ(my_move)}")
    print(f"Unpacked To: {TOSQ(my_move)}")
    print(f"Unpacked Captured Piece: {CAPTURED(my_move)}")
    print(f"Unpacked Promoted Piece: {PROMOTED(my_move)}")
    
    # 3. Check Flags
    if my_move & PAWN_START_FLAG:
        print("Flag Check: This is a Pawn Start!")
'''

'''-------------- ATTACKED SQUARES VISUALIZATION------------------------
enable the show attacked function to print the board too
    board = Board()

    # 3. Set up a specific test position
    # White Queen on e4, White Knight on g3, Black Pawn on d5
    test_fen = "8/8/8/3p4/4Q3/6N1/8/8 w - - 0 1"
    board.parse_fen(test_fen)
    
    print("Current Board State:")
    board.print_board()

    # 4. Run the Attack Tests
    show_attacked_squares(board, Side.WHITE)
    show_attacked_squares(board, Side.BLACK)
'''


''' --------------- Forcing an error for Check Board Function--------
    board = Board()

    board.parse_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    print("--- Testing Board Integrity ---")

    # 2. This should pass quietly
    if board.check_board():
        print("Initial Board: OK")

    # 3. FORCE A FAIL: Manually corrupt the material count
    print("\nCorrupting material count...")
    board.material[Side.WHITE] -= 100 

    try:
        board.check_board()
    except AssertionError as e:
        print(f"Caught Expected Error: {e}")

    # 4. FORCE A FAIL: Corrupt the Hash Key
    print("\nCorrupting Position Key...")
    board.pos_key ^= 123456789 # Flip some bits in the hash

    try:
        board.check_board()
    except AssertionError as e:
        print(f"Caught Expected Error: {e}")
'''

'''--------------------TEST NEW BOARD PRINT FUNCTION--------------------
    board = Board()
    FEN1 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    FEN2 = "rnbqkbnr/pp1ppppp/8/2p1P3/8/8/PPPP1PPP/RNBQKBNR b KQkq d6 0 2"
    FEN3 = "rnbqkbnr/pp1ppppp/8/2p1P3/5N2/8/PPPP1PPP/RNBQKB1R b KQkq - 1 2"
    #wiki positions to check and verify the working
    print("--- Testing FEN 1 (After 1. e4) ---")
    board.parse_fen(FEN1)
    board.print_board()
    # Expected: Side b, EP 45 (E3), Castle KQkq

    print("\n--- Testing FEN 2 (After 1. e4 c5 2. e5) ---")
    board.parse_fen(FEN2)
    board.print_board()
    # Expected: Side b, EP 73 (D6), Castle KQkq

    print("\n--- Testing FEN 3 (After 1. e4 c5 2. e5 Nf3) ---")
    board.parse_fen(FEN3)
    board.print_board()
'''

'''-------------- TEST FEN ALL CASES-----------------------------------
    board = Board()
    
    # Test 1: Standard Start
    print("Test 1: Starting Position")
    board.parse_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    assert board.side == Side.WHITE
    assert board.pce_num[Pieces.wP] == 8
    print("[PASS]")

    # Test 2: Mid-game with En Passant and Black to move
    # This FEN has a pawn on e5, and an en passant target on d6
    print("\nTest 2: Mid-game + En Passant")
    board.parse_fen("rnbqkbnr/pp1ppppp/8/2p1P3/8/8/PPPP1PPP/RNBQKBNR b KQkq d6 0 3")
    assert board.side == Side.BLACK
    assert board.en_passant == Square.D6
    # Square D6 is rank 6, file 4 (0-indexed) -> FR2SQ(3, 5)
    print(f"En Passant Square: {board.en_passant} (D6)")
    print("[PASS]")

    # Test 3: Endgame (Few pieces, no castling)
    print("\nTest 3: Endgame (No Castling)")
    board.parse_fen("8/k7/8/8/8/8/7P/K7 w - - 0 1")
    board.print_board()
    assert board.castle_perm == 0
    assert board.pce_num[Pieces.wK] == 1
    assert board.pce_num[Pieces.bK] == 1
    assert board.big_pce[Side.WHITE] == 1 # Just the King
    print("[PASS]")

    print("\n[ALL FEN TESTS PASSED]")
'''


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


# def show_attacked_squares(board, side):
#     print(f"\nSquares Attacked by {'White' if side == Side.WHITE else 'Black'}:")
#     # We loop from Rank 8 down to Rank 1
#     for rank in range(Ranks.RANK_8, Ranks.RANK_1 - 1, -1):
#         line = f"{rank + 1}  "
#         for file in range(File.FILE_1, File.FILE_8 + 1):
#             sq = FR2SQ(file, rank)
#             # Call the method we added to the Board class
#             if board.is_sq_attacked(sq, side):
#                 line += "X "
#             else:
#                 line += ". "
#         print(line)
#     print("   a b c d e f g h")