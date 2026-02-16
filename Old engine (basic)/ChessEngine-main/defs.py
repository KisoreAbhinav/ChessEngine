# defs.py
from enum import IntEnum
from validate import *


def AllInit():
    init_sq120tosq64()
    from hashkeys import init_hash_keys
    init_hash_keys()
    from move_gen import InitMvvLva
    InitMvvLva()


U64 = int
# arbitrary precision
# instead of using unsigned long long int in C, we just define it, as python handles it


MAX_GAME_MOVES = 2048
# maximum number of moves (mostly engines use numbers between 1024 to 4096)
# these are half moves
# used to keep a track of the game, and use undos 
MAXDEPTH = 64


ENGINE_NAME = "Hydra 1.0"
# Name of the engine - can be anything but i am obsessed with Hydra so...


BOARD_SQ_NUM = 120
# Size of the board, including the actual chess board along with the excess squares to check for invalid positions 
# Prevents the flow of calculation to cross the board limits


class Pieces (IntEnum):
    EMPTY = 0

    wP = 1
    wN = 2
    wB = 3
    wR = 4
    wQ = 5
    wK = 6

    bP = 7
    bN = 8
    bB = 9
    bR = 10
    bQ = 11
    bK = 12
# Assigned values to the pieces so instead of using variables, we can just use the value of each piece to make these calculations simpler

    
class Ranks (IntEnum):
    RANK_1 = 0
    RANK_2 = 1
    RANK_3 = 2
    RANK_4 = 3
    RANK_5 = 4
    RANK_6 = 5
    RANK_7 = 6
    RANK_8 = 7
    RANK_NONE= 8
# defining each rank, with rank 1 being white's home square and 8 being black's.
# RANK_NONE here is used to calculate the overflow


class File (IntEnum):
    FILE_1 = 0
    FILE_2 = 1
    FILE_3 = 2
    FILE_4 = 3
    FILE_5 = 4
    FILE_6 = 5
    FILE_7 = 6
    FILE_8 = 7
    FILE_NONE= 8
#defining each file where file a = file 1 and so on, upto file h = 8
# FILE_NONE here is used to calculate the overflow


class Side(IntEnum):
    WHITE = 0
    BLACK = 1
    BOTH = 2
# teams definition
# BOTH will be used to check for total number of pieces, attacks, moves, etc
# Ex- if after a move, the condition says BOTH, means a piece was captured


class Square(IntEnum):
    A1 = 21; B1 = 22; C1 = 23; D1 = 24; E1 = 25; F1 = 26; G1 = 27; H1 = 28
    A2 = 31; B2 = 32; C2 = 33; D2 = 34; E2 = 35; F2 = 36; G2 = 37; H2 = 38
    A3 = 41; B3 = 42; C3 = 43; D3 = 44; E3 = 45; F3 = 46; G3 = 47; H3 = 48
    A4 = 51; B4 = 52; C4 = 53; D4 = 54; E4 = 55; F4 = 56; G4 = 57; H4 = 58
    A5 = 61; B5 = 62; C5 = 63; D5 = 64; E5 = 65; F5 = 66; G5 = 67; H5 = 68
    A6 = 71; B6 = 72; C6 = 73; D6 = 74; E6 = 75; F6 = 76; G6 = 77; H6 = 78
    A7 = 81; B7 = 82; C7 = 83; D7 = 84; E7 = 85; F7 = 86; G7 = 87; H7 = 88
    A8 = 91; B8 = 92; C8 = 93; D8 = 94; E8 = 95; F8 = 96; G8 = 97; H8 = 98

    NO_SQ = 99
# defining the entire board of operation
# NO_SQ is used for calculations of stuff like out of board, en-passant etc
NO_SQ = Square.NO_SQ

class Castling(IntEnum):
    WKSC = 1
    WQSC = 2
    BKSC = 4
    BQSC = 8
# used to bitmask and store the possibility of castling of both sides in a single integer
# these are in powers of 2, represented by a 4 bit number
# 1 = 0001, 2 = 0010, 4 = 0100, 8 = 1000
# so if the white king can castle king side and the black king can castle queen side, the options are WKSC | BKQS so 0001 | 1000 = 1001
# hence all the possibilities are stored in a single 4 bit number



