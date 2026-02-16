# move_gen.py
from defs import *

MAX_POS_MOVES = 256


# The '0' at the end of each sequence acts as a terminator for the while loop
LoopSlidePiece = [ 
    Pieces.wB, Pieces.wR, Pieces.wQ, 0, 
    Pieces.bB, Pieces.bR, Pieces.bQ, 0 
]

LoopNonSlidePiece = [ 
    Pieces.wN, Pieces.wK, 0, 
    Pieces.bN, Pieces.bK, 0 
]

# These tell the engine where to start looking in the arrays above 
# based on the side: [WHITE (0), BLACK (1)]
LoopSlideIndex = [ 0, 4 ]
LoopNonSlideIndex = [ 0, 3 ]


class MoveList:
    def __init__(self):
        self.moves = [Move() for _ in range(MAX_POS_MOVES)]
        self.count = 0

def AddQuietMove(pos, move, list):
    list.moves[list.count].move = move
    list.moves[list.count].score = 0
    list.count += 1

def AddCaptureMove(pos, move, list):
    list.moves[list.count].move = move
    list.moves[list.count].score = 0
    list.count += 1

def AddEnPassantMove(pos, move, list):
    list.moves[list.count].move = move
    list.moves[list.count].score = 0
    list.count += 1

def AddWhitePawnCaptureMove(board, from_sq, to_sq, cap, move_list):
    if RanksBoard[from_sq] == Ranks.RANK_7:
        AddCaptureMove(board, MOVE(from_sq, to_sq, cap, Pieces.wQ, 0), move_list)
        AddCaptureMove(board, MOVE(from_sq, to_sq, cap, Pieces.wR, 0), move_list)
        AddCaptureMove(board, MOVE(from_sq, to_sq, cap, Pieces.wB, 0), move_list)
        AddCaptureMove(board, MOVE(from_sq, to_sq, cap, Pieces.wN, 0), move_list)
    else:
        AddCaptureMove(board, MOVE(from_sq, to_sq, cap, Pieces.EMPTY, 0), move_list)

# In move_gen.py
def AddWhitePawnMove(board, from_sq, to_sq, move_list):
    # Check if the pawn is on the 7th rank (ready to promote)
    if RanksBoard[from_sq] == Ranks.RANK_7:
        AddQuietMove(board, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.wQ, 0), move_list)
        AddQuietMove(board, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.wR, 0), move_list)
        AddQuietMove(board, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.wB, 0), move_list)
        AddQuietMove(board, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.wN, 0), move_list)
    else:
        # Standard move for pawns on any other rank
        AddQuietMove(board, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.EMPTY, 0), move_list)

def AddBlackPawnCaptureMove(board, from_sq, to_sq, cap, move_list):
    # Black promotes when moving FROM Rank 2 TO Rank 1
    if RanksBoard[from_sq] == Ranks.RANK_2:
        AddCaptureMove(board, MOVE(from_sq, to_sq, cap, Pieces.bQ, 0), move_list)
        AddCaptureMove(board, MOVE(from_sq, to_sq, cap, Pieces.bR, 0), move_list)
        AddCaptureMove(board, MOVE(from_sq, to_sq, cap, Pieces.bB, 0), move_list)
        AddCaptureMove(board, MOVE(from_sq, to_sq, cap, Pieces.bN, 0), move_list)
    else:
        AddCaptureMove(board, MOVE(from_sq, to_sq, cap, Pieces.EMPTY, 0), move_list)

def AddBlackPawnMove(board, from_sq, to_sq, move_list):
    if RanksBoard[from_sq] == Ranks.RANK_2:
        AddQuietMove(board, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.bQ, 0), move_list)
        AddQuietMove(board, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.bR, 0), move_list)
        AddQuietMove(board, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.bB, 0), move_list)
        AddQuietMove(board, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.bN, 0), move_list)
    else:
        AddQuietMove(board, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.EMPTY, 0), move_list)

