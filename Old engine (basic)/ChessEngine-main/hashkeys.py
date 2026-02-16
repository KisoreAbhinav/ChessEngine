import random
from defs import *

# Arrays to hold random numbers
PieceKeys = [[0 for _ in range(BOARD_SQ_NUM)] for _ in range(13)]
SideKey = 0
CastleKeys = [0 for _ in range(16)]

def init_hash_keys():
    global SideKey
    random.seed(1070372)
    
    for i in range(13):
        for j in range(BOARD_SQ_NUM):
            PieceKeys[i][j] = random.getrandbits(64)
            
    SideKey = random.getrandbits(64)
    
    for i in range(16):
        CastleKeys[i] = random.getrandbits(64)


def generate_pos_key(board):
    """Return the Zobrist hash for the given board object."""
    final_key = 0

    # Pieces on squares
    for sq in range(BOARD_SQ_NUM):
        piece = board.pieces[sq]
        if piece != Square.NO_SQ and piece != Pieces.EMPTY:
            # Piece is an IntEnum value that indexes PieceKeys
            final_key ^= PieceKeys[piece][sq]

    # Side to move: XOR SideKey only if BLACK to move
    # (Side.BLACK == 1, Side.WHITE == 0)
    if board.side == Side.BLACK:
        final_key ^= SideKey

    # En Passant: use the EMPTY row's key for the EP square itself
    if board.en_passant != Square.NO_SQ:
        final_key ^= PieceKeys[Pieces.EMPTY][board.en_passant]

    # Castling permissions
    final_key ^= CastleKeys[board.castle_perm]

    return final_key