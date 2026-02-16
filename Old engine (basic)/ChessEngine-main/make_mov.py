from defs import *
from validate import SqOnBoard, PieceValid
import hashkeys
from hashkeys import PieceKeys, CastleKeys


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
# def HASH_PCE(pce, sq, pos):
#     pos.pos_key ^= PieceKeys[pce][sq]

def HASH_PCE(pce, sq, pos):
    # Only XOR if it's an actual piece (1-12). 
    # Never XOR Pieces.EMPTY (0) or NO_SQ (99).
    if pce != Pieces.EMPTY and pce != 99:
        pos.pos_key ^= PieceKeys[pce][sq]

def HASH_CA(pos):
    pos.pos_key ^= CastleKeys[pos.castle_perm]

def HASH_SIDE(pos):
    pos.pos_key ^= hashkeys.SideKey

# def HASH_EP(pos):
#     pos.pos_key ^= PieceKeys[Pieces.EMPTY][pos.en_passant]

def HASH_EP(pos):
    # Only XOR if there is an active en passant square
    if pos.en_passant != NO_SQ:
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

def MakeMove(pos, move):
    assert pos.check_board()

    from_sq = FROMSQ(move)
    to_sq = TOSQ(move)
    side = pos.side

    # 1. Store current state for TakeMove
    pos.history[pos.his_ply].pos_key = pos.pos_key
    pos.history[pos.his_ply].move = move
    pos.history[pos.his_ply].fifty_move = pos.fifty_move
    pos.history[pos.his_ply].en_passant = pos.en_passant
    pos.history[pos.his_ply].castle_perm = pos.castle_perm

    # 2. Handle special captures/moves before the main piece move
    if move & MFLAG_EP:
        if side == Side.WHITE:
            ClearPiece(to_sq - 10, pos)
        else:
            ClearPiece(to_sq + 10, pos)
    elif move & MFLAG_CA:
        if to_sq == Square.C1:
            MovePiece(Square.A1, Square.D1, pos)
        elif to_sq == Square.G1:
            MovePiece(Square.H1, Square.F1, pos)
        elif to_sq == Square.C8:
            MovePiece(Square.A8, Square.D8, pos)
        elif to_sq == Square.G8:
            MovePiece(Square.H8, Square.F8, pos)

    # 3. Hash out old en-passant and castling rights
    if pos.en_passant != Square.NO_SQ:
        HASH_EP(pos)
    HASH_CA(pos)

    # 4. Update rights/state and hash in new castling rights
    pos.castle_perm &= CastlePerm[from_sq]
    pos.castle_perm &= CastlePerm[to_sq]
    pos.en_passant = Square.NO_SQ
    HASH_CA(pos)

    # 5. Handle captures and move counters
    pos.fifty_move += 1
    captured = CAPTURED(move)
    if captured != Pieces.EMPTY:
        ClearPiece(to_sq, pos)
        pos.fifty_move = 0

    pos.his_ply += 1
    pos.ply += 1

    # 6. Pawn start sets en-passant target
    if PiecePawn[pos.pieces[from_sq]]:
        pos.fifty_move = 0
        if move & MFLAG_PS:
            if side == Side.WHITE:
                pos.en_passant = from_sq + 10
            else:
                pos.en_passant = from_sq - 10
            HASH_EP(pos)

    # 7. Move the piece and handle promotion replacement
    MovePiece(from_sq, to_sq, pos)

    promoted = PROMOTED(move)
    if promoted != Pieces.EMPTY:
        ClearPiece(to_sq, pos)
        AddPiece(to_sq, pos, promoted)

    # 8. Switch side in board state and hash
    pos.side ^= 1
    HASH_SIDE(pos)

    # 9. Reject illegal move if mover king is attacked
    if pos.is_sq_attacked(pos.king_sq[side], pos.side):
        TakeMove(pos)
        return False

    assert pos.check_board()
    return True

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

# def MakeMove(pos, move):
#     from_sq = FROMSQ(move)
#     to_sq = TOSQ(move)
#     side = pos.side
    
#     # 1. Store current state in history for TakeMove
#     pos.history[pos.his_ply].pos_key = pos.pos_key
    
#     # 2. Handle En Passant Capture
#     if move & MFLAG_EP:
#         if side == Side.WHITE:
#             ClearPiece(to_sq - 10, pos)
#         else:
#             ClearPiece(to_sq + 10, pos)
            
