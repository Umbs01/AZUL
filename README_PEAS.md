# PEAS for Azul-lite (Goal-Based Agent)

## Performance measure (P)
- Win the game (highest final score).
- Maximize points gained per round (tile placement chains).
- Minimize floor penalties and wasted overflow.
- Secondary: prioritize completing rows/columns/color-sets for future bonuses.

## Environment (E)
- Fully observable, deterministic, discrete, sequential.
- Two-player turn-taking.
- State:
  - Factories (5 for 2P), each with up to 4 tiles.
  - Center pool.
  - Bag + discard (hidden composition but draw uniform when refilled).
  - Each player’s pattern lines (row capacity 1..5, chosen color, count).
  - Each player’s wall (5×5, 0/1 occupied according to standard pattern).
  - Score, floor line.

Prolog (SWI) encodes legality and scoring based on the canonical wall pattern.

## Actuators (A)
- Action schema = (source, color, row):
  - `take_from_factory(factory_idx, color, row)`
  - `take_from_center(color, row)`

## Sensors (S)
- Full game state visible each turn:
  - Factories / center contents, current pattern lines and wall for both players, score and floor.
  - Prolog answers:
    - `legal_placement(Row, Color, Grid)`
    - `score_for_placement(Grid, Row, Color, Score)`
    - `wall_column_for(Row, Color, Col)`

---

# Goal-Based Agent Design

We implement a **myopic (1-ply) goal-based agent** that chooses the action maximizing a heuristic utility:

**Heuristic(action | state)** =
1. **Line fill value**: number of tiles that will be added to the chosen pattern line.
2. **Immediate placement value**: if the line becomes *complete* by this action, request `score_for_placement/4` from Prolog to estimate the points that will be scored at end-of-round when this tile moves to the wall.
3. **Penalty estimate**: subtract floor penalty for any overflow tiles sent to floor (uses the standard first-7 penalty schedule).

This is *not* a full game-tree search; it’s a practical greedy policy that plays reasonably and is easy to compute every turn.

You can extend it to a deeper **minimax** (or **MCTS**) that:
- Generates successor states after opponents’ best replies.
- Uses the Prolog scoring predicates as a high-fidelity evaluation function for frontier states.
