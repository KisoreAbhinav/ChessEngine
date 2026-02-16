from dataclasses import dataclass
from defs import MAXDEPTH

NOMOVE = 0
DEFAULT_PV_SIZE_MB = 2


@dataclass
class PVEntry:
    pos_key: int = 0
    move: int = NOMOVE


class PVTable:
    __slots__ = ("p_table", "num_entries")

    def __init__(self):
        self.p_table = []
        self.num_entries = 0


def InitPvTable(pv_table, size_mb=DEFAULT_PV_SIZE_MB):
    """
    Allocate PV table entries based on requested size in MB.
    Mirrors the C approach: entries = bytes / entry_size, then subtract 2
    as a small safety buffer.
    """
    # C-style aligned PV entry size (U64 + int + padding) ~= 16 bytes.
    approx_entry_size_bytes = 16
    size_bytes = size_mb * 1024 * 1024
    num_entries = (size_bytes // approx_entry_size_bytes) - 2
    if num_entries < 1:
        num_entries = 1

    pv_table.num_entries = int(num_entries)
    pv_table.p_table = [PVEntry() for _ in range(pv_table.num_entries)]
    ClearPvTable(pv_table)


def ClearPvTable(pv_table):
    for i in range(pv_table.num_entries):
        pv_table.p_table[i].pos_key = 0
        pv_table.p_table[i].move = NOMOVE


def StorePvMove(pos, move):
    pv_table = pos.pv_table
    if pv_table.num_entries <= 0:
        return

    index = pos.pos_key % pv_table.num_entries
    assert 0 <= index <= pv_table.num_entries - 1

    pv_table.p_table[index].pos_key = pos.pos_key
    pv_table.p_table[index].move = move


def ProbePvTable(pos):
    pv_table = pos.pv_table
    if pv_table.num_entries <= 0:
        return NOMOVE

    index = pos.pos_key % pv_table.num_entries
    assert 0 <= index <= pv_table.num_entries - 1

    entry = pv_table.p_table[index]
    if entry.pos_key == pos.pos_key:
        return entry.move
    return NOMOVE


def GetPvLine(depth, pos):
    assert depth < MAXDEPTH

    from move_gen import MoveExists
    from make_mov import MakeMove, TakeMove

    move = ProbePvTable(pos)
    count = 0

    while move != NOMOVE and count < depth:
        assert count < MAXDEPTH

        if MoveExists(pos, move):
            MakeMove(pos, move)
            pos.pv_array[count] = move
            count += 1
        else:
            break

        move = ProbePvTable(pos)

    # Restore the board to its original state.
    while pos.ply > 0:
        TakeMove(pos)

    return count
