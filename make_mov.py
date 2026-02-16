from defs import *
from validate import SqOnBoard, PieceValid
from hashkeys import PieceKeys, SideKey, CastleKeys


# Move Decoding Macros (Standardized to your defs.py naming)
def FROMSQ(m):     return (m & 0x7F)
def TOSQ(m):       return ((m >> 7) & 0x7F)
def CAPTURED(m):   return ((m >> 14) & 0xF)
def PROMOTED(m):   return ((m >> 20) & 0xF)

# Data Mapping for Legality Check
Kings = [Pieces.wK, Pieces.bK]

# --- Bitboard Helpers ---
def clear_bit(bitboard, sq64):
    return bitboard & ~(1 << sq64)

def set_bit(bitboard, sq64):
    return bitboard | (1 << sq64)

# --- Hashing Helpers ---
def HASH_PCE(pce, sq, pos):
    pos.pos_key ^= PieceKeys[pce][sq]

def HASH_CA(pos):
    pos.pos_key ^= CastleKeys[pos.castle_perm]

def HASH_SIDE(pos):
    pos.pos_key ^= SideKey

def HASH_EP(pos):
    pos.pos_key ^= PieceKeys[Pieces.EMPTY][pos.en_passant]




# --- Core Board Manipulators ---

def ClearPiece(sq, pos):
    assert SqOnBoard(sq)
    pce = pos.pieces[sq]
    col = PieceCol[pce]
    
    # 1. Use the Helper to hash out
    HASH_PCE(pce, sq, pos)
    
    # 2. Update pieces array and material
    pos.pieces[sq] = Pieces.EMPTY
    pos.material[col] -= PieceVal[pce]
    
    # 3. Update Piece Counters and Bitboards
    if PieceBig[pce]:
        pos.big_pce[col] -= 1
        if PieceMaj[pce]: pos.maj_pce[col] -= 1
        else: pos.min_pce[col] -= 1
    else:
        # Update pawn bitboards ONLY (No += 1 counters here!)
        sq64 = Sq120to64[sq]
        pos.pawns[col] = clear_bit(pos.pawns[col], sq64)
        pos.pawns[2] = clear_bit(pos.pawns[2], sq64)
    
    # 4. Piece List Swap and Pop
    t_pceNum = -1
    for i in range(pos.pce_num[pce]):
        if pos.p_list[pce][i] == sq:
            t_pceNum = i
            break
            
    assert t_pceNum != -1
    pos.pce_num[pce] -= 1
    pos.p_list[pce][t_pceNum] = pos.p_list[pce][pos.pce_num[pce]]

def AddPiece(sq, pos, pce):
    assert SqOnBoard(sq)
    assert PieceValid(pce)
    col = PieceCol[pce]
    
    HASH_PCE(pce, sq, pos)
    
    pos.pieces[sq] = pce
    
    if PieceBig[pce]:
        pos.big_pce[col] += 1
        if PieceMaj[pce]: pos.maj_pce[col] += 1
        else: pos.min_pce[col] += 1
    else:
        # Update pawn bitboards ONLY
        sq64 = Sq120to64[sq]
        pos.pawns[col] = set_bit(pos.pawns[col], sq64)
        pos.pawns[2] = set_bit(pos.pawns[2], sq64)
        
    pos.material[col] += PieceVal[pce]
    
    pos.p_list[pce][pos.pce_num[pce]] = sq
    pos.pce_num[pce] += 1

def MovePiece(from_sq, to_sq, pos):
    """Moves a piece on the board, updating hashes and internal piece lists."""
    assert SqOnBoard(from_sq)
    assert SqOnBoard(to_sq)
    
    pce = pos.pieces[from_sq]
    col = PieceCol[pce]
    
    # 1. Hash the piece out of the old square and into the new square
    HASH_PCE(pce, from_sq, pos)
    pos.pieces[from_sq] = Pieces.EMPTY
    
    HASH_PCE(pce, to_sq, pos)
    pos.pieces[to_sq] = pce
    
    # 2. Update Pawn Bitboards if necessary
    if not PieceBig[pce]:
        f_sq64 = Sq120to64[from_sq]
        t_sq64 = Sq120to64[to_sq]
        
        # Clear old bit, set new bit
        pos.pawns[col] = clear_bit(pos.pawns[col], f_sq64)
        pos.pawns[col] = set_bit(pos.pawns[col], t_sq64)
        
        # Update "Both Pawns" bitboard
        pos.pawns[2] = clear_bit(pos.pawns[2], f_sq64)
        pos.pawns[2] = set_bit(pos.pawns[2], t_sq64)
        
    # 3. Update the Piece List (p_list)
    # We find where the piece was in the list and update its square
    for i in range(pos.pce_num[pce]):
        if pos.p_list[pce][i] == from_sq:
            pos.p_list[pce][i] = to_sq
            break
            
    # 4. Update King square tracker if a King moved
    if pce == Pieces.wK or pce == Pieces.bK:
        pos.king_sq[col] = to_sq

