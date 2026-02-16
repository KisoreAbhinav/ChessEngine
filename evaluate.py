from defs import (
    Pieces,
    Side,
    Square,
    Sq120to64,
    FilesBoard,
    RanksBoard,
    PieceCol,
    KnDir,
    BiDir,
    RkDir,
    KiDir,
)


Mirror64 = [
    56, 57, 58, 59, 60, 61, 62, 63,
    48, 49, 50, 51, 52, 53, 54, 55,
    40, 41, 42, 43, 44, 45, 46, 47,
    32, 33, 34, 35, 36, 37, 38, 39,
    24, 25, 26, 27, 28, 29, 30, 31,
    16, 17, 18, 19, 20, 21, 22, 23,
    8, 9, 10, 11, 12, 13, 14, 15,
    0, 1, 2, 3, 4, 5, 6, 7,
]

PawnTable = [
    0, 0, 0, 0, 0, 0, 0, 0,
    10, 10, 0, -10, -10, 0, 10, 10,
    5, 0, 0, 5, 5, 0, 0, 5,
    0, 0, 10, 20, 20, 10, 0, 0,
    5, 5, 5, 10, 10, 5, 5, 5,
    10, 10, 10, 20, 20, 10, 10, 10,
    20, 20, 20, 30, 30, 20, 20, 20,
    0, 0, 0, 0, 0, 0, 0, 0,
]

KnightTable = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

BishopTable = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]

RookTable = [
    0, 0, 5, 10, 10, 5, 0, 0,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    25, 25, 25, 25, 25, 25, 25, 25,
    0, 0, 5, 10, 10, 5, 0, 0,
]

QueenTable = [
    -15, -10, -10, -5, -5, -10, -10, -15,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    -5, 0, 5, 5, 5, 5, 0, -5,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -15, -10, -10, -5, -5, -10, -10, -15,
]

KingTableMG = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20,
]

KingTableEG = [
    -50, -30, -20, -20, -20, -20, -30, -50,
    -30, -10, 0, 0, 0, 0, -10, -30,
    -20, 0, 10, 15, 15, 10, 0, -20,
    -20, 5, 15, 20, 20, 15, 5, -20,
    -20, 5, 15, 20, 20, 15, 5, -20,
    -20, 0, 10, 15, 15, 10, 0, -20,
    -30, -10, 0, 0, 0, 0, -10, -30,
    -50, -30, -20, -20, -20, -20, -30, -50,
]

PieceValue = {
    Pieces.wP: 100, Pieces.bP: 100,
    Pieces.wN: 320, Pieces.bN: 320,
    Pieces.wB: 330, Pieces.bB: 330,
    Pieces.wR: 500, Pieces.bR: 500,
    Pieces.wQ: 900, Pieces.bQ: 900,
}

PhaseValue = {
    Pieces.wN: 1, Pieces.bN: 1,
    Pieces.wB: 1, Pieces.bB: 1,
    Pieces.wR: 2, Pieces.bR: 2,
    Pieces.wQ: 4, Pieces.bQ: 4,
}

PASSED_PAWN_BONUS = [0, 5, 12, 22, 35, 55, 80, 0]

MOBILITY_MG = {
    Pieces.wN: 4, Pieces.bN: 4,
    Pieces.wB: 4, Pieces.bB: 4,
    Pieces.wR: 2, Pieces.bR: 2,
    Pieces.wQ: 1, Pieces.bQ: 1,
}
MOBILITY_EG = {
    Pieces.wN: 2, Pieces.bN: 2,
    Pieces.wB: 3, Pieces.bB: 3,
    Pieces.wR: 2, Pieces.bR: 2,
    Pieces.wQ: 1, Pieces.bQ: 1,
}


def _sq64_mirrored(piece, sq120):
    sq64 = Sq120to64[sq120]
    if piece >= Pieces.bP:
        return Mirror64[sq64]
    return sq64


