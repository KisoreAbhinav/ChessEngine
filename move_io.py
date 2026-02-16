from defs import FilesBoard, RanksBoard, FROMSQ, TOSQ, PROMOTED, Pieces, FR2SQ, Side
from validate import FileRankValid
from move_gen import GenerateAllMoves, MoveList
from make_mov import MakeMove, TakeMove

NOMOVE = 0

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


def ParseMove(move_str, board):
    """
    Parse user/GUI coordinate move text (e.g. 'e2e4', 'b7a8r')
    into engine's internal move integer.
    Returns NOMOVE if input is invalid or move is illegal.
    """
    move_str = move_str.strip().lower()

    if len(move_str) < 4:
        return NOMOVE

    from_file = ord(move_str[0]) - ord('a')
    from_rank = ord(move_str[1]) - ord('1')
    to_file = ord(move_str[2]) - ord('a')
    to_rank = ord(move_str[3]) - ord('1')

    if not FileRankValid(from_file) or not FileRankValid(from_rank):
        return NOMOVE
    if not FileRankValid(to_file) or not FileRankValid(to_rank):
        return NOMOVE

    from_sq = FR2SQ(from_file, from_rank)
    to_sq = FR2SQ(to_file, to_rank)
    prom_char = move_str[4] if len(move_str) > 4 else None

    move_list = MoveList()
    GenerateAllMoves(board, move_list)

    for i in range(move_list.count):
        move = move_list.moves[i].move
        if FROMSQ(move) != from_sq or TOSQ(move) != to_sq:
            continue

        promoted = PROMOTED(move)
        if promoted != Pieces.EMPTY:
            if prom_char is None:
                continue

            if board.side == Side.WHITE:
                if prom_char == 'q' and promoted != Pieces.wQ:
                    continue
                if prom_char == 'r' and promoted != Pieces.wR:
                    continue
                if prom_char == 'b' and promoted != Pieces.wB:
                    continue
                if prom_char == 'n' and promoted != Pieces.wN:
                    continue
                if prom_char not in ("q", "r", "b", "n"):
                    continue
            else:
                if prom_char == 'q' and promoted != Pieces.bQ:
                    continue
                if prom_char == 'r' and promoted != Pieces.bR:
                    continue
                if prom_char == 'b' and promoted != Pieces.bB:
                    continue
                if prom_char == 'n' and promoted != Pieces.bN:
                    continue
                if prom_char not in ("q", "r", "b", "n"):
                    continue
        elif prom_char is not None:
            continue

        # Ensure returned move is legal in current position.
        if MakeMove(board, move):
            TakeMove(board)
            return move

    return NOMOVE
