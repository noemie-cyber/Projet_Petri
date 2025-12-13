"""
Fenêtre principale de l'application.

- Contient le modèle logique du réseau (PetriNet, backend).
- Contient la barre d'outils et le canvas (interface graphique).
- Gère la boucle principale Tkinter.
"""

import tkinter as tk
from UI.canvas import PetriCanvas
from UI.toolbar import ToolBar

from backend.petri import PetriNet

class MainWindow:
    def __init__(self):
        self.modele = PetriNet()

        self.root = tk.Tk()
        self.root.title("Éditeur de Réseaux de Petri")

        self.toolbar = ToolBar(self.root)
        self.toolbar.pack(side="left", fill="y")

        self.canvas = PetriCanvas(self.root)
        self.canvas.pack(side="right", fill="both", expand=True)

        self.toolbar.set_canvas(self.canvas)

    def run(self):
        self.root.mainloop()
