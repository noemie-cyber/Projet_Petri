"""
Fenêtre principale de l'application.

- Contient le modèle logique du réseau (PetriNet, backend).
- Contient la barre d'outils et le canvas (interface graphique).
- Gère la boucle principale Tkinter.
"""

import tkinter as tk
from tkinter import messagebox
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

    # Création du graphe d'accessibilité et analyse
    def analyser_reseau(self):
        import json, subprocess
        data = self.model.to_dict()

        try:
            result = analyze_from_dict(data, max_states=1000)
        except ValueError as e:
            # Réseau incohérent : on affiche un message et on ne génère aucun fichier
            messagebox.showerror(
                "Erreur réseau de Petri",
                f"Le réseau est incohérent :\n{e}"
            )
            print("Analyse annulée (réseau incohérent) :", e)
            return

        # Si tout va bien, on génère les fichiers comme avant
        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        with open("graph.dot", "w", encoding="utf-8") as f:
            f.write(result["dot"])

        print("Fichiers générés : result.json, graph.dot")

        try:
            subprocess.run(["dot", "-Tpng", "graph.dot", "-o", "graph.png"], check=True)
            print("Image du graph d'état générée : graph.png")
        except Exception:
            print("Impossible de générer graph.png automatiquement (Graphviz non dispo ou 'dot' pas dans le PATH).")