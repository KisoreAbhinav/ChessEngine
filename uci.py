import sys

from defs import AllInit, Board, ENGINE_NAME, MAXDEPTH, SearchInfo, Side
from misc import GetTimeMs
from move_io import NOMOVE, ParseMove
from make_mov import MakeMove
from search import SearchPosition


INITIAL_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def ParsePosition(line, board):
    tokens = line.strip().split()
    if not tokens or tokens[0] != "position":
        return

    # Default fallback keeps behavior safe if command is malformed.
    board.parse_fen(INITIAL_FEN)

    idx = 1
    if idx < len(tokens) and tokens[idx] == "startpos":
        idx += 1
    elif idx < len(tokens) and tokens[idx] == "fen":
        idx += 1
        if idx < len(tokens):
            if "moves" in tokens[idx:]:
                moves_at = tokens.index("moves", idx)
                fen = " ".join(tokens[idx:moves_at])
                idx = moves_at
            else:
                fen = " ".join(tokens[idx:])
                idx = len(tokens)
            if fen:
                board.parse_fen(fen)

    if idx < len(tokens) and tokens[idx] == "moves":
        idx += 1
        while idx < len(tokens):
            move = ParseMove(tokens[idx], board)
            if move == NOMOVE:
                break
            if not MakeMove(board, move):
                break
            # Search should always begin from root in this current position.
            board.ply = 0
            idx += 1


def ParseGo(line, info, board):
    tokens = line.strip().split()

    depth = -1
    movetime = -1
    wtime = -1
    btime = -1
    winc = 0
    binc = 0
    movestogo = 30
    infinite = False

    i = 1
    while i < len(tokens):
        tok = tokens[i]
        if tok == "depth" and i + 1 < len(tokens):
            depth = max(1, int(tokens[i + 1]))
            i += 2
            continue
        if tok == "movetime" and i + 1 < len(tokens):
            movetime = max(1, int(tokens[i + 1]))
            i += 2
            continue
        if tok == "wtime" and i + 1 < len(tokens):
            wtime = max(0, int(tokens[i + 1]))
            i += 2
            continue
        if tok == "btime" and i + 1 < len(tokens):
            btime = max(0, int(tokens[i + 1]))
            i += 2
            continue
        if tok == "winc" and i + 1 < len(tokens):
            winc = max(0, int(tokens[i + 1]))
            i += 2
            continue
        if tok == "binc" and i + 1 < len(tokens):
            binc = max(0, int(tokens[i + 1]))
            i += 2
            continue
        if tok == "movestogo" and i + 1 < len(tokens):
            movestogo = max(1, int(tokens[i + 1]))
            i += 2
            continue
        if tok == "infinite":
            infinite = True
            i += 1
            continue
        i += 1

    info.start_time = GetTimeMs()
    info.depth = depth if depth != -1 else MAXDEPTH
    info.time_set = 0
    info.infinite = 1 if infinite else 0
    info.moves_to_go = movestogo
    info.stop_time = 0
    info.stopped = 0

    if board.side == Side.WHITE:
        time_left = wtime
        inc = winc
    else:
        time_left = btime
        inc = binc

    if movetime != -1:
        time_left = movetime
        movestogo = 1
        info.moves_to_go = 1

    if not infinite and time_left != -1:
        alloc = time_left // movestogo
        alloc -= 50  # Safety margin for GUI/IO lag.
        if alloc < 1:
            alloc = 1
        info.time_set = 1
        info.stop_time = info.start_time + alloc + inc

    return SearchPosition(board, info)


def _send(line):
    print(line, flush=True)


def _configure_stdio():
    # Python equivalent of disabling stdio buffering for UCI responsiveness.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True, write_through=True)
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(line_buffering=True)


def _dispatch_uci_command(line, board, info):
    cmd = line.strip()
    if not cmd:
        return True

    if cmd.startswith("isready"):
        _send("readyok")
        return True

    if cmd.startswith("position"):
        ParsePosition(cmd, board)
        return True

    if cmd.startswith("ucinewgame"):
        ParsePosition("position startpos", board)
        return True

    if cmd.startswith("go"):
        ParseGo(cmd, info, board)
        return True

    if cmd.startswith("quit"):
        info.quit = 1
        return False

    if cmd.startswith("uci"):
        _send(f"id name {ENGINE_NAME}")
        _send("id author Hydra")
        _send("uciok")
        return True

    return True


def UciLoop():
    _configure_stdio()
    AllInit()
    board = Board()
    board.parse_fen(INITIAL_FEN)
    info = SearchInfo()
    info.stdin_enabled = 1

    _send(f"id name {ENGINE_NAME}")
    _send("id author Hydra")
    _send("uciok")

    while True:
        line = sys.stdin.readline()
        if line == "":
            break

        if line == "\n":
            continue
        if not _dispatch_uci_command(line, board, info):
            break
        if info.quit:
            break


if __name__ == "__main__":
    UciLoop()
