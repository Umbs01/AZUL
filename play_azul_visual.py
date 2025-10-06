import tkinter as tk
from tkinter import ttk
import turtle

class AITab:
    def __init__(self, parent, name):
        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text=name)
        self.canvas = tk.Canvas(self.frame, width=400, height=400)
        self.canvas.pack()
        self.screen = turtle.TurtleScreen(self.canvas)
        self.t = turtle.RawTurtle(self.screen)
        self.t.speed(0)

    def reset(self):
        self.screen.clearscreen()
        self.t = turtle.RawTurtle(self.screen)
        self.t.speed(0)

    def draw_state(self, text, x, y, color="black"):
        self.t.penup()
        self.t.goto(x,y)
        self.t.pendown()
        self.t.color(color)
        self.t.write(text, align="center", font=("Arial", 10, "normal"))
        self.t.penup()
        self.t.goto(x,y-15)
        self.t.pendown()
        self.t.circle(15)

def launch_visualizer():
    root = tk.Tk()
    root.title("AI Reasoning")

    notebook = ttk.Notebook(root)
    notebook.pack(expand=1, fill="both")

    agents = {}
    for name in ["Greedy","Random","Minimax"]:
        agents[name] = AITab(notebook, name)

    root.update()
    return root, agents

if __name__ == "__main__":
    root, visualizers = launch_visualizer()
    # Example test:
    visualizers["Greedy"].draw_state("Start",0,100,"blue")
    visualizers["Greedy"].draw_state("Move1",-80,0,"green")
    visualizers["Greedy"].draw_state("Bad",-160,-100,"red")
    root.mainloop()