def MakeMove(pos, move):
    from_sq = FROMSQ(move)
    to_sq = TOSQ(move)
    side = pos.side
    
    # 1. Store current state in history for TakeMove
    pos.history[pos.his_ply].pos_key = pos.pos_key
    
    # 2. Handle En Passant Capture
    if move & MFLAG_EP:
        if side == Side.WHITE:
            ClearPiece(to_sq - 10, pos)
        else:
            ClearPiece(to_sq + 10, pos)
            
    # 3. Handle Castling
    elif move & MFLAG_CA:
        if to_sq == Square.C1: MovePiece(Square.A1, Square.D1, pos)
        elif to_sq == Square.G1: MovePiece(Square.H1, Square.F1, pos)
        elif to_sq == Square.C8: MovePiece(Square.A8, Square.D8, pos)
        elif to_sq == Square.G8: MovePiece(Square.H8, Square.F8, pos)

    # 4. Hash out current state
    if pos.en_passant != Square.NO_SQ: HASH_EP(pos)
    HASH_CA(pos) # Hash out old permissions
    
    # Update history and permissions
    pos.history[pos.his_ply].move = move
    pos.history[pos.his_ply].fifty_move = pos.fifty_move
    pos.history[pos.his_ply].en_passant = pos.en_passant
    pos.history[pos.his_ply].castle_perm = pos.castle_perm
    
    pos.castle_perm &= CastlePerm[from_sq]
    pos.castle_perm &= CastlePerm[to_sq]
    pos.en_passant = Square.NO_SQ
    
    HASH_CA(pos) # Hash in NEW permissions
    
    # 5. Handle Standard Captures
    pos.fifty_move += 1
    captured = CAPTURED(move)
    if captured != Pieces.EMPTY:
        ClearPiece(to_sq, pos)
        pos.fifty_move = 0
        
    pos.his_ply += 1
    pos.ply += 1
    
    # 6. Set new En Passant square if pawn double-moved
    if PiecePawn[pos.pieces[from_sq]]:
        pos.fifty_move = 0
        if move & MFLAG_PS:
            if side == Side.WHITE:
                pos.en_passant = from_sq + 10
            else:
                pos.en_passant = from_sq - 10
            HASH_EP(pos)
            
    # 7. Move the piece and handle promotions
    MovePiece(from_sq, to_sq, pos)
    
    prom_pce = PROMOTED(move)
    if prom_pce != Pieces.EMPTY:
        ClearPiece(to_sq, pos)
        AddPiece(to_sq, pos, prom_pce)
        
    # 8. Final Legality Check
    pos.side ^= 1
    HASH_SIDE(pos)
    
    # Check if the side that just moved left their king in check
    if pos.is_sq_attacked(pos.king_sq[side], pos.side):
        return False
        
    return True


def TakeMove(pos):
    """Undoes the last move made on the board using the history array."""
    # 1. Decrement counters first
    pos.his_ply -= 1
    pos.ply -= 1
    
    # 2. Get the move info from history
    move = pos.history[pos.his_ply].move
    from_sq = FROMSQ(move)
    to_sq = TOSQ(move)
    
    # 3. Hash out current state
    if pos.en_passant != Square.NO_SQ: HASH_EP(pos)
    HASH_CA(pos)
    
    # 4. Restore state from history
    pos.castle_perm = pos.history[pos.his_ply].castle_perm
    pos.fifty_move = pos.history[pos.his_ply].fifty_move
    pos.en_passant = pos.history[pos.his_ply].en_passant
    
    # 5. Hash new (restored) state back in
    if pos.en_passant != Square.NO_SQ: HASH_EP(pos)
    HASH_CA(pos)
    
    # 6. Flip side back
    pos.side ^= 1
    HASH_SIDE(pos)
    
    # 7. Handle special move types
    if move & MFLAG_EP:
        # If it was an En Passant capture, add the pawn back [00:01:51]
        if pos.side == Side.WHITE:
            AddPiece(to_sq - 10, pos, Pieces.bP)
        else:
            AddPiece(to_sq + 10, pos, Pieces.wP)
    
    elif move & MFLAG_CA:
        # Move the Rook back to its original square [00:02:11]
        if to_sq == Square.C1: MovePiece(Square.D1, Square.A1, pos)
        elif to_sq == Square.G1: MovePiece(Square.F1, Square.H1, pos)
        elif to_sq == Square.C8: MovePiece(Square.D8, Square.A8, pos)
        elif to_sq == Square.G8: MovePiece(Square.F8, Square.H8, pos)
        
    # 8. Move the main piece back (From To_Sq back to From_Sq)
    MovePiece(to_sq, from_sq, pos)
    
    # 9. Handle captured pieces
    captured = CAPTURED(move)
    if captured != Pieces.EMPTY:
        AddPiece(to_sq, pos, captured)
        
    # 10. Handle promotions
    # If we promoted, we currently have a Queen/Rook etc. on the From_Sq. 
    # We must clear it and put the pawn back. [00:03:25]
    if PROMOTED(move) != Pieces.EMPTY:
        ClearPiece(from_sq, pos)
        if pos.side == Side.WHITE:
            AddPiece(from_sq, pos, Pieces.wP)
        else:
            AddPiece(from_sq, pos, Pieces.bP)


CastlePerm = [
    15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
    15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
    15, 13, 15, 15, 15, 12, 15, 15, 14, 15,
    15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
    15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
    15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
    15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
    15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
    15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
    15,  7, 15, 15, 15,  3, 15, 15, 11, 15,
    15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
    15, 15, 15, 15, 15, 15, 15, 15, 15, 15
]