class Undo:
    __slots__ = ("move", "castle_perm", "en_passant", "fifty_move", "pos_key")
    def __init__(self, move=0, castle_perm=0, en_passant=0, fifty_move=0, pos_key=0):
        self.move = move
        self.castle_perm = castle_perm
        self.en_passant = en_passant
        self.fifty_move = fifty_move
        self.pos_key = pos_key
# move -> stores the move just before the current ongoing one
# castle_perm -> stores the castle permission status for both white and black kings on the move right before the ongoing one
# en_passant -> stores the status of the en_passant squares that are possible due to the previous move
# fifty_move -> stores the counter of the 50 move rule; reset by every pawn push or piece captures
# pos_key -> the Zobrist hash key that of the attributes of the board of the previous move
    
class Move:
    def __init__(self):
        self.move = 0   # The 32-bit integer that will hold all move info
        self.score = 0  # An integer used for move ordering (sorting)


class SearchInfo:
    __slots__ = (
        "start_time",
        "stop_time",
        "depth",
        "depth_set",
        "time_set",
        "moves_to_go",
        "infinite",
        "nodes",
        "quit",
        "stopped",
        "fh",
        "fhf",
        "stdin_enabled",
        "stdin_buffer",
    )

    def __init__(self):
        self.start_time = 0
        self.stop_time = 0
        self.depth = 0
        self.depth_set = 0
        self.time_set = 0
        self.moves_to_go = 0
        self.infinite = 0
        self.nodes = 0
        self.quit = 0
        self.stopped = 0
        self.fh = 0.0
        self.fhf = 0.0
        self.stdin_enabled = 1
        self.stdin_buffer = ""


#--------------------------------------------------------------------------------------------------
# Look Up Tables
#--------------------------------------------------------------------------------------------------

Sq120to64 = [0] * BOARD_SQ_NUM
Sq64to120 = [0] * 64

FilesBoard = [0]*BOARD_SQ_NUM
RanksBoard = [0]*BOARD_SQ_NUM

def FR2SQ(f, r):
    return (21 + (f) + (r)*10)

def Sq120(sq120):
    return Sq120to64[sq120]


KnDir = [-8, -19, -21, -12, 8, 19, 21, 12]
RkDir = [-1, -10, 1, 10]
BiDir = [-9, -11, 11, 9]
KiDir = [-1, -10, 1, 10, -9, -11, 11, 9]

PceKnight = [False, False, True, False, False, False, False, False, True, False, False, False, False]
PceKing = [False, False, False, False, False, False, True, False, False, False, False, False, True]
PceRookQueen = [False, False, False, False, True, True, False, False, False, False, True, True, False]
PceBishopQueen = [False, False, False, True, False, True, False, False, False, True, False, True, False]


FROMSQ_MASK     = 0x7F        # 7 bits
TOSQ_MASK       = 0x7F << 7   # 7 bits shifted
CAPTURED_MASK   = 0xF << 14   # 4 bits shifted
EP_FLAG         = 0x40000     # bit 18 (1 << 18)
PAWN_START_FLAG = 0x80000     # bit 19 (1 << 19)
PROMOTED_MASK   = 0xF << 20   # 4 bits shifted
CASTLE_FLAG     = 0x1000000   # bit 24 (1 << 24)

# Unpacking functions
def FROMSQ(m):     return (m & 0x7F)
def TOSQ(m):       return ((m >> 7) & 0x7F)
def CAPTURED(m):   return ((m >> 14) & 0xF)
def PROMOTED(m):   return ((m >> 20) & 0xF)

# Packing function
def MOVE(f, t, ca, pro, fl):    return (f) | (t << 7) | (ca << 14) | (pro << 20) | (fl)

# Flag Constants
MFLAG_EP = 0x40000         # En Passant
MFLAG_PS = 0x80000         # Pawn Start
MFLAG_CA = 0x1000000       # Castling

