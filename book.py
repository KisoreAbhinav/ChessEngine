import os
import random

from defs import Board
from make_mov import MakeMove, TakeMove
from move_gen import GenerateAllMoves, MoveList
from move_io import NOMOVE, ParseMove


START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
DEFAULT_BOOK_PATH = "openings.txt"

_BOOK = {}
_BOOK_LOADED = False
_BOOK_PATH = DEFAULT_BOOK_PATH


def _add_book_move(pos_key, move):
    if pos_key not in _BOOK:
        _BOOK[pos_key] = {}
    _BOOK[pos_key][move] = _BOOK[pos_key].get(move, 0) + 1


def load_opening_book(path=DEFAULT_BOOK_PATH):
    global _BOOK_LOADED, _BOOK_PATH

    if _BOOK_LOADED and _BOOK_PATH == path:
        return

    _BOOK.clear()
    _BOOK_PATH = path
    _BOOK_LOADED = True

    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue

        tokens = line.split()
        pos = Board()
        pos.parse_fen(START_FEN)

        for token in tokens:
            pos_key = pos.pos_key
            move = ParseMove(token, pos)
            if move == NOMOVE:
                break

            _add_book_move(pos_key, move)

            if not MakeMove(pos, move):
                break


def _legal_moves_set(board):
    legal = set()
    move_list = MoveList()
    GenerateAllMoves(board, move_list)

    for i in range(move_list.count):
        move = move_list.moves[i].move
        if MakeMove(board, move):
            legal.add(move)
            TakeMove(board)
    return legal


def get_book_move(board):
    if not _BOOK_LOADED:
        load_opening_book(_BOOK_PATH)

    candidates = _BOOK.get(board.pos_key)
    if not candidates:
        return NOMOVE

    legal = _legal_moves_set(board)
    weighted = [(move, weight) for move, weight in candidates.items() if move in legal]
    if not weighted:
        return NOMOVE

    total = sum(weight for _, weight in weighted)
    pick = random.randint(1, total)
    running = 0
    for move, weight in weighted:
        running += weight
        if running >= pick:
            return move
    return weighted[-1][0]

