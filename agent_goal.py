# agent_goal.py - Goal-based agent for Azul-lite.
from collections import Counter
from pyswip import Prolog

COLORS = ["blue","yellow","red","black","white"]
ROW_CAP = {1:1,2:2,3:3,4:4,5:5}
FLOOR_PENALTIES = [-1,-1,-2,-2,-2,-3,-3]

class GoalAgent:
    def __init__(self, prolog: Prolog):
        self.prolog = prolog

    def _floor_penalty_for_overflow(self, current_floor_len: int, overflow: int) -> int:
        if overflow <= 0:
            return 0
        start = current_floor_len
        end = min(current_floor_len + overflow, len(FLOOR_PENALTIES))
        return sum(FLOOR_PENALTIES[start:end])

    def _prolog_score(self, wall, row, color):
        py_to_pl = "[" + ",".join("[" + ",".join(str(v) for v in r) + "]" for r in wall) + "]"
        col_res = list(self.prolog.query(f"wall_column_for({row}, '{color}', C)."))
        if not col_res:
            return 0
        sc_res = list(self.prolog.query(f"score_for_placement({py_to_pl}, {row}, '{color}', S)."))
        if not sc_res:
            return 0
        return int(sc_res[0]["S"])

    def _legal_wall_target(self, wall, row, color) -> bool:
        py_to_pl = "[" + ",".join("[" + ",".join(str(v) for v in r) + "]" for r in wall) + "]"
        list(self.prolog.query(f"legal_placement({row}, '{color}', {py_to_pl})."))
        return True

    def choose(self, game, pid: int):
        """Return best action tuple:
           ('F', factory_idx, color, row) or ('C', color, row)
           or None if no legal action exists.
        """
        player = game.players[pid]
        best_val, best_action = None, None

        # From factories
        for k, f in enumerate(game.factories):
            counts = Counter(f)
            for color, cnt in counts.items():
                for row in range(1,6):
                    line = player.pattern[row]
                    if line['color'] not in (None, color):
                        continue
                    try:
                        if not self._legal_wall_target(player.wall, row, color):
                            continue
                    except Exception:
                        continue
                    cap = ROW_CAP[row]
                    available = cap - line['count']
                    if available <= 0:
                        continue
                    to_line = min(available, cnt)
                    overflow = cnt - to_line
                    val = 0
                    val += to_line
                    if to_line == available and line['color'] in (None, color):
                        val += self._prolog_score(player.wall, row, color)
                    val += self._floor_penalty_for_overflow(len(player.floor), overflow)
                    if (best_val is None) or (val > best_val):
                        best_val = val
                        best_action = ('F', k, color, row)

        # From center
        from collections import Counter as C2
        center_counts = C2(game.center)
        for color, cnt in center_counts.items():
            for row in range(1,6):
                line = player.pattern[row]
                if line['color'] not in (None, color):
                    continue
                try:
                    if not self._legal_wall_target(player.wall, row, color):
                        continue
                except Exception:
                    continue
                cap = ROW_CAP[row]
                available = cap - line['count']
                if available <= 0:
                    continue
                to_line = min(available, cnt)
                overflow = cnt - to_line
                val = 0
                val += to_line
                if to_line == available and line['color'] in (None, color):
                    val += self._prolog_score(player.wall, row, color)
                val += self._floor_penalty_for_overflow(len(player.floor), overflow)
                if (best_val is None) or (val > best_val):
                    best_val = val
                    best_action = ('C', color, row)

        return best_action