# Special Check Masks
# These allow us to quickly check if ANY capture or ANY promotion happened
MFLAG_CAP = 0x7C000        # Includes EP and Captured bits
MFLAG_PRO = 0xF00000       # Any Promotion

# Number of directions for each piece: [EMPTY, wP, wN, wB, wR, wQ, wK, bP, bN, bB, bR, bQ, bK]
NumDir = [ 0, 0, 8, 4, 4, 8, 8, 0, 8, 4, 4, 8, 8 ]

# Direction offsets for each piece type
PceDir = [
    [0, 0, 0, 0, 0, 0, 0, 0], # EMPTY
    [0, 0, 0, 0, 0, 0, 0, 0], # wP (handled separately)
    [-8, -19, -21, -12, 8, 19, 21, 12], # wN (Knight)
    [-9, -11, 11, 9, 0, 0, 0, 0], # wB
    [-1, -10, 1, 10, 0, 0, 0, 0], # wR
    [-1, -10, 1, 10, -9, -11, 11, 9], # wQ
    [-1, -10, 1, 10, -9, -11, 11, 9], # wK
    [0, 0, 0, 0, 0, 0, 0, 0], # bP (handled separately)
    [-8, -19, -21, -12, 8, 19, 21, 12], # bN
    [-9, -11, 11, 9, 0, 0, 0, 0], # bB
    [-1, -10, 1, 10, 0, 0, 0, 0], # bR
    [-1, -10, 1, 10, -9, -11, 11, 9], # bQ
    [-1, -10, 1, 10, -9, -11, 11, 9]  # bK
]

PieceSlider = [ False, False, False, True, True, True, False, False, False, True, True, True, False ]

# PiecePawn array (True if the piece is a White or Black pawn)
PiecePawn = [False, True, False, False, False, False, False, True, False, False, False, False, False]


