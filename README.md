# Hydra - The Chess-Engine
Chess Engine With Variable Playing Mechanisms and Learner's mode
[Mailboard based Python Chess Engine]

## Resources
https://talkchess.com/

https://www.chessprogramming.org/Main_Page

https://www.chessprogramming.org/Gerbil

https://www.chessprogramming.org/Robert_Hyatt

https://www.computerchess.org.uk/ccrl/4040/

https://www.tckerrigan.com/Chess/

http://www.open-aurec.com/wbforum/WinBoard/WinBoard4314.html

http://www.playwitharena.de/



## Files
defs.py - main definitions file; board constants, enums, board class, parsing, and shared engine structures.

hydra.py - terminal entry point; main menu, game flow, analysis options, learner output, and toggles.

search.py - core search logic (iterative deepening, alpha-beta, quiescence, move ordering, timing checks).

evaluate.py - static evaluation for positions (material + positional terms used by search).

move_gen.py - legal/pseudo-legal move generation and move scoring (captures, quiets, ordering hooks).

make_mov.py - make/unmake move logic; updates board state, hash, castling, en-passant, and legality checks.

move_io.py - move parsing/printing utilities (string to internal move and move to string).

hashkeys.py - Zobrist hashing key setup and position key generation.

pvtable.py - principal variation table helpers (store/probe/clear PV moves).

perft.py - perft test utilities for validating move generation and make/unmake correctness.

validate.py - assertion/sanity validation helpers used across board and move logic.

uci.py - UCI protocol loop and command parsing for GUI integration.

misc.py - utility helpers (timing/input helpers and other cross-cutting runtime helpers).

book.py - opening-book loader and book move selection logic.

openings.txt - opening book data used by book.py.

predictions.py - learner-guide move interpretation (plans, threats, tactical hints, counters).

persona_trace.py - humanized/adaptive personality move-selection layer and Elo adaptation behavior.

data.py - shared static data tables used by engine components.

Old engine (basic)/ - older baseline engine version kept for reference.



## Engine Working (End-to-End)

This section explains the full Hydra pipeline, from board setup to best-move output, including search, heuristics, UCI, and learner/personality layers.

### 1. Core Foundation Layer

defs.py is the foundation of the engine.
- Defines piece IDs, sides, ranks/files, square mapping (120 board + 64 board mapping tables), move bitmasks, and board-wide constants.
- Implements the Board structure that stores:
  - piece array
  - side to move
  - castling, en passant, fifty-move counter
  - piece lists / material counts
  - game history stack for takeback
  - PV/search helper arrays
- Provides board setup and validation (parse_fen, reset_board, check_board, is_sq_attacked).

hashkeys.py provides Zobrist hashing.
- Builds random keys for piece-square, side, castling, en-passant.
- Computes pos_key uniquely for the current position.
- Enables repetition detection, PV indexing, and transposition-style lookups.

validate.py provides assertion and safety helpers.
- Used to detect invalid board/move states during development and debugging.

### 2. Move Representation and Legality Layer

move_gen.py handles move generation.
- Generates pseudo-legal moves for all pieces.
- Handles special rules: castling, en passant, promotions.
- Includes move scoring hooks for ordering (captures, MVV-LVA, quiet move heuristics).

make_mov.py handles state transitions.
- MakeMove: applies a move to board state and updates all side effects.
- TakeMove: restores previous state from history stack.
- Ensures search can recurse safely through millions of positions.

move_io.py is the I/O bridge for moves.
- Converts text input like e2e4 into internal move integers.
- Converts internal move integer back to printable notation.

### 3. Position Evaluation Layer

evaluate.py scores static positions.
- Material balance plus positional signals.
- Piece-square table style terms.
- Returns score from side-to-move perspective (used by search leaf nodes and quiescence standing pat).

### 4. Search and Decision Layer

search.py is the engine brain.

Main flow:
1. SearchPosition / iterative deepening:
   - searches depth 1 -> N progressively.
   - keeps best-so-far move if time expires.
2. AlphaBeta (Negamax form):
   - recursive full-width search with pruning.
   - uses move ordering to maximize cutoffs.
