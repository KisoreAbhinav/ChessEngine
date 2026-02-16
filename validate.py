from defs import *

def SqOnBoard(sq):
    # Checks if the square index is within the playable 64 squares 
    # (returns True if Sq120to64 doesn't have the 65/OFFBOARD marker)
    return Sq120to64[sq] != 65

def SideValid(side):
    return side == Side.WHITE or side == Side.BLACK

def FileRankValid(fr):
    return 0 <= fr <= 7

def PieceValidEmpty(pce):
    return Pieces.EMPTY <= pce <= Pieces.bK

def PieceValid(pce):
    return Pieces.wP <= pce <= Pieces.bK