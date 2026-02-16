from defs import (
    Side,
    Pieces,
    MAX_GAME_MOVES,
    MAXDEPTH,
    PieceVal,
    FROMSQ,
    TOSQ,
    CAPTURED,
    MFLAG_EP,
    SearchInfo,
)
from move_gen import GenerateAllMoves, GenerateAllCaps, MoveList
from make_mov import MakeMove, TakeMove
from move_io import PrMove
from misc import GetTimeMs, ReadInput
from pvtable import ProbePvTable, StorePvMove, ClearPvTable, GetPvLine
from evaluate import EvalPosition

INF = 30000
MATE = 29000
MAX_PLY = MAXDEPTH


def _eval_for_side_to_move(board):
    return EvalPosition(board)


def _is_capture_move(move):
    return CAPTURED(move) != Pieces.EMPTY or (move & MFLAG_EP)


def CheckUp(info):
    if info.time_set and GetTimeMs() >= info.stop_time:
        info.stopped = True
    ReadInput(info)


def IsRepetition(board):
    assert 0 <= board.his_ply <= MAX_GAME_MOVES
    assert 0 <= board.fifty_move <= MAX_GAME_MOVES

    start = max(0, board.his_ply - board.fifty_move)
    assert 0 <= start <= board.his_ply

    for i in range(start, board.his_ply):
        assert 0 <= i < MAX_GAME_MOVES
        if board.history[i].pos_key == board.pos_key:
            return True
    return False


def _score_move(board, move, ply, pv_move, base_move_score):
    if move == pv_move:
        return 2_000_000

    if _is_capture_move(move):
        # Capture ordering: MVV-LVA (or EP score 105) plus capture band.
        return 1_000_000 + base_move_score

    if board.search_killers[0][ply] == move:
        return 900_000
    if board.search_killers[1][ply] == move:
        return 800_000

    piece = board.pieces[FROMSQ(move)]
    return board.search_history[piece][TOSQ(move)]


def _order_moves(board, move_list, ply, pv_move):
    for i in range(move_list.count):
        move = move_list.moves[i].move
        base_score = move_list.moves[i].score
        move_list.moves[i].score = _score_move(board, move, ply, pv_move, base_score)

def PickNextMove(move_num, move_list):
    best_num = move_num
    best_score = 0

    for index in range(move_num, move_list.count):
        if move_list.moves[index].score > best_score:
            best_score = move_list.moves[index].score
            best_num = index

    temp = move_list.moves[move_num]
    move_list.moves[move_num] = move_list.moves[best_num]
    move_list.moves[best_num] = temp


def ClearForSearch(board, info):
    ClearPvTable(board.pv_table)
    for i in range(2):
        for j in range(MAX_PLY):
            board.search_killers[i][j] = 0
    for i in range(13):
        for j in range(120):
            board.search_history[i][j] = 0

    board.ply = 0
    info.start_time = GetTimeMs()
    info.nodes = 0
    info.stopped = 0
    info.fh = 0.0
    info.fhf = 0.0


def MinMax(board, depth, maximizing_player):
    if depth == 0:
        return EvalPosition(board)

    move_list = MoveList()
    GenerateAllMoves(board, move_list)

    legal_moves = 0
    if maximizing_player:
        best_score = -INF
        for i in range(move_list.count):
            move = move_list.moves[i].move
            if not MakeMove(board, move):
                continue
            legal_moves += 1
            score = MinMax(board, depth - 1, False)
            TakeMove(board)
            if score > best_score:
                best_score = score
    else:
        best_score = INF
        for i in range(move_list.count):
            move = move_list.moves[i].move
            if not MakeMove(board, move):
                continue
            legal_moves += 1
            score = MinMax(board, depth - 1, True)
            TakeMove(board)
            if score < best_score:
                best_score = score

    if legal_moves == 0:
        return EvalPosition(board)

    return best_score


def NegaMax(board, depth, stats=None):
    if stats is not None:
        stats["nodes"] += 1

    if depth == 0:
        return _eval_for_side_to_move(board)

    move_list = MoveList()
    GenerateAllMoves(board, move_list)

    best_score = -INF
    legal_moves = 0

    for i in range(move_list.count):
        move = move_list.moves[i].move
        if not MakeMove(board, move):
            continue
        legal_moves += 1
        score = -NegaMax(board, depth - 1, stats)
        TakeMove(board)

        if score > best_score:
            best_score = score

    if legal_moves == 0:
        return _eval_for_side_to_move(board)

    return best_score


