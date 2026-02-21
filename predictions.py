from defs import (
    Side,
    Pieces,
    Square,
    FilesBoard,
    RanksBoard,
    FROMSQ,
    TOSQ,
    CAPTURED,
    PROMOTED,
    MFLAG_CA,
    MFLAG_EP,
    PieceVal,
    PieceCol,
    FR2SQ,
    File,
    Ranks,
    SqOnBoard,
)
from make_mov import MakeMove, TakeMove
from move_gen import GenerateAllMoves, MoveList
from move_io import PrMove


KI_DIR = [-1, -10, 1, 10, -9, -11, 11, 9]
KN_DIR = [-8, -19, -21, -12, 8, 19, 21, 12]
RK_DIR = [-1, -10, 1, 10]
BI_DIR = [-9, -11, 11, 9]


SIDE_NAME = {
    Side.WHITE: "White",
    Side.BLACK: "Black",
}


PIECE_NAME = {
    Pieces.wP: "pawn",
    Pieces.wN: "knight",
    Pieces.wB: "bishop",
    Pieces.wR: "rook",
    Pieces.wQ: "queen",
    Pieces.wK: "king",
    Pieces.bP: "pawn",
    Pieces.bN: "knight",
    Pieces.bB: "bishop",
    Pieces.bR: "rook",
    Pieces.bQ: "queen",
    Pieces.bK: "king",
}


SIDE_PIECES = {
    Side.WHITE: [Pieces.wP, Pieces.wN, Pieces.wB, Pieces.wR, Pieces.wQ, Pieces.wK],
    Side.BLACK: [Pieces.bP, Pieces.bN, Pieces.bB, Pieces.bR, Pieces.bQ, Pieces.bK],
}


def _sq_to_alg(sq):
    return f"{chr(ord('a') + FilesBoard[sq])}{RanksBoard[sq] + 1}"


def _is_center_square(sq):
    return FilesBoard[sq] in (2, 3, 4, 5) and RanksBoard[sq] in (2, 3, 4, 5)


def _attacked_squares_for_piece(board, sq, piece):
    out = []
    side = PieceCol[piece]

    if piece in (Pieces.wP, Pieces.bP):
        offs = (9, 11) if side == Side.WHITE else (-9, -11)
        for off in offs:
            t = sq + off
            if SqOnBoard(t):
                out.append(t)
        return out

    if piece in (Pieces.wN, Pieces.bN):
        for d in KN_DIR:
            t = sq + d
            if not SqOnBoard(t):
                continue
            p = board.pieces[t]
            if p == Pieces.EMPTY or PieceCol[p] != side:
                out.append(t)
        return out

    if piece in (Pieces.wK, Pieces.bK):
        for d in KI_DIR:
            t = sq + d
            if not SqOnBoard(t):
                continue
            p = board.pieces[t]
            if p == Pieces.EMPTY or PieceCol[p] != side:
                out.append(t)
        return out

    if piece in (Pieces.wB, Pieces.bB):
        dirs = BI_DIR
    elif piece in (Pieces.wR, Pieces.bR):
        dirs = RK_DIR
    else:
        dirs = BI_DIR + RK_DIR

    for d in dirs:
        t = sq + d
        while SqOnBoard(t):
            p = board.pieces[t]
            if p == Pieces.EMPTY:
                out.append(t)
                t += d
                continue
            if PieceCol[p] != side:
                out.append(t)
            break
    return out


def _mobility_for_types(board, side, piece_types):
    total = 0
    for pce in piece_types:
        for i in range(board.pce_num[pce]):
            sq = board.p_list[pce][i]
            if sq == Square.NO_SQ:
                continue
            total += len(_attacked_squares_for_piece(board, sq, pce))
    return total


def _king_ring_pressure(board, attacker_side):
    enemy_king = board.king_sq[attacker_side ^ 1]
    ring = [enemy_king]
    for d in KI_DIR:
        t = enemy_king + d
        if SqOnBoard(t):
            ring.append(t)
    attacked = [sq for sq in ring if board.is_sq_attacked(sq, attacker_side)]
    return len(attacked), attacked, enemy_king


def _open_file_for_rook(board, rook_sq):
    f = FilesBoard[rook_sq]
    for r in range(Ranks.RANK_1, Ranks.RANK_8 + 1):
        sq = FR2SQ(f, r)
        p = board.pieces[sq]
        if p in (Pieces.wP, Pieces.bP):
            return False
    return True