#     # 3. Handle Castling
#     elif move & MFLAG_CA:
#         if to_sq == Square.C1: MovePiece(Square.A1, Square.D1, pos)
#         elif to_sq == Square.G1: MovePiece(Square.H1, Square.F1, pos)
#         elif to_sq == Square.C8: MovePiece(Square.A8, Square.D8, pos)
#         elif to_sq == Square.G8: MovePiece(Square.H8, Square.F8, pos)

#     # 4. Hash out current state
#     if pos.en_passant != Square.NO_SQ: HASH_EP(pos)
#     HASH_CA(pos) # Hash out old permissions
    
#     # Update history and permissions
#     pos.history[pos.his_ply].move = move
#     pos.history[pos.his_ply].fifty_move = pos.fifty_move
#     pos.history[pos.his_ply].en_passant = pos.en_passant
#     pos.history[pos.his_ply].castle_perm = pos.castle_perm
    
#     pos.castle_perm &= CastlePerm[from_sq]
#     pos.castle_perm &= CastlePerm[to_sq]
#     pos.en_passant = Square.NO_SQ
    
#     HASH_CA(pos) # Hash in NEW permissions
    
#     # 5. Handle Standard Captures
#     pos.fifty_move += 1
#     captured = CAPTURED(move)
#     if captured != Pieces.EMPTY:
#         ClearPiece(to_sq, pos)
#         pos.fifty_move = 0
        
#     pos.his_ply += 1
#     pos.ply += 1
    
#     # 6. Set new En Passant square if pawn double-moved
#     if PiecePawn[pos.pieces[from_sq]]:
#         pos.fifty_move = 0
#         if move & MFLAG_PS:
#             if side == Side.WHITE:
#                 pos.en_passant = from_sq + 10
#             else:
#                 pos.en_passant = from_sq - 10
#             HASH_EP(pos)
            
#     # 7. Move the piece and handle promotions
#     MovePiece(from_sq, to_sq, pos)
    
#     prom_pce = PROMOTED(move)
#     if prom_pce != Pieces.EMPTY:
#         ClearPiece(to_sq, pos)
#         AddPiece(to_sq, pos, prom_pce)
        
# # make_mov.py (Step 8)

#     # Switch side and hash it
#     HASH_SIDE(pos)
#     pos.side ^= 1
    
#     # Check if the move was legal (King not under attack)
#     # 'side' is the side that just moved
#     if pos.is_sq_attacked(pos.king_sq[side], pos.side):
#         # IMPORTANT: You MUST call TakeMove to restore the board and the key 
#         # before returning False, or the next move in your loop will fail!
#         TakeMove(pos)
#         return False
        
#     return True

# def MakeMove(pos, move):
#     from_sq = FROMSQ(move)
#     to_sq = TOSQ(move)
#     side = pos.side

#     # 1. Store current state for TakeMove
#     pos.history[pos.his_ply].pos_key = pos.pos_key
#     pos.history[pos.his_ply].move = move
#     pos.history[pos.his_ply].fifty_move = pos.fifty_move
#     pos.history[pos.his_ply].en_passant = pos.en_passant
#     pos.history[pos.his_ply].castle_perm = pos.castle_perm

#     # 2. Handle en-passant capture
#     if move & MFLAG_EP:
#         if side == Side.WHITE:
#             ClearPiece(to_sq - 10, pos)
#         else:
#             ClearPiece(to_sq + 10, pos)

#     # 3. Handle castling rook move
#     elif move & MFLAG_CA:
#         if to_sq == Square.C1:
#             MovePiece(Square.A1, Square.D1, pos)
#         elif to_sq == Square.G1:
#             MovePiece(Square.H1, Square.F1, pos)
#         elif to_sq == Square.C8:
#             MovePiece(Square.A8, Square.D8, pos)
#         elif to_sq == Square.G8:
#             MovePiece(Square.H8, Square.F8, pos)

#     # 4. Hash out en-passant and castling
#     if pos.en_passant != Square.NO_SQ:
#         HASH_EP(pos)
#     HASH_CA(pos)

#     # 5. Update castling rights
#     pos.castle_perm &= CastlePerm[from_sq]
#     pos.castle_perm &= CastlePerm[to_sq]
#     pos.en_passant = Square.NO_SQ

#     HASH_CA(pos)