def _piece_square(piece, sq120, mg=True):
    sq = _sq64_mirrored(piece, sq120)

    if piece in (Pieces.wP, Pieces.bP):
        return PawnTable[sq]
    if piece in (Pieces.wN, Pieces.bN):
        return KnightTable[sq]
    if piece in (Pieces.wB, Pieces.bB):
        return BishopTable[sq]
    if piece in (Pieces.wR, Pieces.bR):
        return RookTable[sq]
    if piece in (Pieces.wQ, Pieces.bQ):
        return QueenTable[sq]
    if piece in (Pieces.wK, Pieces.bK):
        return KingTableMG[sq] if mg else KingTableEG[sq]
    return 0


def _mobility_for_piece(pos, sq, piece):
    own = PieceCol[piece]
    pieces = pos.pieces
    mob = 0

    if piece in (Pieces.wN, Pieces.bN):
        for d in KnDir:
            t = sq + d
            p = pieces[t]
            if p != Square.NO_SQ and (p == Pieces.EMPTY or PieceCol[p] != own):
                mob += 1
        return mob

    if piece in (Pieces.wB, Pieces.bB, Pieces.wR, Pieces.bR, Pieces.wQ, Pieces.bQ):
        dirs = []
        if piece in (Pieces.wB, Pieces.bB, Pieces.wQ, Pieces.bQ):
            dirs += BiDir
        if piece in (Pieces.wR, Pieces.bR, Pieces.wQ, Pieces.bQ):
            dirs += RkDir
        for d in dirs:
            t = sq + d
            p = pieces[t]
            while p != Square.NO_SQ:
                if p == Pieces.EMPTY:
                    mob += 1
                else:
                    if PieceCol[p] != own:
                        mob += 1
                    break
                t += d
                p = pieces[t]
        return mob

    return 0


def _collect_pawns_by_file(pos):
    white_files = [[] for _ in range(8)]
    black_files = [[] for _ in range(8)]

    for i in range(pos.pce_num[Pieces.wP]):
        sq = pos.p_list[Pieces.wP][i]
        white_files[FilesBoard[sq]].append(RanksBoard[sq])

    for i in range(pos.pce_num[Pieces.bP]):
        sq = pos.p_list[Pieces.bP][i]
        black_files[FilesBoard[sq]].append(RanksBoard[sq])

    return white_files, black_files


def _pawn_structure_score(pos):
    mg = 0
    eg = 0
    white_files, black_files = _collect_pawns_by_file(pos)

    # White pawns
    for f in range(8):
        cnt = len(white_files[f])
        if cnt > 1:
            mg -= 12 * (cnt - 1)
            eg -= 10 * (cnt - 1)
        for r in white_files[f]:
            left = len(white_files[f - 1]) if f > 0 else 0
            right = len(white_files[f + 1]) if f < 7 else 0
            if left == 0 and right == 0:
                mg -= 10
                eg -= 8

            passed = True
            for ef in range(max(0, f - 1), min(7, f + 1) + 1):
                for er in black_files[ef]:
                    if er > r:
                        passed = False
                        break
                if not passed:
                    break
            if passed:
                bonus = PASSED_PAWN_BONUS[r]
                mg += bonus
                eg += bonus + 5

    # Black pawns
    for f in range(8):
        cnt = len(black_files[f])
        if cnt > 1:
            mg += 12 * (cnt - 1)
            eg += 10 * (cnt - 1)
        for r in black_files[f]:
            left = len(black_files[f - 1]) if f > 0 else 0
            right = len(black_files[f + 1]) if f < 7 else 0
            if left == 0 and right == 0:
                mg += 10
                eg += 8

            passed = True
            for ef in range(max(0, f - 1), min(7, f + 1) + 1):
                for er in white_files[ef]:
                    if er < r:
                        passed = False
                        break
                if not passed:
                    break
            if passed:
                bonus = PASSED_PAWN_BONUS[7 - r]
                mg -= bonus
                eg -= bonus + 5

    return mg, eg