3. Quiescence:
   - extends tactical lines (captures/checking tactical noise) at depth frontier.
   - reduces horizon-effect blunders.
4. terminal logic:
   - repetition draw
   - fifty-move draw
   - checkmate / stalemate detection
5. timing + interruption:
   - checks elapsed time and stop flags periodically.
6. search stats:
   - node count, fail-high metrics, depth completion.

### 5. Ordering, PV, and Speed Helpers

pvtable.py stores best move by pos_key bucket.
- StorePvMove, ProbePvTable, GetPvLine.
- Lets deeper iterations start with likely best line first.

move_gen.py + search.py together implement ordering strategy.
- Typical order:
  - PV move
  - captures (MVV-LVA)
  - killers
  - history heuristic quiet moves
- Better ordering = more beta cutoffs = deeper effective search.

perft.py validates move-gen/make-unmake correctness.
- Node-count verification against known test positions.
- Used to catch subtle legality/state corruption issues.

### 6. Opening and Personality Extensions

book.py + openings.txt implement opening book support.
- If enabled and position is covered, engine can play book move instantly.
- Saves time and improves opening quality.

persona_trace.py implements humanized/adaptive play behavior.
- Converts target Elo / personality controls into move-choice shaping.
- Can adapt strength during game based on user move quality.

### 7. Learner/Interpretation Layer

predictions.py explains ideas and tactical themes.
- Builds snapshots of own plans and opponent threats.
- Tracks changes after each move:
  - immediate move meaning
  - countered threats
  - remaining threats
  - current plans
- Includes tactical motifs like pressure, forks, open files, and pin-related warnings.

### 8. Interfaces and Runtime Modes

hydra.py is terminal mode orchestration.
- Displays menu.
- Runs analysis mode, play mode, humanized bot mode.
- Prints board/eval/PV/results and learner feedback.
- Toggles opening book and learner guide.

uci.py is GUI protocol mode.
- Implements UCI loop commands like:
  - uci
  - isready
  - position
  - go
  - stop
  - quit
- Allows Hydra to connect to Arena/Fritz/etc.

misc.py contains utility runtime helpers.
- timing helpers
- input/tick checks used by search control

data.py holds shared data tables used across modules.

---

## Engine Workflow (Phase-by-Phase)

### A) Program Start
1. hydra.py starts.
2. AllInit() (from defs.py) initializes board mapping, hash keys, and move-order tables.
3. Opening book is loaded (book.py) if configured.
4. User chooses terminal mode or UCI mode flow (depending on entry path).

### B) Position Setup
1. Position comes from:
   - FEN input (terminal), or
   - UCI position command (uci.py).
2. Board.parse_fen() creates full internal position.
3. Material lists, king squares, hash key, and rights are updated.

### C) Move Search
1. search.py receives position + depth/time constraints.
2. ClearForSearch-style reset of search stats/heuristics.
3. Iterative deepening loop starts.
4. For each depth:
   - call AlphaBeta.
   - inside each node:
     - draw/terminal checks
     - generate moves (move_gen.py)
     - order moves
     - MakeMove / recurse / TakeMove
     - prune using alpha-beta
   - if depth reaches 0 -> Quiescence + evaluate.py.
5. Best move and PV are returned.

### D) Output and Explanation
1. hydra.py prints:
   - best move
   - score
   - depth/nodes
   - principal variation
2. If learner mode is on:
   - predictions.py explains move intent and tactical/strategic effects.
3. In play modes:
   - move is applied
   - loop continues until terminal result.

### E) GUI Path (UCI)
1. GUI sends position ....
2. GUI sends go ... with depth/time controls.
3. Engine searches and outputs:
   - info ...
   - bestmove ...
4. stop/quit can interrupt and exit cleanly.

---


## Quick Phase-to-File Map

- Initialization phase: defs.py, hashkeys.py, move_gen.py
- Position ingest phase: defs.py, move_io.py, uci.py
- Search phase: search.py, move_gen.py, make_mov.py, evaluate.py, pvtable.py
- Validation/debug phase: perft.py, validate.py, defs.py (check_board)
- UX/interaction phase: hydra.py, uci.py
- Extension phase: book.py, persona_trace.py, predictions.py