def _unprotected_target_ideas(board, side):
    enemy = side ^ 1
    enemy_types = SIDE_PIECES[enemy]
    ideas = []
    for pce in enemy_types:
        if pce in (Pieces.wK, Pieces.bK):
            continue
        for i in range(board.pce_num[pce]):
            sq = board.p_list[pce][i]
            if sq == Square.NO_SQ:
                continue
            if not board.is_sq_attacked(sq, side):
                continue
            defended = board.is_sq_attacked(sq, enemy)
            loose_bonus = 90 if not defended else 0
            score = PieceVal[pce] + loose_bonus
            label = PIECE_NAME[pce]
            if defended:
                text = f"Pressure on {SIDE_NAME[enemy]} {label} at {_sq_to_alg(sq)}."
            else:
                text = f"Loose {SIDE_NAME[enemy]} {label} at {_sq_to_alg(sq)} can be targeted."
            ideas.append(
                {
                    "id": f"target:{sq}",
                    "text": text,
                    "score": score,
                }
            )
    return ideas


def _knight_fork_ideas(board, side):
    knight = Pieces.wN if side == Side.WHITE else Pieces.bN
    enemy = side ^ 1
    ideas = []
    for i in range(board.pce_num[knight]):
        sq = board.p_list[knight][i]
        if sq == Square.NO_SQ:
            continue
        attacked = _attacked_squares_for_piece(board, sq, knight)
        major_targets = []
        for t in attacked:
            p = board.pieces[t]
            if p == Pieces.EMPTY or PieceCol[p] != enemy:
                continue
            if PieceVal[p] >= 325:
                major_targets.append(t)
        if len(major_targets) >= 2:
            target_txt = ", ".join(_sq_to_alg(x) for x in major_targets[:3])
            ideas.append(
                {
                    "id": f"fork:{sq}",
                    "text": f"Knight at {_sq_to_alg(sq)} has fork ideas on {target_txt}.",
                    "score": 330 + 20 * len(major_targets),
                }
            )
    return ideas


def _rook_open_file_ideas(board, side):
    rook = Pieces.wR if side == Side.WHITE else Pieces.bR
    ideas = []
    for i in range(board.pce_num[rook]):
        sq = board.p_list[rook][i]
        if sq == Square.NO_SQ:
            continue
        if _open_file_for_rook(board, sq):
            ideas.append(
                {
                    "id": f"rook_open:{sq}",
                    "text": f"Rook at {_sq_to_alg(sq)} has an open file for pressure.",
                    "score": 260,
                }
            )
    return ideas


def build_ideas_snapshot(board, side, limit=5):
    ideas = []
    pressure, attacked_ring, enemy_king = _king_ring_pressure(board, side)
    if pressure >= 1:
        squares_txt = ", ".join(_sq_to_alg(sq) for sq in attacked_ring[:4])
        ideas.append(
            {
                "id": f"king_pressure:{enemy_king}",
                "text": f"King pressure on {_sq_to_alg(enemy_king)} (attacks on {squares_txt}).",
                "score": 250 + 30 * pressure,
            }
        )

    ideas.extend(_unprotected_target_ideas(board, side))
    ideas.extend(_knight_fork_ideas(board, side))
    ideas.extend(_rook_open_file_ideas(board, side))

    # Fallback strategic ideas for quiet positions.
    center_sqs = [
        FR2SQ(File.FILE_4, Ranks.RANK_4),
        FR2SQ(File.FILE_5, Ranks.RANK_4),
        FR2SQ(File.FILE_4, Ranks.RANK_5),
        FR2SQ(File.FILE_5, Ranks.RANK_5),
    ]
    center_attacks = [sq for sq in center_sqs if board.is_sq_attacked(sq, side)]
    if center_attacks:
        c_txt = ", ".join(_sq_to_alg(sq) for sq in center_attacks)
        ideas.append(
            {
                "id": f"center_control:{side}",
                "text": f"Center control available on {c_txt}.",
                "score": 180 + 15 * len(center_attacks),
            }
        )

    bishop = Pieces.wB if side == Side.WHITE else Pieces.bB
    knight = Pieces.wN if side == Side.WHITE else Pieces.bN
    dev_mob = _mobility_for_types(board, side, [bishop, knight])
    if dev_mob > 0:
        ideas.append(
            {
                "id": f"development:{side}",
                "text": "Piece development can increase coordination and tactical chances.",
                "score": 140 + min(80, dev_mob),
            }
        )

    # De-dup by id, keep best score.
    best = {}
    for idea in ideas:
        prev = best.get(idea["id"])
        if prev is None or idea["score"] > prev["score"]:
            best[idea["id"]] = idea

    ordered = sorted(best.values(), key=lambda x: x["score"], reverse=True)
    return ordered[:limit]


def compare_ideas(previous_ideas, current_ideas):
    if not previous_ideas:
        return [], []
    prev_map = {x["id"]: x for x in previous_ideas}
    cur_map = {x["id"]: x for x in current_ideas}
    countered = [prev_map[k]["text"] for k in prev_map if k not in cur_map]
    remaining = [prev_map[k]["text"] for k in prev_map if k in cur_map]
    return countered, remaining