#--------------------------------------------------------------------------------------------------
# Board Constants/Conditions
#--------------------------------------------------------------------------------------------------
class Board:
    __slots__ = ("pieces", "pawns", "king_sq", "side", 
                 "en_passant", "fifty_move", "ply", 
                 "his_ply", "pos_key", "pce_num", "big_pce", 
                 "maj_pce", "min_pce", "castle_perm", "history", "p_list",
                 "material", "pv_table", "pv_array",
                 "search_history", "search_killers")

    def __init__(self):
        self.pieces = [Pieces.EMPTY] * BOARD_SQ_NUM 
        #creates a list of empty squares in the size of the board

        self.pawns = [0, 0, 0]
        # bit board for all the pawns, white, black and both
        
        self.king_sq = [Square.NO_SQ, Square.NO_SQ]
        # initializes squares for the white and black king

        self.side = Side.WHITE
        # sets the first moving team/player as WHITE, as that is the standard rule, can be overridden by ParseFEN

        self.en_passant = Square.NO_SQ
        # sets the possibility of en-passant to 0, basically invalid

        self.fifty_move = 0
        # counter for a 50 move rule, if no pawns have been pushed and no pieces have been captured
    
        self.ply = 0
        # sets the current search depth to 0

        self.his_ply = 0
        # total half moves played so far, used for tracking actual game progress

        self.pos_key = 0
        # assigns each position obtained on a chess board to a Zobrist Hash key
        # set as 0 as no pieces have been setup yet
        # used for checking 3 fold repetitions

        self.pce_num = [0] * 13
        # stores the number of pieces on the board

        self.big_pce = [0, 0, 0]
        # stores the number of pieces other than pawns on the board for white, black and both

        self.maj_pce = [0, 0, 0]
        # stores the number of major pieces (rook and queens) on the board for white, black and both
        # used for material evaluation
        
        self.min_pce = [0, 0, 0]
        # stores the number of minor pieces (bishops, knights) on the board for white, black and both
        # used for positional calculation

        self.castle_perm = 0
        # stores the castle permissions for the king
        # since the board hasnt yet been initialized, there are no pieces that can castle
        # it stores '0000' -> no sides can castle
        # discussed in detail with the Class Castling   

        self.history = [Undo() for _ in range (MAX_GAME_MOVES)]
        # stores all the unique board positions and attributes of each move upto the maximum game moves, for this engine, set to 2048
        
        self.p_list = [[Square.NO_SQ for _ in range (10)] for _ in range (13)]
        # Total number of pieces including an empty square can be 13
        # At any given instance, the maximum number of piece of any type can be 10
        # Example - 2 rooks and all pawns promoted to rooks so 2 + 8 = 10

        self.material = [0,0,0]
        # White and Black's material Score

        from pvtable import PVTable, InitPvTable
        self.pv_table = PVTable()
        InitPvTable(self.pv_table)
        self.pv_array = [0] * MAXDEPTH
        self.search_history = [[0 for _ in range(120)] for _ in range(13)]
        self.search_killers = [[0 for _ in range(MAXDEPTH)] for _ in range(2)]


    def check_board(self):

        temp_pce_num = [0] * 13

        # Temporary arrays to match with the current board state
        t_pce_num = [0] * 13
        t_big_pce = [0] * 3  
        t_maj_pce = [0] * 3  
        t_min_pce = [0] * 3  
        t_material = [0] * 3
            
        # Temporary bitboards for pawns
        t_pawns = [0, 0, 0]



        for t_pce in [Pieces.wP, Pieces.wN, Pieces.wB, 
                     Pieces.wR, Pieces.wQ, Pieces.wK,
                     Pieces.bP, Pieces.bN, Pieces.bB, 
                     Pieces.bR, Pieces.bQ, Pieces.bK]:
           
           for j in range(self.pce_num[t_pce]):
               sq = self.p_list[t_pce][j]

               assert self.pieces[sq] == t_pce, f"Piece List mismatch at {sq}"


        for i in range(64):
            sq120 = Sq64to120[i]
            pce = self.pieces[sq120]
            if pce != Pieces.EMPTY:
                col = PieceCol[pce]
                
                t_pce_num[pce] += 1
                if PieceBig[pce]: t_big_pce[col] += 1
                if PieceMaj[pce]: t_maj_pce[col] += 1
                if PieceMin[pce]: t_min_pce[col] += 1
                t_material[col] += PieceVal[pce]
                
                # pawn bitboards for comparison
                if pce == Pieces.wP:
                    t_pawns[Side.WHITE] |= (1 << i)
                    t_pawns[Side.BOTH] |= (1 << i)
                elif pce == Pieces.bP:
                    t_pawns[Side.BLACK] |= (1 << i)
                    t_pawns[Side.BOTH] |= (1 << i)

        # Compare temporary results with the actual Board state
        for pce_type in range(Pieces.wP, Pieces.bK + 1):
            assert t_pce_num[pce_type] == self.pce_num[pce_type], f"Count mismatch for piece {pce_type}"

        assert t_material[Side.WHITE] == self.material[Side.WHITE], "White material mismatch"
        assert t_material[Side.BLACK] == self.material[Side.BLACK], "Black material mismatch"
        
        assert t_pawns[Side.WHITE] == self.pawns[Side.WHITE], "White pawn bitboard mismatch"
        assert t_pawns[Side.BLACK] == self.pawns[Side.BLACK], "Black pawn bitboard mismatch"
        assert t_pawns[Side.BOTH] == self.pawns[Side.BOTH], "Combined pawn bitboard mismatch"

        # verify the Hash Key 
        from hashkeys import generate_pos_key
        calc = generate_pos_key(self)
        if calc != self.pos_key:
            print(f"DEBUG PosKey mismatch!\n  computed: {calc:016X}\n  stored:   {self.pos_key:016X}\n  side: {self.side} (0=WHITE,1=BLACK)\n  en_passant: {self.en_passant}\n  castle_perm: {self.castle_perm}")
            raise AssertionError("PosKey mismatch - engine state is corrupted")
        # Side and King positions
        assert self.side in [Side.WHITE, Side.BLACK]
        assert self.pieces[self.king_sq[Side.WHITE]] == Pieces.wK
        assert self.pieces[self.king_sq[Side.BLACK]] == Pieces.bK

        return True


    def reset_board(self):

        for i in range(BOARD_SQ_NUM):
            self.pieces[i] = Square.NO_SQ 
            # setting all of the squares to OFFBOARD
            
        for i in range(64):
            self.pieces[Sq64to120[i]] = Pieces.EMPTY
            # setting the playable squares to empty from OFFBOARD
            # 21 to 98
            
       
        for i in range(13):
            self.pce_num[i] = 0
            
        for i in range(2):
            self.big_pce[i] = 0
            self.maj_pce[i] = 0
            self.min_pce[i] = 0
            self.material[i] = 0
        # Reset all the pieces and counts

        for i in range (3):
            self.pawns[i] = 0

            
        for i in range(13):
            for j in range(10):
                self.p_list[i][j] = Square.NO_SQ
                #clearing the piece list [type of piece and max of 10 pieces]
                
        # 5. Reset Kings and Game State
        self.king_sq = [Square.NO_SQ, Square.NO_SQ]
        self.side = Side.BOTH 
        # Setting to BOTH as a "null" state
        # hence when the board is set, if the side is still NULL, an illegal postion can be called using the checkboard function
        self.en_passant = Square.NO_SQ
        self.fifty_move = 0
        self.ply = 0
        self.his_ply = 0
        self.castle_perm = 0
        self.pos_key = 0


    def update_lists_material(self):
        for i in range(13):
            self.pce_num[i] = 0
        for i in range(3):
            self.big_pce[i] = 0
            self.maj_pce[i] = 0
            self.min_pce[i] = 0
            self.pawns[i] = 0 

        self.material = [0, 0, 0]
        
        for i in range(64):
            sq = Sq64to120[i]
            pce = self.pieces[sq]
            if pce != Pieces.EMPTY:
                col = PieceCol[pce]
                
                if col != Side.BOTH:
                    self.material[col] += PieceVal[pce]

                # helper arrays to increment counts
                if PieceBig[pce]: self.big_pce[col] += 1
                if PieceMaj[pce]: self.maj_pce[col] += 1
                if PieceMin[pce]: self.min_pce[col] += 1
                
                #updates the pawn bitboards
                if pce == Pieces.wP:
                    self.pawns[Side.WHITE] |= (1 << i)
                    self.pawns[Side.BOTH] |= (1 << i)
                elif pce == Pieces.bP:
                    self.pawns[Side.BLACK] |= (1 << i)
                    self.pawns[Side.BOTH] |= (1 << i)

                # Update Piece List: self.p_list[piece_type][index_of_that_piece] = square
                self.p_list[pce][self.pce_num[pce]] = sq
                self.pce_num[pce] += 1
                
                #Tracks kings
                if pce == Pieces.wK: self.king_sq[Side.WHITE] = sq
                if pce == Pieces.bK: self.king_sq[Side.BLACK] = sq

    def parse_fen(self, fen):
        self.reset_board()
        
        piece_map = {
            'P': Pieces.wP, 'N': Pieces.wN, 'B': Pieces.wB, 
            'R': Pieces.wR, 'Q': Pieces.wQ, 'K': Pieces.wK,
            'p': Pieces.bP, 'n': Pieces.bN, 'b': Pieces.bB, 
            'r': Pieces.bR, 'q': Pieces.bQ, 'k': Pieces.bK
        }
        # based on the way FEN works, we map our variables with the one in the notation

        
        tokens = fen.split()
        placement = tokens[0]
        side_to_move = tokens[1]
        castling = tokens[2]
        en_passant = tokens[3]
        #split the fen token using FEN rules

        # Extraction of the Data from the FEN string
        rank = Ranks.RANK_8
        file = File.FILE_1

        for char in placement:
            if char == '/':
                rank -= 1
                file = File.FILE_1
            elif char.isdigit():
                file += int(char)
            else:
                piece = piece_map[char]
                sq120 = FR2SQ(file, rank)
                self.pieces[sq120] = piece
                file += 1

        # Get Side to Move
        self.side = Side.WHITE if side_to_move == 'w' else Side.BLACK

        # Get Castling Permissions
        for char in castling:
            if char == 'K': self.castle_perm |= Castling.WKSC
            if char == 'Q': self.castle_perm |= Castling.WQSC
            if char == 'k': self.castle_perm |= Castling.BKSC
            if char == 'q': self.castle_perm |= Castling.BQSC

        # Get En Passant Square
        if en_passant != '-':
            f = ord(en_passant[0]) - ord('a')
            r = int(en_passant[1]) - 1
            self.en_passant = FR2SQ(f, r)

        
        self.update_lists_material()

        # Generating a unique position key using the hashkeys function
        from hashkeys import generate_pos_key
        self.pos_key = generate_pos_key(self)

    
    def print_board(self):
        print("\nGame Board:")
        pce_char = ".PNBRQKpnbrqk"
        side_char = "wb-"
        
        for rank in range(Ranks.RANK_8, Ranks.RANK_1 - 1, -1):
            line = f"{rank + 1}  " # Print rank number
            for file in range(File.FILE_1, File.FILE_8 + 1):
                sq = FR2SQ(file, rank)
                pce = self.pieces[sq]

                line += f"{pce_char[pce]:>3}" 
            print(line)
            
        print("\n     a  b  c  d  e  f  g  h")
        
        print(f"Side: {side_char[self.side]}")
        print(f"EnPassant: {self.en_passant}") # Printed as decimal (99 = No Sq)
        
        # Castling Logic: Check bits and print letter or dash
        c = self.castle_perm
        ksc = 'K' if c & Castling.WKSC else '-'
        qsc = 'Q' if c & Castling.WQSC else '-'
        bksc = 'k' if c & Castling.BKSC else '-'
        bqsc = 'q' if c & Castling.BQSC else '-'
        print(f"Castle: {ksc}{qsc}{bksc}{bqsc}")
        
        print(f"PosKey: {self.pos_key:X}")

    # def print_board(self):
    #     print("\nGame Board:")
    #     pce_char = ".PNBRQKpnbrqk"
        
    #     for rank in range(Ranks.RANK_8, Ranks.RANK_1 - 1, -1):
    #         line = f"{rank + 1}  "
    #         for file in range(File.FILE_1, File.FILE_8 + 1):
    #             sq = FR2SQ(file, rank)
    #             pce = self.pieces[sq]
    #             line += f"{pce_char[pce]} "
    #         print(line)
            
    #     print("   a b c d e f g h")
    #     print(f"Side: {'white' if self.side == Side.WHITE else 'black'}")
    #     print(f"EnPassant: {self.en_passant}")
    #     print(f"Castle: {self.castle_perm:x}")
    #     print(f"PosKey: {self.pos_key:X}")


    def is_sq_attacked(self, sq, side):

        assert SqOnBoard(sq)
        assert SideValid(side)
        assert self.check_board()

        # pawns
        if side == Side.WHITE:
            if self.pieces[sq - 11] == Pieces.wP or self.pieces[sq - 9] == Pieces.wP:
                return True
        else:
            if self.pieces[sq + 11] == Pieces.bP or self.pieces[sq + 9] == Pieces.bP:
                return True

        # knights
        for direction in KnDir:
            pce = self.pieces[sq + direction]
            if pce != Square.NO_SQ and PceKnight[pce] and PieceCol[pce] == side:
                return True
        
        for direction in RkDir:
            t_sq = sq + direction
            pce = self.pieces[t_sq]
            while pce != Square.NO_SQ: # While not offboard
                if pce != Pieces.EMPTY:
                    if PceRookQueen[pce] and PieceCol[pce] == side:
                        return True
                    break 
                t_sq += direction
                pce = self.pieces[t_sq]

        # Bishops & Queens
        for direction in BiDir:
            t_sq = sq + direction
            pce = self.pieces[t_sq]
            while pce != Square.NO_SQ:
                if pce != Pieces.EMPTY:
                    if PceBishopQueen[pce] and PieceCol[pce] == side:
                        return True
                    break
                t_sq += direction
                pce = self.pieces[t_sq]

        # Kings
        for direction in KiDir:
            pce = self.pieces[sq + direction]
            if pce != Square.NO_SQ and PceKing[pce] and PieceCol[pce] == side:
                return True

        return False
    
