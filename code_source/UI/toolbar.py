"""
Barre d'outils verticale pour choisir l'outil de dessin :
- Place
- Transition
- Arc
- Gomme

Elle met à jour une StringVar partagée avec le canvas.
"""

import tkinter as tk
import os


class ToolBar(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#CCB29B")  # fond marron

        self.tool = tk.StringVar(value="place")
        self.canvas = None
        self.analyser_callback = None

        # Dossier où se trouvent les images (même dossier que toolbar.py)
        script_dir = os.path.dirname(__file__)

        # On garde les images dans des attributs pour éviter le garbage collection
        self.icons = {}
        def load_icon(name, filename):
            path = os.path.join(script_dir, filename)
            self.icons[name] = tk.PhotoImage(file=path)
            return self.icons[name]

        icon_place      = load_icon("place",      "btn_place.png")
        icon_trans      = load_icon("trans",      "btn_transition.png")
        icon_arc        = load_icon("arc",        "btn_arc.png")
        icon_eraser     = load_icon("eraser",     "btn_eraser.png")
        icon_fire       = load_icon("fire",       "btn_fire.png")
        icon_auto       = load_icon("auto",       "btn_auto.png")
        icon_trash      = load_icon("trash",      "btn_trash.png")

        btn_opts = {
            "bg": "#CCB29B",
            "activebackground": "#CCB29B",
            "bd": 0,
            "relief": "flat",
        }

        tk.Label(self, text="Outils", bg="#CCB29B", fg="white",
                 font=("Arial", 12, "bold")).pack(pady=(5, 10))

        tk.Button(self, image=icon_place,
                  command=lambda: self.tool.set("place"), **btn_opts).pack(pady=3)
        tk.Button(self, image=icon_trans,
                  command=lambda: self.tool.set("transition"), **btn_opts).pack(pady=3)
        tk.Button(self, image=icon_arc,
                  command=lambda: self.tool.set("arc"), **btn_opts).pack(pady=3)
        tk.Button(self, image=icon_eraser,
                  command=lambda: self.tool.set("eraser"), **btn_opts).pack(pady=3)
        tk.Button(self, image=icon_fire,
                  command=lambda: self.tool.set("fire"), **btn_opts).pack(pady=(3, 80))

        tk.Label(self, text="Simulation", bg="#CCB29B", fg="white",
                 font=("Arial", 12, "bold")).pack(pady=(40, 5))

        tk.Button(self, image=icon_auto,
                  command=self._on_auto, **btn_opts).pack(pady=3)
        tk.Button(self, image=icon_trash,
                  command=self._on_clear_all, **btn_opts).pack(pady=(3, 10))

        tk.Button(self, text="Analyser", bg="#FFFFFF", fg="#583F27",
                  font=("Arial", 10, "bold"), bd=0,
                  activebackground="#CCB29B", activeforeground="white", command=self._on_analyser).pack(pady=(10, 5))

    def set_canvas(self, canvas):
        self.canvas = canvas
        canvas.set_tool_var(self.tool)

    def set_analyser_callback(self, func):
        self.analyser_callback = func

    def _on_analyser(self):
        if self.analyser_callback is not None:
            self.analyser_callback()

    def _on_auto(self):
        if self.canvas is not None:
            self.canvas.start_auto_simulation()

    def _on_clear_all(self):
        if self.canvas is not None:
            self.canvas.clear_all()
