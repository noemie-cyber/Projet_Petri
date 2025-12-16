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
from backend.petri import analyze_from_dict

class MainWindow:
    def __init__(self):
        self.model = PetriNet()

        self.root = tk.Tk()
        self.root.title("Éditeur de Réseaux de Petri")

        self.toolbar = ToolBar(self.root)
        self.toolbar.pack(side="left", fill="y")

        self.canvas = PetriCanvas(self.root, self.model)
        self.canvas.pack(side="right", fill="both", expand=True)

        self.toolbar.set_canvas(self.canvas)
        self.toolbar.set_analyser_callback(self.analyser_reseau)

    def run(self):
        self.root.mainloop()

    def analyser_reseau(self):
        data = self.model.to_dict()

        result = analyze_from_dict(data, max_states=1000)

        import json, subprocess

        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        with open("graph.dot", "w", encoding="utf-8") as f:
            f.write(result["dot"])

        print("Fichiers générés : result.json, graph.dot")

        try:
            subprocess.run(["dot", "-Tpng", "graph.dot", "-o", "graph.png"], check=True)
            print("Image synthétique générée : graph.png")
        except Exception:
            print("Impossible de générer graph.png automatiquement (Graphviz non dispo ou 'dot' pas dans le PATH).")