def Quiescence(alpha, beta, board, info):
    if (info.nodes & 2047) == 0:
        CheckUp(info)

    if info.stopped:
        return 0

    info.nodes += 1

    if board.ply > 0 and (IsRepetition(board) or board.fifty_move >= 100):
        return 0

    if board.ply >= MAX_PLY - 1:
        return EvalPosition(board)

    # Standing pat
    score = EvalPosition(board)
    if score >= beta:
        return beta
    if score > alpha:
        alpha = score

    move_list = MoveList()
    GenerateAllCaps(board, move_list)

    for move_num in range(move_list.count):
        PickNextMove(move_num, move_list)
        move = move_list.moves[move_num].move

        if not MakeMove(board, move):
            continue

        score = -Quiescence(-beta, -alpha, board, info)
        TakeMove(board)

        if info.stopped:
            return 0

        if score >= beta:
            info.fh += 1
            if move_num == 0:
                info.fhf += 1
            return beta

        if score > alpha:
            alpha = score

    return alpha


def AlphaBeta(alpha, beta, depth, board, info, do_null=1, ply=0):
    if (info.nodes & 2047) == 0:
        CheckUp(info)

    if info.stopped:
        return 0

    # Base case: switch to quiescence search to resolve tactical captures.
    if depth == 0:
        return Quiescence(alpha, beta, board, info)

    info.nodes += 1

    # Draw detection via repetition / 50-move rule.
    if ply > 0 and (IsRepetition(board) or board.fifty_move >= 100):
        return 0

    if ply >= MAX_PLY - 1:
        return _eval_for_side_to_move(board)

    move_list = MoveList()
    GenerateAllMoves(board, move_list)

    pv_move = ProbePvTable(board)
    _order_moves(board, move_list, ply, pv_move)

    legal_moves = 0
    old_alpha = alpha
    best_move = 0

    for move_num in range(move_list.count):
        PickNextMove(move_num, move_list)
        move = move_list.moves[move_num].move
        if not MakeMove(board, move):
            continue

        legal_moves += 1
        score = -AlphaBeta(-beta, -alpha, depth - 1, board, info, do_null, ply + 1)
        TakeMove(board)

        if info.stopped:
            return 0

        if score > alpha:
            if score >= beta:
                info.fh += 1
                if legal_moves == 1:
                    info.fhf += 1

                if not _is_capture_move(move):
                    board.search_killers[1][ply] = board.search_killers[0][ply]
                    board.search_killers[0][ply] = move
                return beta

            alpha = score
            best_move = move
            if not _is_capture_move(move):
                moved_piece = board.pieces[FROMSQ(move)]
                board.search_history[moved_piece][TOSQ(move)] += depth

    if legal_moves == 0:
        in_check = board.is_sq_attacked(board.king_sq[board.side], board.side ^ 1)
        if in_check:
            return -MATE + ply
        return 0

    if alpha != old_alpha and best_move != 0:
        StorePvMove(board, best_move)

    return alpha


def FindBestMoveMinMax(board, depth):
    move_list = MoveList()
    GenerateAllMoves(board, move_list)

    best_move = 0
    legal_moves = 0
    maximizing = board.side == Side.WHITE
    best_score = -INF if maximizing else INF

    for i in range(move_list.count):
        move = move_list.moves[i].move
        if not MakeMove(board, move):
            continue
        legal_moves += 1

        score = MinMax(board, depth - 1, not maximizing)
        TakeMove(board)

        if maximizing and score > best_score:
            best_score = score
            best_move = move
        elif not maximizing and score < best_score:
            best_score = score
            best_move = move

    move_str = PrMove(best_move) if best_move != 0 else "(none)"
    return best_move, move_str, best_score, legal_moves


def FindBestMoveNegaMax(board, depth):
    move, move_str, score, legal_moves, _ = FindBestMoveNegaMaxWithStats(board, depth)
    return move, move_str, score, legal_moves


def FindBestMoveNegaMaxWithStats(board, depth):
    move_list = MoveList()
    GenerateAllMoves(board, move_list)

    stats = {"nodes": 0}
    best_move = 0
    best_score = -INF
    legal_moves = 0

    for i in range(move_list.count):
        move = move_list.moves[i].move
        if not MakeMove(board, move):
            continue
        legal_moves += 1

        score = -NegaMax(board, depth - 1, stats)
        TakeMove(board)

        if score > best_score:
            best_score = score
            best_move = move

    move_str = PrMove(best_move) if best_move != 0 else "(none)"
    return best_move, move_str, best_score, legal_moves, stats


