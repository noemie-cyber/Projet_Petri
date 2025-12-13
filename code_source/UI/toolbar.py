"""
Barre d'outils verticale pour choisir l'outil de dessin :
- Place
- Transition
- Arc
- Gomme

Elle met à jour une StringVar partagée avec le canvas.
"""

import tkinter as tk

class ToolBar(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.tool = tk.StringVar(value="place")

        tk.Button(self, text="Place", command=lambda: self.tool.set("place")).pack()
        tk.Button(self, text="Transition", command=lambda: self.tool.set("transition")).pack()
        tk.Button(self, text="Arc", command=lambda: self.tool.set("arc")).pack()
        tk.Button(self, text="Gomme", command=lambda: self.tool.set("eraser")).pack()

    def set_canvas(self, canvas):
        canvas.set_tool_var(self.tool)
