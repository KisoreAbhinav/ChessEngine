from defs import (
    AllInit,
    Board,
    Side,
    Pieces,
    FROMSQ,
    TOSQ,
    CAPTURED,
    PROMOTED,
    MFLAG_CA,
    MFLAG_EP,
    FilesBoard,
    RanksBoard,
)
from evaluate import EvalPosition
from book import get_book_move, load_opening_book
from make_mov import MakeMove, TakeMove
from move_gen import GenerateAllMoves, MoveList
from move_io import ParseMove, PrMove
from search import IterativeDeepening
from persona_trace import choose_trace_personality_move, infer_target_elo
from predictions import build_move_feedback
import math
import os
from datetime import datetime

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BOOK_ENABLED = True
LEARNER_GUIDE_ENABLED = False
BORDER_EQ = "=" * 66
BORDER_DASH = "-" * 66

# ---- Input Helpers ----
def ask_int(prompt, default_value, min_value=1):
    text = input(f"{prompt} [{default_value}]: ").strip()
    if not text:
        return default_value
    try:
        value = int(text)
        if value < min_value:
            return default_value
        return value
    except ValueError:
        return default_value

def ask_percent(prompt, default_value=50):
    return ask_int(prompt, default_value, 0)

def ask_yes_no(prompt, default_yes=True):
    default_tag = "Y/n" if default_yes else "y/N"
    raw = input(f"{prompt} [{default_tag}]: ").strip().lower()
    if not raw:
        return default_yes
    return raw in ("y", "yes", "1", "true")

def ask_elo(prompt, default_value=1600):
    value = ask_int(prompt, default_value, 400)
    return max(400, min(2600, value))

# ---- Display Helpers ----
def side_name(side):
    return "White" if side == Side.WHITE else "Black"

def cp_to_white_win_pct(cp):
    # Smooth centipawn -> win tendency mapping for display only.
    x = max(-1200, min(1200, cp))
    return 100.0 / (1.0 + math.exp(-x / 180.0))

def print_eval_meter_from_white_cp(white_cp):
    pct = cp_to_white_win_pct(white_cp)
    width = 24
    white_blocks = int(round((pct / 100.0) * width))
    white_blocks = max(0, min(width, white_blocks))
    bar = "#" * white_blocks + "." * (width - white_blocks)

    if white_cp > 80:
        tag = "White better"
    elif white_cp < -80:
        tag = "Black better"
    else:
        tag = "Roughly equal"

    print(f"Eval meter |W {pct:5.1f}%| [{bar}] {tag}")

def result_white_cp(result, side_to_move):
    return result["best_score"] if side_to_move == Side.WHITE else -result["best_score"]


def print_major_divider(label=None):
    print(BORDER_EQ)
    if label:
        print(label)
        print(BORDER_EQ)


def print_minor_divider(label=None):
    print(BORDER_DASH)
    if label:
        print(label)
        print(BORDER_DASH)