def _king_shield_bonus(pos, side):
    king_sq = pos.king_sq[side]
    f = FilesBoard[king_sq]
    r = RanksBoard[king_sq]
    if f < 0 or f > 7 or r < 0 or r > 7:
        return 0

    if side == Side.WHITE:
        pawn = Pieces.wP
        rr1 = r + 1
        rr2 = r + 2
    else:
        pawn = Pieces.bP
        rr1 = r - 1
        rr2 = r - 2

    bonus = 0
    for ff in (f - 1, f, f + 1):
        if ff < 0 or ff > 7:
            continue
        for sq in range(21, 99):
            if FilesBoard[sq] == ff and RanksBoard[sq] == rr1 and pos.pieces[sq] == pawn:
                bonus += 12
            if FilesBoard[sq] == ff and RanksBoard[sq] == rr2 and pos.pieces[sq] == pawn:
                bonus += 6
    return bonus


def _king_attack_pressure(pos, king_side):
    enemy = Side.BLACK if king_side == Side.WHITE else Side.WHITE
    king_sq = pos.king_sq[king_side]
    zone = [king_sq]
    for d in KiDir:
        t = king_sq + d
        if pos.pieces[t] != Square.NO_SQ:
            zone.append(t)

    attacks = 0
    for sq in zone:
        if pos.is_sq_attacked(sq, enemy):
            attacks += 1
    return attacks


def _king_safety_score(pos):
    mg = 0
    eg = 0

    w_shield = _king_shield_bonus(pos, Side.WHITE)
    b_shield = _king_shield_bonus(pos, Side.BLACK)
    mg += w_shield - b_shield

    w_pressure = _king_attack_pressure(pos, Side.WHITE)
    b_pressure = _king_attack_pressure(pos, Side.BLACK)
    mg += (b_pressure - w_pressure) * 10
    eg += (b_pressure - w_pressure) * 3

    return mg, eg


def _phase(pos):
    phase = 0
    for p, v in PhaseValue.items():
        phase += pos.pce_num[p] * v
    if phase < 0:
        phase = 0
    if phase > 24:
        phase = 24
    return phase


def EvalPosition(pos):
    mg = 0
    eg = 0

    # Material + PST + mobility + bishop pair
    for piece in (
        Pieces.wP, Pieces.wN, Pieces.wB, Pieces.wR, Pieces.wQ, Pieces.wK,
        Pieces.bP, Pieces.bN, Pieces.bB, Pieces.bR, Pieces.bQ, Pieces.bK,
    ):
        sign = 1 if piece <= Pieces.wK else -1
        for i in range(pos.pce_num[piece]):
            sq = pos.p_list[piece][i]
            if piece in PieceValue:
                mg += sign * PieceValue[piece]
                eg += sign * PieceValue[piece]

            mg += sign * _piece_square(piece, sq, mg=True)
            eg += sign * _piece_square(piece, sq, mg=False)

            if piece in MOBILITY_MG:
                mob = _mobility_for_piece(pos, sq, piece)
                mg += sign * mob * MOBILITY_MG[piece]
                eg += sign * mob * MOBILITY_EG[piece]

    # Bishop pair
    if pos.pce_num[Pieces.wB] >= 2:
        mg += 35
        eg += 45
    if pos.pce_num[Pieces.bB] >= 2:
        mg -= 35
        eg -= 45

    p_mg, p_eg = _pawn_structure_score(pos)
    mg += p_mg
    eg += p_eg

    k_mg, k_eg = _king_safety_score(pos)
    mg += k_mg
    eg += k_eg

    # Tapered blend from midgame -> endgame
    phase = _phase(pos)
    score = (mg * phase + eg * (24 - phase)) // 24

    # Side-to-move perspective
    return score if pos.side == Side.WHITE else -score

