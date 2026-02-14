# hydra.py
from defs import *

def main():
    AllInit()

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

if __name__ == "__main__":
    main()