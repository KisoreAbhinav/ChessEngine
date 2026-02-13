# hydra.py
from defs import *

def main():
    AllInit()

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