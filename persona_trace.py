import math
import random

from defs import (
    CAPTURED,
    FROMSQ,
    MFLAG_CA,
    MFLAG_EP,
    PROMOTED,
    Ranks,
    RanksBoard,
    Side,
    Pieces,
    TOSQ,
)
from evaluate import EvalPosition
from make_mov import MakeMove, TakeMove
from move_gen import GenerateAllMoves, MoveList


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _cp_to_unit(cp, scale=200.0):
    return (math.tanh(cp / scale) + 1.0) * 0.5


def infer_target_elo(personality):
    explicit_elo = int(getattr(personality, "target_elo", 0) or 0)
    if explicit_elo > 0:
        return int(_clamp(explicit_elo, 400, 2600))

    accuracy = int(getattr(personality, "accuracy", 50))
    tenacity = int(getattr(personality, "tenacity", 50))
    endgames = int(getattr(personality, "endgames", 50))
    inferred = 500 + (accuracy * 13) + (tenacity * 5) + (endgames * 4)
    return int(_clamp(inferred, 400, 2600))


def _allowed_loss_cp(target_elo, accuracy, endgames, in_endgame):
    elo_n = _clamp((target_elo - 400) / 2200.0, 0.0, 1.0)
    acc_n = _clamp(accuracy / 100.0, 0.0, 1.0)
    end_n = _clamp(endgames / 100.0, 0.0, 1.0)

    base = 260.0 - (165.0 * elo_n) - (95.0 * acc_n)
    if in_endgame:
        base -= 35.0 * end_n
    return _clamp(base, 18.0, 260.0)


def _is_endgame_position(board):
    white_heavy = board.pce_num[Pieces.wR] + board.pce_num[Pieces.wQ]
    black_heavy = board.pce_num[Pieces.bR] + board.pce_num[Pieces.bQ]
    white_minor = board.pce_num[Pieces.wN] + board.pce_num[Pieces.wB]
    black_minor = board.pce_num[Pieces.bN] + board.pce_num[Pieces.bB]
    total_non_pawn = white_heavy + black_heavy + white_minor + black_minor
    return total_non_pawn <= 6


