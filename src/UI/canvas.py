import tkinter as tk
from tkinter import simpledialog

class PetriCanvas(tk.Canvas):
    def __init__(self, master):
        super().__init__(master, width=800, height=600, bg="white")

        self.tool_var = None
        self.arc_start = None

        self.bind("<Button-1>", self.on_click)

    def set_tool_var(self, tool_var):
        self.tool_var = tool_var

    def on_click(self, event):
        if not self.tool_var:
            return

        tool = self.tool_var.get()

        if tool == "place":
            self.create_place(event.x, event.y)

        elif tool == "transition":
            self.create_transition(event.x, event.y)

        elif tool == "arc":
            self.handle_arc(event.x, event.y)

        elif tool == "eraser":
            self.erase(event.x, event.y)

    def create_place(self, x, y):
        tokens = simpledialog.askinteger(
            "Création Place", "Nombre de jetons :", minvalue=0
        )
        if tokens is None:
            return

        r = 20
        place = self.create_oval(x-r, y-r, x+r, y+r, fill="white", outline="black")
        self.create_text(x, y, text=str(tokens))

    def create_transition(self, x, y):
        self.create_rectangle(x-5, y-25, x+5, y+25, fill="black")

    def handle_arc(self, x, y):
        item = self.find_closest(x, y)

        if not item:
            return

        if self.arc_start is None:
            self.arc_start = item
        else:
            x1, y1, x2, y2 = self.coords(self.arc_start)
            self.create_line(x1, y1, x, y, arrow=tk.LAST)
            self.arc_start = None

    def erase(self, x, y):
        item = self.find_closest(x, y)
        self.delete(item)
