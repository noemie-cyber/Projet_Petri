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

from PIL import Image, ImageTk   
import os


class MainWindow:
    def __init__(self):
        self.model = PetriNet()

        self.root = tk.Tk()
        self.root.title("Éditeur de Réseaux de Petri")

        #  ÉCRAN D'ACCUEIL BILLARD 
        self.start_frame = tk.Frame(self.root)
        self.start_frame.pack(fill="both", expand=True)

        # charge l'image de fond
        script_dir = os.path.dirname(__file__)
        bg_path = os.path.join(script_dir, "FondBillard.png")
        bg_image = Image.open(bg_path)
        bg_image = bg_image.resize((1920, 1080))          # taille fenêtre
        self.bg_photo = ImageTk.PhotoImage(bg_image)   

        # label plein écran avec l'image de fond
        bg_label = tk.Label(self.start_frame, image=self.bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)   # couvre tout 

        # texte titre centré
        title = tk.Label(
            self.start_frame,
            text="Éditeur de Réseaux de Petri",
            fg="white",
            bg="#438632",
            font=("Arial", 24, "bold")
        )
        title.place(relx=0.5, rely=0.3, anchor="center")    # centré 

        # gros bouton Start centré
        start_btn = tk.Button(
            self.start_frame,
            text="START",
            font=("Arial", 20, "bold"),
            bg="#FFFFFF",
            fg="#583F27",
            activebackground="#7a563f",
            activeforeground="white",
            bd=0,
            padx=20,
            pady=10,
            command=self.show_editor
        )
        start_btn.place(relx=0.5, rely=0.55, anchor="center")   # centré aussi


        # ÉDITEUR (caché au début)
        self.editor_frame = tk.Frame(self.root)

        self.toolbar = ToolBar(self.editor_frame)
        self.toolbar.pack(side="left", fill="y")

        self.canvas = PetriCanvas(self.editor_frame, self.model)
        self.canvas.pack(side="right", fill="both", expand=True)

        self.toolbar.set_canvas(self.canvas)
        self.toolbar.set_analyser_callback(self.analyser_reseau)

    def show_editor(self):
        self.start_frame.pack_forget()
        self.editor_frame.pack(fill="both", expand=True)


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

                    # Afficher l'image du graphe dans une nouvelle fenêtre
        try:
            top = tk.Toplevel(self.root)
            top.title("Graphe d'accessibilité")

            img = Image.open("graph.png")
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(top, image=photo)
            label.image = photo  # garder une référence
            label.pack()
        except Exception as e:
            print("Impossible d'afficher graph.png dans Tkinter :", e)
