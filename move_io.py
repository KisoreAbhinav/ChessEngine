from defs import FilesBoard, RanksBoard, FROMSQ, TOSQ, PROMOTED, Pieces

def PrSq(sq):
    f = FilesBoard[sq]
    r = RanksBoard[sq]
    return f"{chr(ord('a') + f)}{r + 1}"
# extracts data from the notations

def PrMove(move):
    # Converts a packed move integer to a move string (e.g., 'e2e4' or 'a7a8q')
    ff = FilesBoard[FROMSQ(move)]
    rf = RanksBoard[FROMSQ(move)]
    ft = FilesBoard[TOSQ(move)]
    rt = RanksBoard[TOSQ(move)]
    
    # Basic move string: from_file + from_rank + to_file + to_rank
    move_str = f"{chr(ord('a') + ff)}{rf + 1}{chr(ord('a') + ft)}{rt + 1}"
    
    # Check and obtain promotions
    promoted = PROMOTED(move)
    if promoted != Pieces.EMPTY:
        pchar = 'q' # Fallback default to Queen
        # mapping the piece value to character in the move string
        # (wN=2, bN=8), (wB=3, bB=9), (wR=4, bR=10)
        # piece type regardless of color
        if promoted in [Pieces.wN, Pieces.bN]: pchar = 'n'
        elif promoted in [Pieces.wR, Pieces.bR]: pchar = 'r'
        elif promoted in [Pieces.wB, Pieces.bB]: pchar = 'b'
        move_str += pchar
        
    return move_str