def print_learner_feedback(feedback):
    def _unique_keep_order(lines):
        out = []
        seen = set()
        for line in lines:
            key = (line or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(line)
        return out

    print_minor_divider("Learner Guide")
    print(f"Learner | {feedback['headline']}")

    if feedback.get("highlights"):
        print_minor_divider("Move Interpretation")
    for line in feedback.get("highlights", []):
        print(f"Learner | idea: {line}")

    tactical = feedback.get("tactical_alerts", [])
    if tactical:
        print_minor_divider("Tactical Alerts")
        for line in tactical[:4]:
            print(f"Learner | ! {line}")

    defensive = feedback.get("defensive_updates", [])
    if defensive:
        print_minor_divider("Defensive Update")
        for line in defensive[:3]:
            print(f"Learner | {line}")

    countered = feedback.get("countered_enemy_ideas", [])
    if countered:
        print_minor_divider("Countered Threats")
        for line in _unique_keep_order(countered)[:3]:
            print(f"Learner | - {line}")

    remaining = _unique_keep_order(feedback.get("remaining_enemy_ideas", []))
    if remaining:
        print_minor_divider("Remaining Threats")
        for line in remaining[:3]:
            print(f"Learner | - {line}")

    own = feedback.get("own_ideas", [])
    own_texts = _unique_keep_order([idea.get("text", "") for idea in own])
    # Avoid showing the same sentence in both Remaining Threats and Current Plans.
    remaining_set = {(x or "").strip().lower() for x in remaining}
    own_texts = [x for x in own_texts if (x or "").strip().lower() not in remaining_set]

    if not own_texts and own:
        # Fallback if all own ideas were filtered as duplicates.
        own_texts = _unique_keep_order([idea.get("text", "") for idea in own[:1]])

    if own:
        print_minor_divider("Current Plans")
        for line in own_texts[:4]:
            print(f"Learner | - {line}")

# ---- Personality Models ----
class Personality:
    def __init__(
        self,
        playstyle=50,
        tenacity=50,
        accuracy=50,
        temperament=50,
        endgames=50,
        target_elo=0,
        adaptive_mode=False,
    ):
        self.playstyle = max(0, min(100, int(playstyle)))
        self.tenacity = max(0, min(100, int(tenacity)))
        self.accuracy = max(0, min(100, int(accuracy)))
        self.temperament = max(0, min(100, int(temperament)))
        self.endgames = max(0, min(100, int(endgames)))
        self.target_elo = max(0, min(2600, int(target_elo)))
        self.adaptive_mode = bool(adaptive_mode)

class AdaptiveEloTracker:
    def __init__(self, start_elo=2600, min_elo=700, max_elo=2600):
        self.start_elo = int(start_elo)
        self.current_elo = int(start_elo)
        self.min_elo = int(min_elo)
        self.max_elo = int(max_elo)
        self.loss_window = []
        self.blunder_window = []
        self.avg_loss = 0.0
        self.blunder_rate = 0.0
        self.sample_count = 0

    def update_from_cp_loss(self, cp_loss):
        cp_loss = max(0.0, float(cp_loss))
        self.sample_count += 1

        self.loss_window.append(cp_loss)
        if len(self.loss_window) > 12:
            self.loss_window.pop(0)

        blunder = 1.0 if cp_loss >= 180.0 else 0.0
        self.blunder_window.append(blunder)
        if len(self.blunder_window) > 8:
            self.blunder_window.pop(0)

        self.avg_loss = sum(self.loss_window) / max(1, len(self.loss_window))
        self.blunder_rate = sum(self.blunder_window) / max(1, len(self.blunder_window))

        target = self.max_elo - int((3.0 * self.avg_loss) + (380.0 * self.blunder_rate))
        target = max(self.min_elo, min(self.max_elo, target))
        if self.avg_loss <= 25.0 and self.blunder_rate == 0.0:
            target = min(self.max_elo, max(target, self.current_elo + 25))

        smoothed = int(round((0.72 * self.current_elo) + (0.28 * target)))
        self.current_elo = max(self.min_elo, min(self.max_elo, smoothed))
        return self.current_elo

def estimate_bot_elo(depth, movetime_ms):
    if depth <= 1:
        base = 700
    elif depth == 2:
        base = 850
    elif depth == 3:
        base = 1050
    elif depth == 4:
        base = 1250
    elif depth == 5:
        base = 1450
    elif depth == 6:
        base = 1650
    elif depth == 7:
        base = 1820
    elif depth == 8:
        base = 1980
    elif depth == 9:
        base = 2100
    elif depth == 10:
        base = 2200
    else:
        base = 2200 + min(180, (depth - 10) * 30)

    if movetime_ms <= 0:
        time_bonus = 0
    elif movetime_ms <= 500:
        time_bonus = 20
    elif movetime_ms <= 1500:
        time_bonus = 60
    elif movetime_ms <= 3000:
        time_bonus = 100
    elif movetime_ms <= 5000:
        time_bonus = 140
    elif movetime_ms <= 10000:
        time_bonus = 180
    else:
        time_bonus = 220

    return max(700, min(2450, base + time_bonus))

def classify_move_quality(cp_loss):
    if cp_loss <= 20:
        return "excellent"
    if cp_loss <= 60:
        return "good"
    if cp_loss <= 120:
        return "inaccuracy"
    if cp_loss <= 220:
        return "mistake"
    return "blunder"

# ---- Move/Notation Helpers ----
def _sq_to_alg(sq):
    return f"{chr(ord('a') + FilesBoard[sq])}{RanksBoard[sq] + 1}"

def _piece_letter(piece):
    if piece in (Pieces.wN, Pieces.bN):
        return "N"
    if piece in (Pieces.wB, Pieces.bB):
        return "B"
    if piece in (Pieces.wR, Pieces.bR):
        return "R"
    if piece in (Pieces.wQ, Pieces.bQ):
        return "Q"
    if piece in (Pieces.wK, Pieces.bK):
        return "K"
    return ""

def _promotion_letter(piece):
    if piece in (Pieces.wN, Pieces.bN):
        return "N"
    if piece in (Pieces.wB, Pieces.bB):
        return "B"
    if piece in (Pieces.wR, Pieces.bR):
        return "R"
    return "Q"

def _move_disambiguation(board, move, piece):
    from_sq = FROMSQ(move)
    to_sq = TOSQ(move)
    conflicts = []
    move_list = MoveList()
    GenerateAllMoves(board, move_list)
    for i in range(move_list.count):
        other = move_list.moves[i].move
        if other == move:
            continue
        if TOSQ(other) != to_sq:
            continue
        if board.pieces[FROMSQ(other)] != piece:
            continue
        if MakeMove(board, other):
            TakeMove(board)
            conflicts.append(FROMSQ(other))

    if not conflicts:
        return ""

    from_file = FilesBoard[from_sq]
    from_rank = RanksBoard[from_sq]
    same_file = any(FilesBoard[sq] == from_file for sq in conflicts)
    same_rank = any(RanksBoard[sq] == from_rank for sq in conflicts)

    if not same_file:
        return chr(ord("a") + from_file)
    if not same_rank:
        return str(from_rank + 1)
    return f"{chr(ord('a') + from_file)}{from_rank + 1}"

def move_to_san(board, move):
    from_sq = FROMSQ(move)
    to_sq = TOSQ(move)
    piece = board.pieces[from_sq]
    capture = CAPTURED(move) != Pieces.EMPTY or (move & MFLAG_EP) != 0

    if move & MFLAG_CA:
        san = "O-O" if FilesBoard[to_sq] > FilesBoard[from_sq] else "O-O-O"
    else:
        dst = _sq_to_alg(to_sq)
        if piece in (Pieces.wP, Pieces.bP):
            if capture:
                san = f"{chr(ord('a') + FilesBoard[from_sq])}x{dst}"
            else:
                san = dst
        else:
            san = _piece_letter(piece)
            san += _move_disambiguation(board, move, piece)
            if capture:
                san += "x"
            san += dst

        promoted = PROMOTED(move)
        if promoted != Pieces.EMPTY:
            san += f"={_promotion_letter(promoted)}"

    if not MakeMove(board, move):
        return PrMove(move)

    in_check = board.is_sq_attacked(board.king_sq[board.side], board.side ^ 1)
    if in_check:
        legal = count_legal_moves(board)
        san += "#" if legal == 0 else "+"

    TakeMove(board)
    return san

# ---- Board/Position Helpers ----
def load_fen_interactive(board):
    fen = input("Enter FEN (blank = start position):\n> ").strip()
    if not fen:
        fen = START_FEN
    board.parse_fen(fen)
    return fen

def count_legal_moves(board):
    move_list = MoveList()
    GenerateAllMoves(board, move_list)
    legal = 0
    for i in range(move_list.count):
        if MakeMove(board, move_list.moves[i].move):
            legal += 1
            TakeMove(board)
    return legal

def terminal_result(board):
    legal = count_legal_moves(board)
    if legal > 0:
        return None, None
    in_check = board.is_sq_attacked(board.king_sq[board.side], board.side ^ 1)
    if in_check:
        if board.side == Side.WHITE:
            return "0-1", "checkmate"
        return "1-0", "checkmate"
    return "1/2-1/2", "stalemate"

def print_game_state_if_terminal(board):
    legal = count_legal_moves(board)
    if legal > 0:
        return False
    in_check = board.is_sq_attacked(board.king_sq[board.side], board.side ^ 1)
    if in_check:
        winner = "Black" if board.side == Side.WHITE else "White"
        print(f"Checkmate. {winner} wins.")
    else:
        print("Stalemate.")
    return True

# ---- Recording ----
class GameRecorder:
    def __init__(self, start_fen, white_name, black_name):
        self.start_fen = start_fen
        self.white_name = white_name
        self.black_name = black_name
        self.moves_uci = []
        self.moves_san = []

    def add_move(self, board, move):
        self.moves_uci.append(PrMove(move))
        self.moves_san.append(move_to_san(board, move))

    def save(self, result, reason=""):
        os.makedirs("games", exist_ok=True)
        ts = datetime.now()
        date_tag = ts.strftime("%Y.%m.%d")
        fname = ts.strftime("%Y%m%d_%H%M%S")
        path = os.path.join("games", f"hydra_game_{fname}.pgn")

        tags = [
            '[Event "Hydra Terminal Game"]',
            '[Site "Local"]',
            f'[Date "{date_tag}"]',
            '[Round "-"]',
            f'[White "{self.white_name}"]',
            f'[Black "{self.black_name}"]',
            f'[Result "{result}"]',
        ]
        if self.start_fen != START_FEN:
            tags.append('[SetUp "1"]')
            tags.append(f'[FEN "{self.start_fen}"]')

        move_tokens = []
        for idx, san in enumerate(self.moves_san):
            if idx % 2 == 0:
                move_tokens.append(f"{(idx // 2) + 1}.")
            move_tokens.append(san)
        move_tokens.append(result)
        movetext = " ".join(move_tokens)

        uci_line = " ".join(self.moves_uci)
        reason_line = f"\n{{Reason: {reason}}}\n" if reason else "\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(tags))
            f.write("\n\n")
            f.write(movetext)
            f.write(reason_line)
            f.write(f"{{UCI: {uci_line}}}\n")

        return path

# ---- Search Integration ----
def run_search(board, depth, movetime_ms, verbose=False):
    if BOOK_ENABLED:
        book_move = get_book_move(board)
        if book_move != 0:
            return {
                "best_move": book_move,
                "best_move_str": PrMove(book_move),
                "best_score": EvalPosition(board),
                "completed_depth": 0,
                "nodes": 0,
                "cutoffs": 0,
                "first_cutoffs": 0,
                "stopped": 0,
                "quit": 0,
                "pv": [PrMove(book_move)],
                "book": True,
            }
    return IterativeDeepening(
        board,
        max_depth=depth,
        time_limit_ms=movetime_ms,
        stdin_enabled=False,
        verbose=verbose,
    )

def collect_legal_moves(board):
    legal_moves = []
    move_list = MoveList()
    GenerateAllMoves(board, move_list)
    for i in range(move_list.count):
        move = move_list.moves[i].move
        if MakeMove(board, move):
            legal_moves.append(move)
            TakeMove(board)
    return legal_moves

def is_endgame_position(board):
    white_heavy = board.pce_num[4] + board.pce_num[5]
    black_heavy = board.pce_num[10] + board.pce_num[11]
    white_minor = board.pce_num[2] + board.pce_num[3]
    black_minor = board.pce_num[8] + board.pce_num[9]
    total_non_pawn = white_heavy + black_heavy + white_minor + black_minor
    return total_non_pawn <= 6

def _development_bonus(board, move):
    from_sq = (move & 0x7F)
    to_sq = ((move >> 7) & 0x7F)
    piece = board.pieces[from_sq]
    # Knight / bishop development from back rank.
    if piece in (2, 3, 8, 9):
        from_rank = (from_sq // 10) - 2
        if from_rank in (0, 7):
            return 1.0
    # Center occupation bonus.
    if to_sq in (44, 45, 54, 55):
        return 0.6
    return 0.0

def choose_humanized_move(board, depth, movetime_ms, personality):
    base_result = run_search(board, depth, movetime_ms, verbose=False)
    if base_result["best_move"] == 0:
        return 0, {
            "book": base_result.get("book", False),
            "best_move": 0,
            "best_score": base_result.get("best_score", 0),
            "effective_accuracy": personality.accuracy,
            "target_elo": infer_target_elo(personality),
            "fallback": True,
        }

    if base_result.get("book"):
        return base_result["best_move"], {
            "best_move": base_result["best_move"],
            "best_score": base_result["best_score"],
            "effective_accuracy": personality.accuracy,
            "book": True,
            "target_elo": infer_target_elo(personality),
        }

    return choose_trace_personality_move(
        board,
        depth,
        movetime_ms,
        personality,
        base_result,
    )

def assess_player_move(board, move, depth, movetime_ms):
    analysis_depth = max(2, min(depth, 4))
    analysis_time = 0 if movetime_ms == 0 else min(movetime_ms, 1200)

    reference = run_search(board, analysis_depth, analysis_time, verbose=False)
    best_cp = reference.get("best_score", EvalPosition(board))
    ref_move = reference.get("best_move", 0)

    if not MakeMove(board, move):
        return None
    move_cp = -EvalPosition(board)
    gives_check = board.is_sq_attacked(board.king_sq[board.side], board.side ^ 1)
    TakeMove(board)

    cp_loss = max(0.0, float(best_cp) - float(move_cp))
    return {
        "cp_loss": cp_loss,
        "best_cp": int(best_cp),
        "move_cp": int(move_cp),
        "quality": classify_move_quality(cp_loss),
        "gives_check": bool(gives_check),
        "ref_move": ref_move,
    }

# ---- Menu Configuration ----
def configure_personality():
    print("\n=== Humanized Bot Personality ===")
    adaptive_mode = ask_yes_no("Enable adaptive mode (auto strength adapts to your play)?", True)
    if adaptive_mode:
        p = Personality(
            playstyle=52,
            tenacity=62,
            accuracy=82,
            temperament=42,
            endgames=72,
            target_elo=0,
            adaptive_mode=True,
        )
        print("\nAdaptive personality loaded:")
        print("- Mode: Adaptive")
        print("- Elo target: Auto (estimated from settings + adaptation)")
        print("- Sliders: Auto")
        return p
    else:
        print("Use values from 0 to 100.")
        print("playstyle   : foundational -> explosive")
        print("tenacity    : fragile -> resilient")
        print("accuracy    : low -> excellent")
        print("temperament : conservative -> reckless")
        print("endgames    : casual -> precise")
        print("---------------------------------")
        target_elo = ask_elo("Target Elo (400-2600)", 1600)

    p = Personality(
        playstyle=ask_percent("Playstyle", 50),
        tenacity=ask_percent("Tenacity", 60),
        accuracy=ask_percent("Accuracy", 65),
        temperament=ask_percent("Temperament", 45),
        endgames=ask_percent("Endgames", 60),
        target_elo=target_elo,
        adaptive_mode=adaptive_mode,
    )
    print("\nPersonality loaded:")
    print(f"- Playstyle: {p.playstyle}")
    print(f"- Tenacity: {p.tenacity}")
    print(f"- Accuracy: {p.accuracy}")
    print(f"- Temperament: {p.temperament}")
    print(f"- Endgames: {p.endgames}")
    print(f"- Target Elo: {infer_target_elo(p)}")
    print(f"- Adaptive Mode: {'ON' if p.adaptive_mode else 'OFF'}")
    return p

# ---- Menu Actions ----
def print_search_result(result, side_to_move):
    print_minor_divider("Search Result")
    pv_text = " ".join(result["pv"]) if result["pv"] else "(none)"
    if result.get("book"):
        print("Source: Opening book")
    print_minor_divider("Top Move")
    print(f"Best move: {result['best_move_str']}")
    print(f"Eval (cp): {result['best_score']}")
    print_eval_meter_from_white_cp(result_white_cp(result, side_to_move))
    print_minor_divider("Search Stats")
    print(f"Depth reached: {result['completed_depth']}")
    print(f"Nodes: {result['nodes']}")
    print_minor_divider("Principal Variation")
    print(f"Best line (PV): {pv_text}")

def analyze_best_move_only():
    board = Board()
    fen = load_fen_interactive(board)
    depth = ask_int("Search depth", 5)
    movetime_ms = ask_int("Move time (ms, 0 means depth-only)", 0, 0)

    print("\nLoaded position:")
    board.print_board()
    print_major_divider()
    print(f"\nFEN: {fen}")
    print("\nAnalyzing best move...")

    result = run_search(board, depth, movetime_ms, verbose=False)
    print("\nSearch result")
    print_search_result(result, board.side)

def evaluate_position_and_line():
    board = Board()
    fen = load_fen_interactive(board)
    depth = ask_int("Search depth", 5)
    movetime_ms = ask_int("Move time (ms, 0 means depth-only)", 0, 0)

    print("\nLoaded position:")
    board.print_board()
    print_major_divider()
    print(f"\nFEN: {fen}")

    static_eval = EvalPosition(board)
    print(f"Static eval (cp, side-to-move perspective): {static_eval}")

    print("Searching for best sequence...")
    result = run_search(board, depth, movetime_ms, verbose=False)
    print("\nEvaluation + best sequence")
    print_search_result(result, board.side)

def play_game_vs_engine():
    board = Board()
    fen = load_fen_interactive(board)
    side_choice = input("Choose a side: White or Black? (w/b) [w]: ").strip().lower()
    human_side = Side.BLACK if side_choice == "b" else Side.WHITE
    engine_side = Side.BLACK if human_side == Side.WHITE else Side.WHITE

    depth = ask_int("Engine search depth", 4)
    movetime_ms = ask_int("Engine move time (ms, 0 means depth-only)", 0, 0)

    print(f"\nGame start FEN: {fen}")
    print(f"You play: {side_name(human_side)}")
    print(f"Engine plays: {side_name(engine_side)}")
    print("Enter moves like e2e4. Type q to quit.\n")
    print_major_divider("Game Start")
    recorder = GameRecorder(
        fen,
        "Human" if human_side == Side.WHITE else "Hydra 1.0",
        "Human" if human_side == Side.BLACK else "Hydra 1.0",
    )
    tracked_human_ideas = []
    tracked_engine_ideas = []
    game_result = "*"
    game_reason = "unfinished"

    while True:
        board.print_board()
        print_major_divider()
        result, reason = terminal_result(board)
        if result is not None:
            print_game_state_if_terminal(board)
            game_result = result
            game_reason = reason
            break

        if board.side == human_side:
            user_text = input("Your move (e2e4, q=quit): ").strip().lower()
            if user_text in ("q", "quit", "exit"):
                print("Game ended.")
                game_result = "*"
                game_reason = "quit"
                break

            move = ParseMove(user_text, board)
            if move == 0:
                print("Illegal move. Try again.")
                continue
            if not MakeMove(board, move):
                print("Illegal move. Try again.")
                continue
            TakeMove(board)

            learner_feedback = None
            if LEARNER_GUIDE_ENABLED:
                learner_feedback = build_move_feedback(
                    board,
                    move,
                    human_side,
                    "You",
                    previous_enemy_ideas=tracked_engine_ideas,
                )

            recorder.add_move(board, move)
            MakeMove(board, move)
            print(f"You played: {PrMove(move)}")
            print_major_divider()
            if LEARNER_GUIDE_ENABLED and learner_feedback:
                print_learner_feedback(learner_feedback)
                tracked_human_ideas = learner_feedback.get("own_ideas", [])
                tracked_engine_ideas = learner_feedback.get("enemy_ideas", [])
        else:
            print("Engine thinking...")
            result = run_search(board, depth, movetime_ms, verbose=False)
            best_move = result["best_move"]
            if best_move == 0:
                print("Engine has no legal moves.")
                r, rsn = terminal_result(board)
                if r is not None:
                    print_game_state_if_terminal(board)
                    game_result, game_reason = r, rsn
                else:
                    print("Draw.")
                    game_result, game_reason = "1/2-1/2", "no-legal-move"
                break
            print(
                f"Engine plays: {PrMove(best_move)} "
                f"(score {result['best_score']}, depth {result['completed_depth']})"
            )
            print_eval_meter_from_white_cp(result_white_cp(result, board.side))

            learner_feedback = None
            if LEARNER_GUIDE_ENABLED:
                learner_feedback = build_move_feedback(
                    board,
                    best_move,
                    engine_side,
                    "Engine",
                    previous_enemy_ideas=tracked_human_ideas,
                )

            recorder.add_move(board, best_move)
            MakeMove(board, best_move)
            print_major_divider()
            if LEARNER_GUIDE_ENABLED and learner_feedback:
                print_learner_feedback(learner_feedback)
                tracked_engine_ideas = learner_feedback.get("own_ideas", [])
                tracked_human_ideas = learner_feedback.get("enemy_ideas", [])

    saved_path = recorder.save(game_result, game_reason)
    print_major_divider("Game Saved")
    print(f"Game saved: {saved_path}")

def play_game_vs_humanized_bot():
    board = Board()
    fen = load_fen_interactive(board)
    side_choice = input("Choose your side: White or Black? (w/b) [w]: ").strip().lower()
    human_side = Side.BLACK if side_choice == "b" else Side.WHITE
    engine_side = Side.BLACK if human_side == Side.WHITE else Side.WHITE

    depth = ask_int("Bot base search depth", 4)
    movetime_ms = ask_int("Bot move time (ms, 0 means depth-only)", 0, 0)
    personality = configure_personality()
    estimated_cap = estimate_bot_elo(depth, movetime_ms)
    tracker = (
        AdaptiveEloTracker(start_elo=estimated_cap, max_elo=estimated_cap)
        if personality.adaptive_mode
        else None
    )
    if tracker is not None:
        personality.target_elo = tracker.current_elo

    print("\n=== Humanized Bot Match ===")
    print(f"Start FEN: {fen}")
    print(f"You play: {side_name(human_side)}")
    print(f"Humanized bot plays: {side_name(engine_side)}")
    print("Move format: e2e4")
    if tracker is not None:
        print(
            "Adaptive Elo: ON "
            f"(estimated bot ceiling {estimated_cap}, adapts to your move quality)"
        )
    print("Type q to quit.\n")
    print_major_divider("Game Start")
    recorder = GameRecorder(
        fen,
        "Human" if human_side == Side.WHITE else "Hydra Humanized",
        "Human" if human_side == Side.BLACK else "Hydra Humanized",
    )
    tracked_human_ideas = []
    tracked_engine_ideas = []
    game_result = "*"
    game_reason = "unfinished"

    while True:
        board.print_board()
        print_major_divider()
        result, reason = terminal_result(board)
        if result is not None:
            print_game_state_if_terminal(board)
            game_result = result
            game_reason = reason
            break

        if board.side == human_side:
            user_text = input("Your move (e2e4, q=quit): ").strip().lower()
            if user_text in ("q", "quit", "exit"):
                print("Game ended.")
                game_result = "*"
                game_reason = "quit"
                break

            move = ParseMove(user_text, board)
            if move == 0:
                print("Illegal move. Try again.")
                continue

            assessment = None
            if tracker is not None:
                assessment = assess_player_move(board, move, depth, movetime_ms)

            if not MakeMove(board, move):
                print("Illegal move. Try again.")
                continue
            TakeMove(board)

            learner_feedback = None
            if LEARNER_GUIDE_ENABLED:
                learner_feedback = build_move_feedback(
                    board,
                    move,
                    human_side,
                    "You",
                    previous_enemy_ideas=tracked_engine_ideas,
                )

            recorder.add_move(board, move)
            MakeMove(board, move)
            print(f"You played: {PrMove(move)}")
            print_major_divider()
            if LEARNER_GUIDE_ENABLED and learner_feedback:
                print_learner_feedback(learner_feedback)
                tracked_human_ideas = learner_feedback.get("own_ideas", [])
                tracked_engine_ideas = learner_feedback.get("enemy_ideas", [])

            if tracker is not None and assessment is not None:
                new_elo = tracker.update_from_cp_loss(assessment["cp_loss"])
                personality.target_elo = new_elo
                ref_text = PrMove(assessment["ref_move"]) if assessment["ref_move"] else "none"
                print(
                    "Adaptation | "
                    f"your move quality: {assessment['quality']} "
                    f"(loss {int(round(assessment['cp_loss']))}cp, best {assessment['best_cp']}cp, played {assessment['move_cp']}cp, ref {ref_text})"
                )
                print(
                    "Adaptation | "
                    f"bot elo now: {new_elo} "
                    f"(avg loss {tracker.avg_loss:.1f}cp, blunder rate {tracker.blunder_rate * 100.0:.1f}%)"
                )
        else:
            print("Humanized bot thinking...")
            if tracker is not None:
                print(
                    "Thinking | "
                    f"adaptive target elo: {tracker.current_elo}, "
                    f"avg player loss: {tracker.avg_loss:.1f}cp"
                )
            move, meta = choose_humanized_move(board, depth, movetime_ms, personality)
            if move == 0:
                print("Bot has no legal moves.")
                r, rsn = terminal_result(board)
                if r is not None:
                    print_game_state_if_terminal(board)
                    game_result, game_reason = r, rsn
                else:
                    print("Draw.")
                    game_result, game_reason = "1/2-1/2", "no-legal-move"
                break

            msg = f"Bot move: {PrMove(move)}"
            if meta.get("book"):
                msg += " [book]"
            msg += f" | ref: {PrMove(meta['best_move'])} ({meta['best_score']}cp)"
            msg += f" | acc: {meta['effective_accuracy']}"
            if "target_elo" in meta:
                msg += f" | elo: {meta['target_elo']}"
            print(msg)
            if "trace_temperature" in meta:
                print(f"Thinking | trace temperature: {meta['trace_temperature']}")
            if "trace_top" in meta and meta["trace_top"]:
                cand_parts = []
                for item in meta["trace_top"]:
                    cand_parts.append(
                        f"{PrMove(item['move'])}(u={item['utility']},loss={item['loss_cp']}cp)"
                    )
                print("Thinking | top candidates: " + " | ".join(cand_parts))
            white_cp = meta["best_score"] if board.side == Side.WHITE else -meta["best_score"]
            print_eval_meter_from_white_cp(white_cp)

            learner_feedback = None
            if LEARNER_GUIDE_ENABLED:
                learner_feedback = build_move_feedback(
                    board,
                    move,
                    engine_side,
                    "Bot",
                    previous_enemy_ideas=tracked_human_ideas,
                )

            recorder.add_move(board, move)
            MakeMove(board, move)
            print_major_divider()
            if LEARNER_GUIDE_ENABLED and learner_feedback:
                print_learner_feedback(learner_feedback)
                tracked_engine_ideas = learner_feedback.get("own_ideas", [])
                tracked_human_ideas = learner_feedback.get("enemy_ideas", [])

    saved_path = recorder.save(game_result, game_reason)
    print_major_divider("Game Saved")
    print(f"Game saved: {saved_path}")

# ---- Entry Point ----
def main():
    global BOOK_ENABLED, LEARNER_GUIDE_ENABLED

    print("Initializing Hydra 1.0")
    AllInit()
    load_opening_book("openings.txt")

    while True:
        print_major_divider("Hydra Terminal Menu")
        print(f"Opening Book: {'ON' if BOOK_ENABLED else 'OFF'}")
        print(f"Learner Guide: {'ON' if LEARNER_GUIDE_ENABLED else 'OFF'}")
        print_minor_divider("Options")
        print("1) Find the best move in a position (FEN)")
        print("2) Play against the Hydra 1.0 (choose White/Black)")
        print("3) Load position, evaluate, and show best continuation")
        print("4) Toggle opening book ON/OFF")
        print("5) Play against a humanized bot (personality sliders)")
        print("6) Toggle learner guide ON/OFF")
        print("7) Exit")
        print_major_divider()
        choice = input("> ").strip()

        if choice == "1":
            analyze_best_move_only()
        elif choice == "2":
            play_game_vs_engine()
        elif choice == "3":
            evaluate_position_and_line()
        elif choice == "4":
            BOOK_ENABLED = not BOOK_ENABLED
            print(f"Opening book is now {'ON' if BOOK_ENABLED else 'OFF'}.")
        elif choice == "5":
            play_game_vs_humanized_bot()
        elif choice == "6":
            LEARNER_GUIDE_ENABLED = not LEARNER_GUIDE_ENABLED
            print(f"Learner guide is now {'ON' if LEARNER_GUIDE_ENABLED else 'OFF'}.")
        elif choice == "7":
            print("Thank You For Using Hydra 1.0.")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