#     # 6. Handle captures
#     pos.fifty_move += 1
#     captured = CAPTURED(move)
#     if captured != Pieces.EMPTY:
#         ClearPiece(to_sq, pos)
#         pos.fifty_move = 0

#     pos.his_ply += 1
#     pos.ply += 1

#     # 7. Pawn double move → set en-passant
#     if PiecePawn[pos.pieces[from_sq]]:
#         pos.fifty_move = 0
#         if move & MFLAG_PS:
#             if side == Side.WHITE:
#                 pos.en_passant = from_sq + 10
#             else:
#                 pos.en_passant = from_sq - 10
#             HASH_EP(pos)

#     # 8. Move the piece
#     MovePiece(from_sq, to_sq, pos)

#     # 9. Handle promotion
#     promoted = PROMOTED(move)
#     if promoted != Pieces.EMPTY:
#         ClearPiece(to_sq, pos)
#         AddPiece(to_sq, pos, promoted)

#     # 10. Switch side
#     HASH_SIDE(pos)
#     pos.side ^= 1

#     # 11. Illegal move check (king in check)
#     if pos.is_sq_attacked(pos.king_sq[side], pos.side):
#         TakeMove(pos)
#         return False

#     return True

def MovePiece(from_sq, to_sq, pos):
    """
    Move a piece on the board from `from_sq` to `to_sq`.
    This updates:
      - pos.pieces[]
      - incremental Zobrist hash via HASH_PCE
      - pawn bitboards (pos.pawns)
      - piece list (pos.p_list & pos.pce_num)
      - king_sq for kings
    It does NOT handle captures/promotions (ClearPiece/AddPiece handle those).
    """
    assert SqOnBoard(from_sq)
    assert SqOnBoard(to_sq)

    pce = pos.pieces[from_sq]
    col = PieceCol[pce]

    # 1) XOR piece out of the old square and remove it
    HASH_PCE(pce, from_sq, pos)
    pos.pieces[from_sq] = Pieces.EMPTY

    # 2) XOR piece into the new square and set it
    HASH_PCE(pce, to_sq, pos)
    pos.pieces[to_sq] = pce

    # 3) If pawn, update pawn bitboards (and combined)
    if not PieceBig[pce]:
        f_sq64 = Sq120to64[from_sq]
        t_sq64 = Sq120to64[to_sq]

        # Clear old bit, set new bit for that colour
        pos.pawns[col] = clear_bit(pos.pawns[col], f_sq64)
        pos.pawns[col] = set_bit(pos.pawns[col], t_sq64)

        # Update BOTH pawns bitboard
        pos.pawns[Side.BOTH] = clear_bit(pos.pawns[Side.BOTH], f_sq64)
        pos.pawns[Side.BOTH] = set_bit(pos.pawns[Side.BOTH], t_sq64)

    # 4) Update piece list: find the piece entry for from_sq and set to_sq
    #    There must be an entry — sanity assert keeps things safe.
    found_index = -1
    for i in range(pos.pce_num[pce]):
        if pos.p_list[pce][i] == from_sq:
            found_index = i
            break

    assert found_index != -1
    pos.p_list[pce][found_index] = to_sq

    # 5) If king moved, update king tracker
    if pce == Pieces.wK:
        pos.king_sq[Side.WHITE] = to_sq
    elif pce == Pieces.bK:
        pos.king_sq[Side.BLACK] = to_sq