# Class Board stores the board's attributes, lets say, its the opening, what pieces have moved, in what order, what pieces have been traded, etc etc 
# Stores basically a screenshot of a board at a current position



#--------------------------------------------------------------------------------------------------
# 120 board to 64 board
#--------------------------------------------------------------------------------------------------
def init_sq120tosq64():

    #First we setup fail conditions
    # This makes sure that the offboard conditions return a recognizable value
    # Here adding 65 to the mapping -> there are only 64 squares on a board, hence 65 is recognizable
    for index in range (BOARD_SQ_NUM):
        Sq120to64[index] = 65
        FilesBoard [index] = Square.NO_SQ  #NO_SQ is used as an OFFBOARD marker as discussed earlier
        RanksBoard [index] = Square.NO_SQ #NO_SQ is used as an OFFBOARD marker as discussed earlier

    for index in range (64):
        Sq64to120 [index] = 120
    
    # Looping through the valid 64 squares of the board
    sq64 = 0
    for rank in range (Ranks.RANK_1, Ranks.RANK_8+1):
        for file in range (File.FILE_1, File.FILE_8+1):
            sq120 = FR2SQ(file, rank)

            # Linking the 2 arrays
            Sq64to120[sq64] = sq120
            Sq120to64[sq120] = sq64

            #Setting the Rank and File arrays
            FilesBoard[sq120] = file
            RanksBoard[sq120] = rank

            sq64 += 1


