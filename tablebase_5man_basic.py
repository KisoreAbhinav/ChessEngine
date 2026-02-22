
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Basic5ManEntry:
    fen: str
    verdict: str
    best_move_hint: Optional[str] = None
    note: str = ""


def _normalize_fen_key(fen: str) -> str:
    """
    Keep the first 4 FEN fields:
    board / side / castling / en-passant.
    """
    parts = fen.strip().split()
    if len(parts) < 4:
        return fen.strip()
    return " ".join(parts[:4])


def _piece_count_from_fen(fen: str) -> int:
    board = fen.split()[0]
    count = 0
    for ch in board:
        if ch.isalpha():
            count += 1
    return count


def is_five_man_fen(fen: str) -> bool:
    return _piece_count_from_fen(fen) == 5



_SEED_ENTRIES: List[Basic5ManEntry] = [
    # KQ+R vs K+P style snapshots
    Basic5ManEntry(
        fen="6k1/7p/6K1/8/8/8/6Q1/6R1 w - - 0 1",
        verdict="white_win",
        best_move_hint="g2a8",
        note="Heavy pieces dominate; white conversion sample.",
    ),
    Basic5ManEntry(
        fen="6k1/p7/6K1/8/8/8/6Q1/7r b - - 0 1",
        verdict="white_win",
        note="Black rook activity but white queen+king usually decide.",
    ),
    Basic5ManEntry(
        fen="7k/7p/6K1/8/8/8/6Q1/6R1 w - - 0 1",
        verdict="white_win",
        best_move_hint="g2a8",
        note="Typical mating-net pattern setup.",
    ),
    Basic5ManEntry(
        fen="6k1/7p/8/8/8/6K1/6Q1/6R1 b - - 0 1",
        verdict="white_win",
        note="Defensive side to move but still usually lost.",
    ),

    # KR+B+N vs K (5-man because 2 kings + 3 pieces)
    Basic5ManEntry(
        fen="7k/8/8/3NK3/2B5/8/8/R7 w - - 0 1",
        verdict="white_win",
        note="Overwhelming material; practical forced win class.",
    ),
    Basic5ManEntry(
        fen="6k1/8/8/3NK3/2B5/8/8/R7 w - - 0 1",
        verdict="white_win",
        note="White should convert with coordinated minor+rook control.",
    ),
    Basic5ManEntry(
        fen="7k/8/5N2/4KB2/8/8/8/R7 w - - 0 1",
        verdict="white_win",
        note="Centralized king plus rook decides quickly.",
    ),

    # KQ+B+N vs K
    Basic5ManEntry(
        fen="7k/8/3N4/4KB2/8/8/8/3Q4 w - - 0 1",
        verdict="white_win",
        note="Queen + minor support: winning class.",
    ),
    Basic5ManEntry(
        fen="6k1/8/3N4/4KB2/8/8/8/3Q4 w - - 0 1",
        verdict="white_win",
        note="Conversion sample for queen-dominant 5-man ending.",
    ),

    # KRR vs K+P
    Basic5ManEntry(
        fen="7k/7p/8/8/8/6K1/8/R5R1 w - - 0 1",
        verdict="white_win",
        best_move_hint="a1a8",
        note="Two rooks should convert cleanly vs lone pawn.",
    ),
    Basic5ManEntry(
        fen="6k1/7p/8/8/8/6K1/8/R5R1 b - - 0 1",
        verdict="white_win",
        note="Black to move but white material edge is decisive.",
    ),

    # KQ+P vs KR
    Basic5ManEntry(
        fen="6k1/8/8/8/8/6K1/6P1/6Qr w - - 0 1",
        verdict="white_win",
        note="Often winning, queen and pawn coordinate against rook.",
    ),
    Basic5ManEntry(
        fen="6k1/8/8/8/8/6K1/6P1/6Qr b - - 0 1",
        verdict="white_win",
        note="Defender to move but practical winning pressure persists.",
    ),

    # KR+2P vs KR
    Basic5ManEntry(
        fen="6k1/8/8/8/8/6K1/6P1/6Rr w - - 0 1",
        verdict="white_win",
        note="Rook + pawn vs rook sample with practical winning chances.",
    ),
    Basic5ManEntry(
        fen="6k1/8/8/8/8/6K1/6P1/6Rr b - - 0 1",
        verdict="draw",
        note="Some setups hold with active rook checks.",
    ),

    # KQ vs K + minor + pawn
    Basic5ManEntry(
        fen="6k1/7p/8/8/8/6K1/6Q1/7n w - - 0 1",
        verdict="white_win",
        note="Queen often overpowers knight+pawn if king is active.",
    ),
    Basic5ManEntry(
        fen="6k1/7p/8/8/8/6K1/6Q1/7n b - - 0 1",
        verdict="white_win",
        note="Defensive resources exist but usually insufficient.",
    ),

    # Known fortress-like sample draws
    Basic5ManEntry(
        fen="8/8/8/8/8/6k1/6p1/b5KR b - - 0 1",
        verdict="draw",
        note="Rook pawn + king corner motifs can draw.",
    ),
    Basic5ManEntry(
        fen="8/8/8/8/8/6k1/6p1/b5KR w - - 0 1",
        verdict="draw",
        note="Classic practical drawing shell sample.",
    ),

    # Symmetric queen endgame seeds
    Basic5ManEntry(
        fen="6k1/7p/8/8/8/6K1/6Q1/6q1 w - - 0 1",
        verdict="draw",
        note="Perpetual/check resource-heavy queen endings.",
    ),
    Basic5ManEntry(
        fen="6k1/7p/8/8/8/6K1/6Q1/6q1 b - - 0 1",
        verdict="draw",
        note="Exact result depends on tempo motifs; seed marked draw.",
    ),
]


BASIC_5MAN_TABLE: Dict[str, Basic5ManEntry] = {
    _normalize_fen_key(entry.fen): entry for entry in _SEED_ENTRIES
}


def probe_basic_5man(fen: str) -> Optional[Basic5ManEntry]:

    return BASIC_5MAN_TABLE.get(_normalize_fen_key(fen))


def all_basic_5man_entries() -> List[Basic5ManEntry]:
    return list(_SEED_ENTRIES)