def _move_effect_lines(
    board,
    move,
    actor_side,
    moved_piece,
    before_mob,
    after_mob,
    before_pressure,
    after_pressure,
):
    lines = []
    to_sq = TOSQ(move)
    piece_name = PIECE_NAME.get(moved_piece, "piece")

    if CAPTURED(move) != Pieces.EMPTY or (move & MFLAG_EP):
        lines.append(f"{piece_name.capitalize()} captures to {_sq_to_alg(to_sq)} and shifts material balance.")
    elif move & MFLAG_CA:
        lines.append("Castling improves king safety and rook activity.")
    elif moved_piece in (Pieces.wP, Pieces.bP):
        lines.append(f"Pawn push to {_sq_to_alg(to_sq)} changes structure and space.")
    else:
        lines.append(f"{piece_name.capitalize()} repositions to {_sq_to_alg(to_sq)}.")

    if PROMOTED(move) != Pieces.EMPTY:
        promo = PIECE_NAME[PROMOTED(move)]
        lines.append(f"Promotion creates a new {promo} and immediate tactical chances.")

    if _is_center_square(to_sq):
        lines.append(f"Move contests central square {_sq_to_alg(to_sq)}.")

    if after_mob["bishop"] > before_mob["bishop"]:
        lines.append("Bishop lines opened up.")
    if after_mob["rook"] > before_mob["rook"]:
        lines.append("Rook lanes became more active.")
    if after_mob["queen"] > before_mob["queen"]:
        lines.append("Queen mobility increased.")

    if after_pressure > before_pressure:
        lines.append("King-side pressure increased.")
    elif after_pressure < before_pressure:
        lines.append("Pressure eased; move is more consolidating.")

    return lines[:4]


def build_move_feedback(board, move, actor_side, actor_label, previous_enemy_ideas=None):
    if board.side != actor_side:
        return {
            "actor": actor_label,
            "headline": "Feedback unavailable (side mismatch).",
            "highlights": [],
            "own_ideas": [],
            "enemy_ideas": [],
            "countered_enemy_ideas": [],
            "remaining_enemy_ideas": [],
        }

    bishop = Pieces.wB if actor_side == Side.WHITE else Pieces.bB
    rook = Pieces.wR if actor_side == Side.WHITE else Pieces.bR
    queen = Pieces.wQ if actor_side == Side.WHITE else Pieces.bQ

    before_mob = {
        "bishop": _mobility_for_types(board, actor_side, [bishop]),
        "rook": _mobility_for_types(board, actor_side, [rook]),
        "queen": _mobility_for_types(board, actor_side, [queen]),
    }
    before_pressure, _, _ = _king_ring_pressure(board, actor_side)
    moved_piece_before = board.pieces[FROMSQ(move)]

    if not MakeMove(board, move):
        return {
            "actor": actor_label,
            "headline": "Illegal move; no feedback.",
            "highlights": [],
            "own_ideas": [],
            "enemy_ideas": [],
            "countered_enemy_ideas": [],
            "remaining_enemy_ideas": [],
        }

    after_mob = {
        "bishop": _mobility_for_types(board, actor_side, [bishop]),
        "rook": _mobility_for_types(board, actor_side, [rook]),
        "queen": _mobility_for_types(board, actor_side, [queen]),
    }
    after_pressure, _, enemy_king_sq = _king_ring_pressure(board, actor_side)
    gave_check = board.is_sq_attacked(board.king_sq[board.side], actor_side)

    own_ideas = build_ideas_snapshot(board, actor_side, limit=5)
    enemy_ideas = build_ideas_snapshot(board, actor_side ^ 1, limit=5)
    countered_enemy_ideas, remaining_enemy_ideas = compare_ideas(previous_enemy_ideas or [], enemy_ideas)

    lines = _move_effect_lines(
        board,
        move,
        actor_side,
        moved_piece_before,
        before_mob,
        after_mob,
        before_pressure,
        after_pressure,
    )
    if gave_check:
        lines.insert(0, f"Check on {_sq_to_alg(enemy_king_sq)} forces a response.")

    TakeMove(board)

    from_sq = _sq_to_alg(FROMSQ(move))
    to_sq = _sq_to_alg(TOSQ(move))
    headline = f"{actor_label} played {PrMove(move)} ({from_sq}->{to_sq})."

    return {
        "actor": actor_label,
        "headline": headline,
        "highlights": lines[:5],
        "own_ideas": own_ideas,
        "enemy_ideas": enemy_ideas,
        "countered_enemy_ideas": countered_enemy_ideas[:5],
        "remaining_enemy_ideas": remaining_enemy_ideas[:5],
    }
