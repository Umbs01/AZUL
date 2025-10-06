# agents.py - Multiple AI agents for Azul-lite (with optional visualization hooks)
from collections import Counter
from pyswip import Prolog

COLORS = ["blue","yellow","red","black","white"]
ROW_CAP = {1:1,2:2,3:3,4:4,5:5}
FLOOR_PENALTIES = [-1,-1,-2,-2,-2,-3,-3]

def _floor_penalty_for_overflow(current_floor_len: int, overflow: int) -> int:
    if overflow <= 0:
        return 0
    start = current_floor_len
    end = min(current_floor_len + overflow, len(FLOOR_PENALTIES))
    return sum(FLOOR_PENALTIES[start:end])

def _prolog_score(prolog: Prolog, wall, row, color):
    py_to_pl = "[" + ",".join("[" + ",".join(str(v) for v in r) + "]" for r in wall) + "]"
    col_res = list(prolog.query(f"wall_column_for({row}, '{color}', C)."))
    if not col_res:
        return 0
    sc_res = list(prolog.query(f"score_for_placement({py_to_pl}, {row}, '{color}', S)."))
    if not sc_res:
        return 0
    return int(sc_res[0]["S"])

def _legal_wall_target(prolog: Prolog, wall, row, color) -> bool:
    py_to_pl = "[" + ",".join("[" + ",".join(str(v) for v in r) + "]" for r in wall) + "]"
    list(prolog.query(f"legal_placement({row}, '{color}', {py_to_pl})."))
    return True

def _summarize_state(game, pid):
    p = game.players[pid]
    lines = []
    for r in range(1,6):
        line = p.pattern[r]
        lines.append(f"r{r}:{line['color'] or '-'}{line['count']}")
    return " | ".join(lines)

def _format_action(a):
    if a[0] == 'F':
        _, k, color, row = a
        return f"F{k}:{color}->r{row}"
    else:
        _, color, row = a
        return f"C:{color}->r{row}"

class _BaseAgent:
    name = "base"
    def __init__(self, prolog: Prolog, visualizer=None, viz_idx=None):
        self.prolog = prolog
        self.visualizer = visualizer
        self.viz_idx = viz_idx  # tab index

    def _emit(self, root, actions, chosen_idx):
        if self.visualizer is not None and self.viz_idx is not None:
            self.visualizer.reset(self.viz_idx, f"{self.name}")
            self.visualizer.draw_tree(
                self.viz_idx,
                root_label=root,
                child_labels=[_format_action(a) for a in actions],
                chosen_index=chosen_idx
            )

class RandomAgent(_BaseAgent):
    name = "random"
    def choose(self, game, pid: int):
        # Collect all legal actions
        actions = []
        player = game.players[pid]
        for k, f in enumerate(game.factories):
            counts = Counter(f)
            for color, cnt in counts.items():
                for row in range(1,6):
                    line = player.pattern[row]
                    if line["color"] not in (None, color):
                        continue
                    try:
                        _legal_wall_target(self.prolog, player.wall, row, color)
                    except Exception:
                        continue
                    actions.append(('F', k, color, row))
        center_counts = Counter(game.center)
        for color, cnt in center_counts.items():
            for row in range(1,6):
                line = player.pattern[row]
                if line["color"] not in (None, color):
                    continue
                try:
                    _legal_wall_target(self.prolog, player.wall, row, color)
                except Exception:
                    continue
                actions.append(('C', color, row))

        if not actions:
            self._emit(_summarize_state(game, pid), [], None)
            return None

        import random
        idx = random.randrange(len(actions))
        self._emit(_summarize_state(game, pid), actions, idx)
        return actions[idx]

class GreedyAgent(_BaseAgent):
    name = "greedy"
    def choose(self, game, pid: int):
        player = game.players[pid]
        candidates = []
        # factories
        for k, f in enumerate(game.factories):
            counts = Counter(f)
            for color, cnt in counts.items():
                for row in range(1,6):
                    line = player.pattern[row]
                    if line["color"] not in (None, color):
                        continue
                    try:
                        _legal_wall_target(self.prolog, player.wall, row, color)
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
                        val += _prolog_score(self.prolog, player.wall, row, color)
                    val += _floor_penalty_for_overflow(len(player.floor), overflow)
                    candidates.append((('F', k, color, row), val))
        # center
        center_counts = Counter(game.center)
        for color, cnt in center_counts.items():
            for row in range(1,6):
                line = player.pattern[row]
                if line['color'] not in (None, color):
                    continue
                try:
                    _legal_wall_target(self.prolog, player.wall, row, color)
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
                    val += _prolog_score(self.prolog, player.wall, row, color)
                val += _floor_penalty_for_overflow(len(player.floor), overflow)
                candidates.append((('C', color, row), val))

        if not candidates:
            self._emit(_summarize_state(game, pid), [], None)
            return None

        candidates.sort(key=lambda x: x[1], reverse=True)
        actions = [c[0] for c in candidates]
        best_idx = 0
        self._emit(_summarize_state(game, pid), actions, best_idx)
        return actions[best_idx]

class MiniMaxAgent(_BaseAgent):
    name = "minimax"
    def __init__(self, prolog: Prolog, depth: int = 2, visualizer=None, viz_idx=None):
        super().__init__(prolog, visualizer, viz_idx)
        self.depth = depth

    def evaluate(self, game, pid):
        my = game.players[pid].score
        others = [p.score for i,p in enumerate(game.players) if i != pid]
        return my - (max(others) if others else 0)

    def _legal_actions(self, game, pid):
        player = game.players[pid]
        acts = []
        for k, f in enumerate(game.factories):
            counts = Counter(f)
            for color, cnt in counts.items():
                for row in range(1,6):
                    line = player.pattern[row]
                    if line["color"] not in (None, color):
                        continue
                    try:
                        _legal_wall_target(self.prolog, player.wall, row, color)
                    except Exception:
                        continue
                    acts.append(('F', k, color, row))
        center_counts = Counter(game.center)
        for color, cnt in center_counts.items():
            for row in range(1,6):
                line = player.pattern[row]
                if line['color'] not in (None, color):
                    continue
                try:
                    _legal_wall_target(self.prolog, player.wall, row, color)
                except Exception:
                    continue
                acts.append(('C', color, row))
        return acts

    def choose(self, game, pid: int):
        actions = self._legal_actions(game, pid)
        if not actions:
            self._emit(_summarize_state(game, pid), [], None)
            return None
        best_val, best_idx = None, None
        from copy import deepcopy
        for i, a in enumerate(actions[:12]):
            clone = deepcopy(game)
            clone.apply_action(pid, a)
            v = self.evaluate(clone, pid)  # shallow (kept small for speed)
            if best_val is None or v > best_val:
                best_val, best_idx = v, i
        self._emit(_summarize_state(game, pid), actions, best_idx)
        return actions[best_idx]

class GreedyAgent:
    def __init__(self, prolog, visualizer=None):
        self.prolog = prolog
        self.visualizer = visualizer
        self.name = "Greedy"

    def choose(self, game, pid):
        candidates = self.get_candidate_moves(game, pid)

        # 🔹 Draw the reasoning with Turtle
        if self.visualizer:
            self.visualizer.reset()
            self.visualizer.draw_state("Start", 0, 100, "blue")
            for i, move in enumerate(candidates):
                color = "green" if self.is_valid(move) else "red"
                self.visualizer.draw_state(str(move), i*80-100, 0, color)

        return self.pick_best(candidates)
