import defs

def SqOnBoard(sq):
    return defs.Sq120to64[sq] != 65

def SideValid(side):
    return side == defs.Side.WHITE or side == defs.Side.BLACK

def FileRankValid(fr):
    return 0 <= fr <= 7

def PieceValidEmpty(pce):
    return defs.Pieces.EMPTY <= pce <= defs.Pieces.bK

def PieceValid(pce):
    return defs.Pieces.wP <= pce <= defs.Pieces.bK
