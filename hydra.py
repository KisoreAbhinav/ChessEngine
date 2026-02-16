# hydra.py
from defs import *

def main():
    AllInit()


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