def FindBestMoveAlphaBeta(board, depth):
    info = SearchInfo()
    info.start_time = GetTimeMs()
    info.stop_time = 0
    info.time_set = 0
    info.stdin_enabled = 0
    ClearForSearch(board, info)
    score = AlphaBeta(-INF, INF, depth, board, info, 1, 0)
    pv_count = GetPvLine(depth, board)
    best_move = board.pv_array[0] if pv_count > 0 else 0

    move_list = MoveList()
    GenerateAllMoves(board, move_list)
    legal_root_moves = 0
    for i in range(move_list.count):
        if MakeMove(board, move_list.moves[i].move):
            legal_root_moves += 1
            TakeMove(board)

    stats = {
        "nodes": info.nodes,
        "cutoffs": info.fh,
        "first_cutoffs": info.fhf,
        "pv": [PrMove(board.pv_array[i]) for i in range(pv_count)],
    }
    move_str = PrMove(best_move) if best_move != 0 else "(none)"
    return best_move, move_str, score, legal_root_moves, stats


def IterativeDeepening(board, max_depth, time_limit_ms=0, stdin_enabled=True, verbose=True):
    info = SearchInfo()
    info.start_time = GetTimeMs()
    info.stop_time = info.start_time + time_limit_ms if time_limit_ms > 0 else 0
    info.time_set = 1 if time_limit_ms > 0 else 0
    info.stdin_enabled = 1 if stdin_enabled else 0
    ClearForSearch(board, info)

    best_move = 0
    best_score = -INF
    best_pv = []
    completed_depth = 0

    for depth in range(1, max_depth + 1):
        score = AlphaBeta(-INF, INF, depth, board, info, 1, 0)
        if info.stopped:
            break

        pv_count = GetPvLine(depth, board)
        pv_moves = [board.pv_array[i] for i in range(pv_count)]
        if pv_count > 0:
            best_move = board.pv_array[0]
            best_pv = pv_moves
        best_score = score
        completed_depth = depth

        if verbose:
            pv_str = " ".join(PrMove(m) for m in pv_moves)
            print(
                f"Depth {depth}: score={score} nodes={info.nodes} "
                f"cutoffs={info.fh} pv={pv_str}"
            )

    best_move_str = PrMove(best_move) if best_move != 0 else "(none)"
    result = {
        "best_move": best_move,
        "best_move_str": best_move_str,
        "best_score": best_score,
        "completed_depth": completed_depth,
        "nodes": info.nodes,
        "cutoffs": info.fh,
        "first_cutoffs": info.fhf,
        "stopped": info.stopped,
        "quit": info.quit,
        "pv": [PrMove(m) for m in best_pv],
    }
    return result


def SearchPosition(board, info):
    """
    Part 58 iterative deepening search entry-point.
    """
    max_depth = info.depth if info.depth > 0 else 1
    ClearForSearch(board, info)

    best_move = 0
    best_score = -INF
    best_pv = []

    for current_depth in range(1, max_depth + 1):
        best_score = AlphaBeta(-INF, INF, current_depth, board, info, 1, 0)
        if info.stopped:
            break

        pv_count = GetPvLine(current_depth, board)
        if pv_count > 0:
            best_move = board.pv_array[0]
            best_pv = [board.pv_array[i] for i in range(pv_count)]
        else:
            best_pv = []

        elapsed_ms = GetTimeMs() - info.start_time
        pv_str = " ".join(PrMove(board.pv_array[i]) for i in range(pv_count))
        print(
            f"info score cp {best_score} depth {current_depth} "
            f"nodes {info.nodes} time {elapsed_ms} pv {pv_str}".rstrip()
        )

    ordering = (info.fhf / info.fh) * 100.0 if info.fh > 0 else 0.0
    best_move_str = PrMove(best_move) if best_move != 0 else "0000"
    print(f"bestmove {best_move_str}")

    return {
        "best_move": best_move,
        "best_move_str": best_move_str,
        "best_score": best_score,
        "nodes": info.nodes,
        "fh": info.fh,
        "fhf": info.fhf,
        "ordering": ordering,
        "pv": [PrMove(m) for m in best_pv],
    }
