from defs import AllInit, Board, Side
from evaluate import EvalPosition
from book import get_book_move, load_opening_book
from make_mov import MakeMove, TakeMove
from move_gen import GenerateAllMoves, MoveList
from move_io import ParseMove, PrMove
from search import IterativeDeepening
import math
import random


START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BOOK_ENABLED = True


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


def side_name(side):
    return "White" if side == Side.WHITE else "Black"


class Personality:
    def __init__(self, playstyle=50, tenacity=50, accuracy=50, temperament=50, endgames=50):
        self.playstyle = max(0, min(100, int(playstyle)))
        self.tenacity = max(0, min(100, int(tenacity)))
        self.accuracy = max(0, min(100, int(accuracy)))
        self.temperament = max(0, min(100, int(temperament)))
        self.endgames = max(0, min(100, int(endgames)))


def ask_percent(prompt, default_value=50):
    return ask_int(prompt, default_value, 0)


def configure_personality():
    print("\n=== Humanized Bot Personality ===")
    print("Use values from 0 to 100.")
    print("playstyle   : foundational -> explosive")
    print("tenacity    : fragile -> resilient")
    print("accuracy    : low -> excellent")
    print("temperament : conservative -> reckless")
    print("endgames    : casual -> precise")
    print("---------------------------------")

    p = Personality(
        playstyle=ask_percent("Playstyle", 50),
        tenacity=ask_percent("Tenacity", 60),
        accuracy=ask_percent("Accuracy", 65),
        temperament=ask_percent("Temperament", 45),
        endgames=ask_percent("Endgames", 60),
    )
    print("\nPersonality loaded:")
    print(f"- Playstyle: {p.playstyle}")
    print(f"- Tenacity: {p.tenacity}")
    print(f"- Accuracy: {p.accuracy}")
    print(f"- Temperament: {p.temperament}")
    print(f"- Endgames: {p.endgames}")
    return p


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
    legal_moves = collect_legal_moves(board)
    if not legal_moves:
        return 0, {}

    # Strong reference move from normal engine logic.
    base_result = run_search(board, depth, movetime_ms, verbose=False)
    best_move = base_result["best_move"]
    best_score = base_result["best_score"]

    endgame = is_endgame_position(board)
    effective_accuracy = personality.accuracy
    if endgame:
        effective_accuracy = int((2 * effective_accuracy + personality.endgames) / 3)
    if best_score < -150:
        effective_accuracy = int((effective_accuracy * 0.7) + (personality.tenacity * 0.3))
    effective_accuracy = max(0, min(100, effective_accuracy))

    scored = []
    for move in legal_moves:
        from_sq = (move & 0x7F)
        capture = ((move >> 14) & 0xF) != 0 or (move & 0x40000) != 0
        promotion = ((move >> 20) & 0xF) != 0
        mover_piece = board.pieces[from_sq]

        if not MakeMove(board, move):
            continue

        post_eval = -EvalPosition(board)
        gives_check = board.is_sq_attacked(board.king_sq[board.side], board.side ^ 1)
        TakeMove(board)

        score = post_eval * 0.10

        if move == best_move:
            score += 30 + (effective_accuracy * 1.2)
        if capture:
            score += 10 + (personality.playstyle * 0.35) + (personality.temperament * 0.20)
        if promotion:
            score += 55
        if gives_check:
            score += 6 + (personality.playstyle * 0.22) + (personality.temperament * 0.22)

        score += _development_bonus(board, move) * ((100 - personality.playstyle) * 0.35)

        # Conservative bots avoid steep drops from best line; reckless bots tolerate risk.
        if post_eval < (best_score - 80):
            risk_penalty = (best_score - post_eval) * ((100 - personality.temperament) / 100.0) * 0.45
            score -= risk_penalty

        # Endgame preference: king activity and precision.
        if endgame:
            if mover_piece in (6, 12):
                score += personality.endgames * 0.25
            score += personality.endgames * 0.12
        else:
            # Non-endgame king drifting is punished for conservative styles.
            if mover_piece in (6, 12):
                score -= (100 - personality.temperament) * 0.18

        noise_amp = (100 - effective_accuracy) * 0.60
        score += random.uniform(-noise_amp, noise_amp)
        scored.append((score, move))

    if not scored:
        return best_move, {"book": base_result.get("book", False), "fallback": True}

    scored.sort(reverse=True, key=lambda x: x[0])

    if effective_accuracy >= 96:
        chosen = scored[0][1]
    else:
        top_band = 1 + ((100 - effective_accuracy) // 15) + (personality.temperament // 35)
        top_band = max(1, min(len(scored), int(top_band)))
        candidates = scored[:top_band]

        temp = 0.35 + ((100 - effective_accuracy) / 45.0) + (personality.temperament / 120.0)
        if endgame:
            temp *= max(0.6, 1.2 - (personality.endgames / 140.0))
        if best_score < -150:
            if personality.tenacity < 40:
                temp *= 1.25
            elif personality.tenacity > 70:
                temp *= 0.85

        max_score = max(s for s, _ in candidates)
        weights = [math.exp((s - max_score) / max(0.05, temp)) for s, _ in candidates]
        chosen = random.choices([m for _, m in candidates], weights=weights, k=1)[0]

    meta = {
        "best_move": best_move,
        "best_score": best_score,
        "effective_accuracy": effective_accuracy,
        "book": base_result.get("book", False),
    }
    return chosen, meta


def print_search_result(result):
    pv_text = " ".join(result["pv"]) if result["pv"] else "(none)"
    if result.get("book"):
        print("Source: Opening book")
    print(f"Best move: {result['best_move_str']}")
    print(f"Eval (cp): {result['best_score']}")
    print(f"Depth reached: {result['completed_depth']}")
    print(f"Nodes: {result['nodes']}")
    print(f"Best line (PV): {pv_text}")


def analyze_best_move_only():
    board = Board()
    fen = load_fen_interactive(board)
    depth = ask_int("Search depth", 5)
    movetime_ms = ask_int("Move time (ms, 0 means depth-only)", 0, 0)

    print("\nLoaded position:")
    board.print_board()
    print(f"\nFEN: {fen}")
    print("\nAnalyzing best move...")

    result = run_search(board, depth, movetime_ms, verbose=False)
    print("\nSearch result")
    print_search_result(result)


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

    while True:
        board.print_board()
        if print_game_state_if_terminal(board):
            break

        if board.side == human_side:
            user_text = input("Your move (e2e4, q=quit): ").strip().lower()
            if user_text in ("q", "quit", "exit"):
                print("Game ended.")
                break

            move = ParseMove(user_text, board)
            if move == 0:
                print("Illegal move. Try again.")
                continue
            if not MakeMove(board, move):
                print("Illegal move. Try again.")
                continue
        else:
            print("Engine thinking...")
            result = run_search(board, depth, movetime_ms, verbose=False)
            best_move = result["best_move"]
            if best_move == 0:
                print("Engine has no legal moves.")
                if print_game_state_if_terminal(board):
                    break
                print("Draw.")
                break
            print(
                f"Engine plays: {PrMove(best_move)} "
                f"(score {result['best_score']}, depth {result['completed_depth']})"
            )
            MakeMove(board, best_move)


def play_game_vs_humanized_bot():
    board = Board()
    fen = load_fen_interactive(board)
    side_choice = input("Choose your side: White or Black? (w/b) [w]: ").strip().lower()
    human_side = Side.BLACK if side_choice == "b" else Side.WHITE
    engine_side = Side.BLACK if human_side == Side.WHITE else Side.WHITE

    depth = ask_int("Bot base search depth", 4)
    movetime_ms = ask_int("Bot move time (ms, 0 means depth-only)", 0, 0)
    personality = configure_personality()

    print("\n=== Humanized Bot Match ===")
    print(f"Start FEN: {fen}")
    print(f"You play: {side_name(human_side)}")
    print(f"Humanized bot plays: {side_name(engine_side)}")
    print("Move format: e2e4")
    print("Type q to quit.\n")

    while True:
        board.print_board()
        if print_game_state_if_terminal(board):
            break

        if board.side == human_side:
            user_text = input("Your move (e2e4, q=quit): ").strip().lower()
            if user_text in ("q", "quit", "exit"):
                print("Game ended.")
                break

            move = ParseMove(user_text, board)
            if move == 0 or not MakeMove(board, move):
                print("Illegal move. Try again.")
                continue
        else:
            print("Humanized bot thinking...")
            move, meta = choose_humanized_move(board, depth, movetime_ms, personality)
            if move == 0:
                print("Bot has no legal moves.")
                if print_game_state_if_terminal(board):
                    break
                print("Draw.")
                break

            msg = f"Bot move: {PrMove(move)}"
            if meta.get("book"):
                msg += " [book]"
            msg += f" | ref: {PrMove(meta['best_move'])} ({meta['best_score']}cp)"
            msg += f" | acc: {meta['effective_accuracy']}"
            print(msg)

            MakeMove(board, move)


def evaluate_position_and_line():
    board = Board()
    fen = load_fen_interactive(board)
    depth = ask_int("Search depth", 5)
    movetime_ms = ask_int("Move time (ms, 0 means depth-only)", 0, 0)

    print("\nLoaded position:")
    board.print_board()
    print(f"\nFEN: {fen}")

    static_eval = EvalPosition(board)
    print(f"Static eval (cp, side-to-move perspective): {static_eval}")

    print("Searching for best sequence...")
    result = run_search(board, depth, movetime_ms, verbose=False)
    print("\nEvaluation + best sequence")
    print_search_result(result)


def main():
    global BOOK_ENABLED

    print("Initializing Hydra 1.0")
    AllInit()
    load_opening_book("openings.txt")

    while True:
        print("\n----------Hydra Terminal Menu---------------")
        print(f"Opening Book: {'ON' if BOOK_ENABLED else 'OFF'}")
        print("1) Find the best move in a position (FEN)")
        print("2) Play against the Hydra 1.0 (choose White/Black)")
        print("3) Load position, evaluate, and show best continuation")
        print("4) Toggle opening book ON/OFF")
        print("5) Play against a humanized bot (personality sliders)")
        print("6) Exit")
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
            print("Thank You For Using Hydra 1.0.")
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