def generate_white_pawn_moves(pos, move_list):
    # Loop through all white pawns using the piece list (p_list)
    for pce_num in range(pos.pce_num[Pieces.wP]):
        sq = pos.p_list[Pieces.wP][pce_num]
        assert SqOnBoard(sq)
        
        # 1. Forward Moves
        if pos.pieces[sq + 10] == Pieces.EMPTY:
            AddWhitePawnMove(pos, sq, sq + 10, move_list)
            # Double Push from Rank 2
            if RanksBoard[sq] == Ranks.RANK_2 and pos.pieces[sq + 20] == Pieces.EMPTY:
                AddQuietMove(pos, MOVE(sq, sq + 20, Pieces.EMPTY, Pieces.EMPTY, PAWN_START_FLAG), move_list)
        
        # 2. Diagonal Captures
        for off in [9, 11]:
            target_sq = sq + off
            if not SqOnBoard(target_sq):
                continue
            
            pce = pos.pieces[target_sq]
            # Check if square contains a black piece
            if pce != Pieces.EMPTY and PieceCol[pce] == Side.BLACK:
                AddWhitePawnCaptureMove(pos, sq, target_sq, pce, move_list)
            
            # 3. En Passant Check
            if pos.en_passant != Square.NO_SQ:
                if target_sq == pos.en_passant:
                    AddEnPassantMove(pos, MOVE(sq, target_sq, Pieces.EMPTY, Pieces.EMPTY, EP_FLAG), move_list)

def generate_black_pawn_moves(pos, move_list):
    for pce_num in range(pos.pce_num[Pieces.bP]):
        sq = pos.p_list[Pieces.bP][pce_num]
        
        # 1. Forward Move (-10)
        if pos.pieces[sq - 10] == Pieces.EMPTY:
            AddBlackPawnMove(pos, sq, sq - 10, move_list)
            # Double Push from Rank 7 (Black starts on Rank 7)
            if RanksBoard[sq] == Ranks.RANK_7 and pos.pieces[sq - 20] == Pieces.EMPTY:
                AddQuietMove(pos, MOVE(sq, sq - 20, Pieces.EMPTY, Pieces.EMPTY, PAWN_START_FLAG), move_list)
        
        # 2. Diagonal Captures (-9, -11)
        for off in [-9, -11]:
            target_sq = sq + off
            if not SqOnBoard(target_sq):
                continue
            
            pce = pos.pieces[target_sq]
            if pce != Pieces.EMPTY and PieceCol[pce] == Side.WHITE:
                AddBlackPawnCaptureMove(pos, sq, target_sq, pce, move_list)
            
            # 3. En Passant
            if pos.en_passant != Square.NO_SQ:
                if target_sq == pos.en_passant:
                    AddEnPassantMove(pos, MOVE(sq, target_sq, Pieces.EMPTY, Pieces.EMPTY, EP_FLAG), move_list)


def GenerateAllMoves(pos, move_list):
    move_list.count = 0
    side = pos.side

    # 1. Handle Pawns (Keep these separate as they are unique)
    if side == Side.WHITE:
        generate_white_pawn_moves(pos, move_list)
    else:
        generate_black_pawn_moves(pos, move_list)

    # 2. Loop through Sliding Pieces (Bishops, Rooks, Queens)
    pce_idx = LoopSlideIndex[side]
    pce = LoopSlidePiece[pce_idx]
    
    while pce != 0:
        for i in range(pos.pce_num[pce]):
            sq = pos.p_list[pce][i]
            # Actual sliding logic (e.g. Bishop rays) goes here in the next video
            # print(f"Generating slider moves for {pce} at {sq}")
            
        pce_idx += 1
        pce = LoopSlidePiece[pce_idx]

    # 3. Loop through Non-Sliding Pieces (Knights, Kings)
    pce_idx = LoopNonSlideIndex[side]
    pce = LoopNonSlidePiece[pce_idx]
    
    while pce != 0:
        for i in range(pos.pce_num[pce]):
            sq = pos.p_list[pce][i]
            
            # Loop through all possible directions for this piece type
            for index in range(NumDir[pce]):
                dir = PceDir[pce][index]
                target_sq = sq + dir
                
                if not SqOnBoard(target_sq):
                    continue
                
                target_pce = pos.pieces[target_sq]
                
                if target_pce != Pieces.EMPTY:
                    # If target square has an enemy piece, it's a capture
                    # Use XOR with 1 to get the opposite color (White 0 ^ 1 = Black 1)
                    if PieceCol[target_pce] == (side ^ 1):
                        AddCaptureMove(pos, MOVE(sq, target_sq, target_pce, Pieces.EMPTY, 0), move_list)
                else:
                    # If target square is empty, it's a quiet move
                    AddQuietMove(pos, MOVE(sq, target_sq, Pieces.EMPTY, Pieces.EMPTY, 0), move_list)
            
        pce_idx += 1
        pce = LoopNonSlidePiece[pce_idx]
    



