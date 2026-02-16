from defs import AllInit, Board, Side
from evaluate import EvalPosition
from make_mov import MakeMove, TakeMove
from move_gen import GenerateAllMoves, MoveList
from move_io import ParseMove, PrMove
from search import IterativeDeepening


START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


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
    return IterativeDeepening(
        board,
        max_depth=depth,
        time_limit_ms=movetime_ms,
        stdin_enabled=False,
        verbose=verbose,
    )


def print_search_result(result):
    pv_text = " ".join(result["pv"]) if result["pv"] else "(none)"
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
    print("Initializing Hydra 1.0")
    AllInit()

    while True:
        print("\n----------Hydra Terminal Menu---------------")
        print("1) Find the best move in a position (FEN)")
        print("2) Play against the Hydra 1.0 (choose White/Black)")
        print("3) Load position, evaluate, and show best continuation")
        print("4) Exit")
        choice = input("> ").strip()

        if choice == "1":
            analyze_best_move_only()
        elif choice == "2":
            play_game_vs_engine()
        elif choice == "3":
            evaluate_position_and_line()
        elif choice == "4":
            print("Thank You For Using Hydra 1.0.")
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
