from defs import *

MAX_POS_MOVES = 256

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

def GenerateAllMoves(pos, list):
    list.count = 0


def AddWhitePawnCaptureMove(pos, from_sq, to_sq, cap_pce, move_list):

    # If the pawn is on Rank 7, it's moving to Rank 8
    if RanksBoard[from_sq] == Ranks.RANK_7:
        AddCaptureMove(pos, MOVE(from_sq, to_sq, cap_pce, Pieces.wQ, 0), move_list)
        AddCaptureMove(pos, MOVE(from_sq, to_sq, cap_pce, Pieces.wR, 0), move_list)
        AddCaptureMove(pos, MOVE(from_sq, to_sq, cap_pce, Pieces.wB, 0), move_list)
        AddCaptureMove(pos, MOVE(from_sq, to_sq, cap_pce, Pieces.wN, 0), move_list)
    else:
        # Normal capture, no promotion
        AddCaptureMove(pos, MOVE(from_sq, to_sq, cap_pce, Pieces.EMPTY, 0), move_list)

def AddWhitePawnMove(pos, from_sq, to_sq, move_list):

    if RanksBoard[from_sq] == Ranks.RANK_7:
        AddQuietMove(pos, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.wQ, 0), move_list)
        AddQuietMove(pos, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.wR, 0), move_list)
        AddQuietMove(pos, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.wB, 0), move_list)
        AddQuietMove(pos, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.wN, 0), move_list)
    else:
        # Normal move, no promotion
        AddQuietMove(pos, MOVE(from_sq, to_sq, Pieces.EMPTY, Pieces.EMPTY, 0), move_list)

def generate_white_pawn_moves(pos, move_list):
    for pce_num in range(pos.piece_num[Pieces.wP]):
        sq = pos.piece_list[Pieces.wP][pce_num]
        assert SqOnBoard(sq)
        
        # Forward Moves
        if pos.pieces[sq + 10] == Pieces.EMPTY:
            AddWhitePawnMove(pos, sq, sq + 10, move_list)
            if RanksBoard[sq] == Ranks.RANK_2 and pos.pieces[sq + 20] == Pieces.EMPTY:
                AddQuietMove(pos, MOVE(sq, sq + 20, Pieces.EMPTY, Pieces.EMPTY, PAWN_START_FLAG), move_list)