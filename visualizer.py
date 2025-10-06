# visualizer.py
import threading
import tkinter as tk
from tkinter import ttk
import queue
import turtle
import time

class _AgentTab:
    def __init__(self, parent, title):
        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text=title)
        self.canvas = tk.Canvas(self.frame, width=520, height=420)
        self.canvas.pack(fill="both", expand=True)
        self.screen = turtle.TurtleScreen(self.canvas)
        self.screen.tracer(0, 0)
        self.t = turtle.RawTurtle(self.screen)
        self.t.hideturtle()
        self.t.speed(0)

    def clear(self):
        self.screen.clearscreen()
        self.screen.tracer(0, 0)
        self.t = turtle.RawTurtle(self.screen)
        self.t.hideturtle()
        self.t.speed(0)

    def node(self, x, y, label, color="black", r=16):
        pen = turtle.RawTurtle(self.screen); pen.hideturtle(); pen.speed(0); pen.penup()
        pen.goto(x, y - r); pen.pendown()
        pen.pensize(2); pen.color(color)
        pen.circle(r)
        pen.penup(); pen.goto(x, y - 5)
        pen.write(label, align="center", font=("Arial", 10, "normal"))

    def edge(self, x1, y1, x2, y2, color="gray"):
        pen = turtle.RawTurtle(self.screen); pen.hideturtle(); pen.speed(0); pen.penup()
        pen.goto(x1, y1); pen.pendown(); pen.color(color); pen.pensize(1)
        pen.goto(x2, y2)

    def render(self):
        self.screen.update()

class Visualizer:
    """
    Thread-safe viz server. Call from any thread:
      viz.reset(agent_id, title)
      viz.draw_tree(agent_id, root_label, child_labels, chosen_index)
    """
    def __init__(self, titles):
        self.titles = titles
        self.evq = queue.Queue()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.tabs = {}
        self.root = None

    def start(self):
        self.thread.start()

    # ---- public API (thread-safe) ----
    def reset(self, agent_idx, title=None):
        self.evq.put(("reset", agent_idx, title))

    def draw_tree(self, agent_idx, root_label, child_labels, chosen_index=None):
        self.evq.put(("tree", agent_idx, (root_label, child_labels, chosen_index)))

    # ---- tk main loop ----
    def _loop(self):
        self.root = tk.Tk()
        self.root.title("AI Logic Viewer")
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True)

        for i, title in enumerate(self.titles):
            self.tabs[i] = _AgentTab(nb, title)

        def tick():
            try:
                while True:
                    ev, idx, payload = self.evq.get_nowait()
                    tab = self.tabs.get(idx)
                    if not tab:
                        continue
                    if ev == "reset":
                        if isinstance(payload, str) and payload:
                            nb.tab(idx, text=payload)
                        tab.clear()
                        tab.render()
                    elif ev == "tree":
                        root_label, children, chosen = payload
                        tab.clear()
                        # layout
                        root_x, root_y = 0, 150
                        tab.node(root_x, root_y, root_label, color="black")
                        # children: spread horizontally
                        n = max(1, len(children))
                        left = - (n - 1) * 100 // 2
                        coords = []
                        for i, lbl in enumerate(children):
                            x = left + i * 100
                            y = 0
                            col = "green" if (chosen is not None and i == chosen) else "black"
                            tab.node(x, y, lbl, color=col)
                            tab.edge(root_x, root_y - 16, x, y + 16, color="gray")
                            coords.append((x, y))
                        tab.render()
            except queue.Empty:
                pass
            self.root.after(50, tick)

        self.root.after(50, tick)
        self.root.mainloop()