def TakeMove(pos):
    assert pos.check_board()

    # 1. Move the counters back
    pos.his_ply -= 1
    pos.ply -= 1
    
    move = pos.history[pos.his_ply].move
    from_sq = FROMSQ(move)
    to_sq = TOSQ(move)
    
    # ---------------------------------------------------------
    # PART A: REVERSE THE PHYSICAL BOARD
    # We use MovePiece/AddPiece/ClearPiece to move the pieces.
    # IMPORTANT: We ignore the fact that these corrupt the pos_key 
    # for a moment, because we will overwrite it at the end.
    # ---------------------------------------------------------
    
    # Handle En Passant
    if move & MFLAG_EP:
        if pos.side == Side.WHITE: # Side is still WHITE if BLACK just moved
            AddPiece(to_sq + 10, pos, Pieces.wP)
        else:
            AddPiece(to_sq - 10, pos, Pieces.bP)
            
    # Handle Castling
    elif move & MFLAG_CA:
        if to_sq == Square.C1: MovePiece(Square.D1, Square.A1, pos)
        elif to_sq == Square.G1: MovePiece(Square.F1, Square.H1, pos)
        elif to_sq == Square.C8: MovePiece(Square.D8, Square.A8, pos)
        elif to_sq == Square.G8: MovePiece(Square.F8, Square.H8, pos)

    # Move the piece that actually moved back to where it started
    MovePiece(to_sq, from_sq, pos)
    
    # Put captured pieces back
    captured = CAPTURED(move)
    if captured != Pieces.EMPTY:
        AddPiece(to_sq, pos, captured)
        
    # Reverse Promotions
    if PROMOTED(move) != Pieces.EMPTY:
        ClearPiece(from_sq, pos)
        # Put the pawn back (side depends on who just moved)
        # If it's currently Black's turn, White is the one who promoted
        pawn = Pieces.wP if pos.side == Side.BLACK else Pieces.bP
        AddPiece(from_sq, pos, pawn)

    # ---------------------------------------------------------
    # PART B: RESTORE THE PERFECT STATE
    # Now we overwrite everything, including the corrupted pos_key.
    # ---------------------------------------------------------
    pos.side ^= 1 # Flip side back physically
    
    # This overwrites the corruption caused by MovePiece/AddPiece above
    pos.castle_perm = pos.history[pos.his_ply].castle_perm
    pos.fifty_move = pos.history[pos.his_ply].fifty_move
    pos.en_passant = pos.history[pos.his_ply].en_passant
    pos.pos_key = pos.history[pos.his_ply].pos_key

    assert pos.check_board()

# def TakeMove(pos):
#     """Undoes the last move made on the board using the history array."""
#     # 1. Decrement counters first
#     pos.his_ply -= 1
#     pos.ply -= 1
    
#     # 2. Get the move info from history
#     move = pos.history[pos.his_ply].move
#     from_sq = FROMSQ(move)
#     to_sq = TOSQ(move)
    
#     # 3. Hash out current state
#     if pos.en_passant != Square.NO_SQ: HASH_EP(pos)
#     HASH_CA(pos)
    
#     # 4. Restore state from history
#     pos.castle_perm = pos.history[pos.his_ply].castle_perm
#     pos.fifty_move = pos.history[pos.his_ply].fifty_move
#     pos.en_passant = pos.history[pos.his_ply].en_passant
#     pos.pos_key = pos.history[pos.his_ply].pos_key
    
#     # 5. Hash new (restored) state back in
#     if pos.en_passant != Square.NO_SQ: HASH_EP(pos)
#     HASH_CA(pos)
    
#     # 6. Flip side back
#     pos.side ^= 1
#     HASH_SIDE(pos)
    
#     # 7. Handle special move types
#     if move & MFLAG_EP:
#         # If it was an En Passant capture, add the pawn back [00:01:51]
#         if pos.side == Side.WHITE:
#             AddPiece(to_sq - 10, pos, Pieces.bP)
#         else:
#             AddPiece(to_sq + 10, pos, Pieces.wP)
    
#     elif move & MFLAG_CA:
#         # Move the Rook back to its original square [00:02:11]
#         if to_sq == Square.C1: MovePiece(Square.D1, Square.A1, pos)
#         elif to_sq == Square.G1: MovePiece(Square.F1, Square.H1, pos)
#         elif to_sq == Square.C8: MovePiece(Square.D8, Square.A8, pos)
#         elif to_sq == Square.G8: MovePiece(Square.F8, Square.H8, pos)
        
#     # 8. Move the main piece back (From To_Sq back to From_Sq)
#     MovePiece(to_sq, from_sq, pos)
    
#     # 9. Handle captured pieces
#     captured = CAPTURED(move)
#     if captured != Pieces.EMPTY:
#         AddPiece(to_sq, pos, captured)
        
#     # 10. Handle promotions
#     # If we promoted, we currently have a Queen/Rook etc. on the From_Sq. 
#     # We must clear it and put the pawn back. [00:03:25]
#     if PROMOTED(move) != Pieces.EMPTY:
#         ClearPiece(from_sq, pos)
#         if pos.side == Side.WHITE:
#             AddPiece(from_sq, pos, Pieces.wP)
#         else:
#             AddPiece(from_sq, pos, Pieces.bP)


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
