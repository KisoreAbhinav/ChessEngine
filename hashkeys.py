import random
from defs import BOARD_SQ_NUM

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

    final_key = 0
    
    # 1. Pieces on squares
    for sq in range(BOARD_SQ_NUM):
        piece = board.pieces[sq]
        if piece != 99 and piece != 0: # Not NO_SQ or EMPTY
            final_key ^= PieceKeys[piece][sq]
            
    # 2. Side to move
    if board.side == 0: # WHITE
        final_key ^= SideKey
        
    # 3. En Passant
    if board.en_passant != 99: # NO_SQ
        # We use EMPTY piece key to hash the EP square
        final_key ^= PieceKeys[0][board.en_passant]
        
    # 4. Castling
    final_key ^= CastleKeys[board.castle_perm]
    
    return final_key