def _development_signal(side_to_move, mover_piece, from_sq, to_sq):
    score = 0.0

    from_rank = (from_sq // 10) - 2
    if side_to_move == Side.WHITE:
        if mover_piece in (Pieces.wN, Pieces.wB) and from_rank == Ranks.RANK_1:
            score += 0.65
    else:
        if mover_piece in (Pieces.bN, Pieces.bB) and from_rank == Ranks.RANK_8:
            score += 0.65

    if to_sq in (44, 45, 54, 55):
        score += 0.35

    return _clamp(score, 0.0, 1.0)


def _collect_move_trace(board, move):
    side_to_move = board.side
    from_sq = FROMSQ(move)
    to_sq = TOSQ(move)

    mover_piece = board.pieces[from_sq]
    is_capture = CAPTURED(move) != Pieces.EMPTY or (move & MFLAG_EP) != 0
    is_promotion = PROMOTED(move) != Pieces.EMPTY
    is_castle = (move & MFLAG_CA) != 0

    if not MakeMove(board, move):
        return None

    # EvalPosition is side-to-move relative; negate to get original mover perspective.
    after_cp = -EvalPosition(board)
    gives_check = board.is_sq_attacked(board.king_sq[board.side], board.side ^ 1)

    reply_list = MoveList()
    GenerateAllMoves(board, reply_list)

    reply_count = 0
    reply_capture_count = 0
    reply_min_cp = 30000.0
    reply_max_cp = -30000.0
    reply_sum = 0.0
    reply_sum_sq = 0.0

    for i in range(reply_list.count):
        reply_move = reply_list.moves[i].move
        reply_is_capture = CAPTURED(reply_move) != Pieces.EMPTY or (reply_move & MFLAG_EP) != 0

        if not MakeMove(board, reply_move):
            continue

        # After opponent reply, side to move is the original side; EvalPosition matches original perspective.
        cp = float(EvalPosition(board))
        TakeMove(board)

        reply_count += 1
        if reply_is_capture:
            reply_capture_count += 1
        reply_min_cp = min(reply_min_cp, cp)
        reply_max_cp = max(reply_max_cp, cp)
        reply_sum += cp
        reply_sum_sq += cp * cp

    if reply_count == 0:
        if gives_check:
            reply_min_cp = 29000.0
            reply_max_cp = 29000.0
            reply_mean_cp = 29000.0
        else:
            reply_min_cp = 0.0
            reply_max_cp = 0.0
            reply_mean_cp = 0.0
        reply_vol_cp = 0.0
    else:
        reply_mean_cp = reply_sum / reply_count
        variance = max(0.0, (reply_sum_sq / reply_count) - (reply_mean_cp * reply_mean_cp))
        reply_vol_cp = math.sqrt(variance)

    TakeMove(board)

    return {
        "move": move,
        "after_cp": after_cp,
        "reply_min_cp": reply_min_cp,
        "reply_mean_cp": reply_mean_cp,
        "reply_max_cp": reply_max_cp,
        "reply_vol_cp": reply_vol_cp,
        "reply_count": reply_count,
        "reply_capture_ratio": (reply_capture_count / reply_count) if reply_count > 0 else 0.0,
        "initiative_cp": after_cp - reply_mean_cp,
        "is_capture": 1.0 if is_capture else 0.0,
        "is_promotion": 1.0 if is_promotion else 0.0,
        "is_castle": 1.0 if is_castle else 0.0,
        "gives_check": 1.0 if gives_check else 0.0,
        "development": _development_signal(side_to_move, mover_piece, from_sq, to_sq),
        "king_move": 1.0 if mover_piece in (Pieces.wK, Pieces.bK) else 0.0,
    }


def _utility_from_trace(trace, personality, target_elo, reference_cp, in_endgame):
    playstyle = _clamp(float(getattr(personality, "playstyle", 50)) / 100.0, 0.0, 1.0)
    tenacity = _clamp(float(getattr(personality, "tenacity", 50)) / 100.0, 0.0, 1.0)
    accuracy = _clamp(float(getattr(personality, "accuracy", 50)) / 100.0, 0.0, 1.0)
    temperament = _clamp(float(getattr(personality, "temperament", 50)) / 100.0, 0.0, 1.0)
    endgames = _clamp(float(getattr(personality, "endgames", 50)) / 100.0, 0.0, 1.0)

    cp_loss = max(0.0, float(reference_cp) - float(trace["reply_min_cp"]))
    allowed_loss = _allowed_loss_cp(target_elo, accuracy * 100.0, endgames * 100.0, in_endgame)
    quality = math.exp(-cp_loss / max(12.0, allowed_loss))

    vol_norm = _clamp(trace["reply_vol_cp"] / 260.0, 0.0, 1.0)
    initiative_norm = _cp_to_unit(trace["initiative_cp"], 220.0)
    safety_norm = _cp_to_unit(trace["reply_min_cp"] - reference_cp + 90.0, 180.0)

    explosive = _clamp(
        (0.35 * trace["is_capture"])
        + (0.25 * trace["gives_check"])
        + (0.30 * trace["is_promotion"])
        + (0.25 * vol_norm)
        + (0.15 * initiative_norm),
        0.0,
        1.0,
    )
    foundational = _clamp(
        (0.60 * trace["development"])
        + (0.25 * (1.0 - vol_norm))
        + (0.15 * (1.0 - trace["is_capture"])),
        0.0,
        1.0,
    )
    resilience = _clamp((0.55 * (1.0 - vol_norm)) + (0.45 * safety_norm), 0.0, 1.0)
    reckless = _clamp(
        (0.55 * vol_norm) + (0.25 * trace["is_capture"]) + (0.20 * trace["is_promotion"]),
        0.0,
        1.0,
    )
    precision = _clamp((0.55 * (1.0 - vol_norm)) + (0.45 * quality), 0.0, 1.0)

    play_match = ((1.0 - playstyle) * foundational) + (playstyle * explosive)
    tenacity_match = 1.0 - abs(resilience - tenacity)
    temper_match = 1.0 - abs(reckless - temperament)
    endgame_match = 1.0 - abs(precision - endgames)

    elo_norm = _clamp((target_elo - 400) / 2200.0, 0.0, 1.0)
    quality_weight = 2.2 + (2.4 * elo_norm) + (1.6 * accuracy)
    style_weight = 0.9 + (0.7 * (1.0 - accuracy))

    utility = quality_weight * quality
    utility += style_weight * (
        (0.9 * play_match)
        + (0.8 * tenacity_match)
        + (0.7 * temper_match)
        + ((1.0 if in_endgame else 0.3) * endgame_match)
    )

    if cp_loss > allowed_loss:
        utility -= 2.8 * ((cp_loss - allowed_loss) / max(20.0, allowed_loss))

    if target_elo >= 2100 and cp_loss > (allowed_loss * 1.2):
        utility -= 4.0

    if in_endgame and trace["king_move"] > 0.0:
        utility += 0.25 * endgames

    return utility, cp_loss, allowed_loss


def choose_trace_personality_move(board, depth, movetime_ms, personality, baseline_result):
    _ = depth
    _ = movetime_ms

    best_move = int(baseline_result.get("best_move", 0) or 0)
    best_score = float(baseline_result.get("best_score", EvalPosition(board)))

    target_elo = infer_target_elo(personality)
    in_endgame = _is_endgame_position(board)

    move_list = MoveList()
    GenerateAllMoves(board, move_list)

    traces = []
    for i in range(move_list.count):
        trace = _collect_move_trace(board, move_list.moves[i].move)
        if trace is not None:
            traces.append(trace)

    if not traces:
        return best_move, {
            "best_move": best_move,
            "best_score": int(best_score),
            "effective_accuracy": int(getattr(personality, "accuracy", 50)),
            "book": bool(baseline_result.get("book", False)),
            "target_elo": target_elo,
            "fallback": True,
        }

    scored = []
    for trace in traces:
        utility, cp_loss, allowed_loss = _utility_from_trace(
            trace, personality, target_elo, best_score, in_endgame
        )
        if trace["move"] == best_move:
            utility += 0.9 + (float(getattr(personality, "accuracy", 50)) / 100.0) * 0.6
        scored.append(
            {
                "move": trace["move"],
                "utility": utility,
                "cp_loss": cp_loss,
                "allowed_loss": allowed_loss,
                "trace": trace,
            }
        )

    scored.sort(key=lambda x: x["utility"], reverse=True)

    accuracy = _clamp(float(getattr(personality, "accuracy", 50)) / 100.0, 0.0, 1.0)
    temperament = _clamp(float(getattr(personality, "temperament", 50)) / 100.0, 0.0, 1.0)
    endgames = _clamp(float(getattr(personality, "endgames", 50)) / 100.0, 0.0, 1.0)
    elo_norm = _clamp((target_elo - 400) / 2200.0, 0.0, 1.0)

    band = int(round(2 + (1.0 - accuracy) * 5 + (1.0 - elo_norm) * 4 + temperament * 2))
    band = int(_clamp(band, 1, min(10, len(scored))))
    candidates = scored[:band]

    temperature = 1.35 - (0.95 * accuracy) - (0.55 * elo_norm) + (0.45 * temperament)
    if in_endgame:
        temperature *= max(0.55, 1.15 - endgames)
    temperature = _clamp(temperature, 0.08, 1.8)

    if accuracy >= 0.95 and elo_norm >= 0.75 and temperament <= 0.35:
        chosen = candidates[0]
    else:
        max_u = max(c["utility"] for c in candidates)
        denom = max(0.05, temperature)
        weights = [math.exp((c["utility"] - max_u) / denom) for c in candidates]
        chosen = random.choices(candidates, weights=weights, k=1)[0]

    effective_accuracy = int(
        _clamp(100.0 * ((0.55 * accuracy) + (0.45 * elo_norm)), 0.0, 100.0)
    )
    if in_endgame:
        effective_accuracy = int((2 * effective_accuracy + int(endgames * 100)) / 3)

    top_debug = []
    for item in scored[:3]:
        top_debug.append(
            {
                "move": item["move"],
                "loss_cp": int(round(item["cp_loss"])),
                "utility": round(item["utility"], 2),
            }
        )

    return chosen["move"], {
        "best_move": best_move,
        "best_score": int(best_score),
        "effective_accuracy": effective_accuracy,
        "book": bool(baseline_result.get("book", False)),
        "target_elo": target_elo,
        "trace_temperature": round(temperature, 3),
        "trace_top": top_debug,
    }