# Material Calculation for FEN parsing
# [EMPTY, wP, wN, wB, wR, wQ, wK, bP, bN, bB, bR, bQ, bK]
# Kings are counted as Big and Major in Bluefever's implementation
PieceBig = [ False, False, True, True, True, True, True, False, True, True, True, True, True ]
PieceMaj = [ False, False, False, False, True, True, True, False, False, False, True, True, True ]
PieceMin = [ False, False, True, True, False, False, False, False, True, True, False, False, False ]
PieceVal = [ 0, 100, 325, 325, 550, 1000, 50000, 100, 325, 325, 550, 1000, 50000 ]
PieceCol = [ Side.BOTH, Side.WHITE, Side.WHITE, Side.WHITE, Side.WHITE, Side.WHITE, Side.WHITE,
             Side.BLACK, Side.BLACK, Side.BLACK, Side.BLACK, Side.BLACK, Side.BLACK ]


# BIT BOARDS
#
#
#

def print_bitboard(bitboard: int):

    for rank in range(Ranks.RANK_8, Ranks.RANK_1 - 1, -1):
        line = f"{rank + 1}  " # Rank indicator
        for file in range(File.FILE_1, File.FILE_8 + 1):
            sq120 = FR2SQ(file, rank)
            sq64 = Sq120to64[sq120]

            if (1 << sq64) & bitboard:
                line += "X "
            else:
                line += "- "
        print(line)
        
    print("   a b c d e f g h\n")


BIT_TABLE = [
  0, 1, 48,  2, 57, 49, 28,  3,
  61, 58, 50, 42, 38, 29, 17,  4,
  62, 54, 59, 36, 51, 47, 43, 25,
  41, 22, 39, 32, 30, 13, 18,  5,
  63, 47, 55, 44, 60, 37, 52, 26,
  46, 24, 40, 33, 31, 14, 19,  6,
  56, 45, 53, 27, 46, 23, 34, 15,
  20,  7, 21, 35, 16,  8,  9, 10
]

def count_bits(b: int) -> int:

    r = 0
    while b:
        b &= (b - 1) # This clears the least significant bit
        r += 1
    return r

def pop_bit(bb: int) -> tuple[int, int]:

    if bb == 0:
        return -1, 0

    b = bb ^ (bb - 1)
    fold = ( (b & 0xffffffff) ^ (b >> 32) ) & 0xffffffff
    
    # Calculate index using the BitTable
    index = BIT_TABLE[( (fold * 0x783a9b23) & 0xffffffff ) >> 26]
    
    # Update the bitboard by clearing the LSB
    bb &= (bb - 1)
    
    return index, bb




