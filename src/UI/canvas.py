"""
Canvas graphique pour dessiner un réseau de Petri.

Pour l'instant :
- dessine des places (cercles + nombre de jetons),
- dessine des transitions (rectangles),
- dessine des arcs (flèches) en reliant deux éléments,
- permet d'effacer un élément.
"""

import tkinter as tk
from tkinter import simpledialog, messagebox
from backend.petri import Place, Transition, Arc

class PetriCanvas(tk.Canvas):
    def __init__(self, master, model):
        super().__init__(master, width=800, height=600, bg="white")

        self.model = model  # référence vers le PetriNet du backend
        self.tool_var = None
        self.arc_start = None

        # Compteurs pour générer des IDs uniques
        self.place_count = 0
        self.transition_count = 0

        # Lien entre l'ID graphique tkinter et l'ID logique
        self.item_to_id = {}

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

        # Génération d'un ID de place unique (P1, P2, ...)
        self.place_count += 1
        place_id = f"P{self.place_count}"

        # Création de l'objet Place dans le backend
        place_obj = Place(id=place_id, name=place_id, initial_tokens=tokens)
        self.model.add_place(place_obj)

        r = 20
        place_item = self.create_oval(x-r, y-r, x+r, y+r, fill="white", outline="black")
        text_item = self.create_text(x, y, text=str(tokens))

        # On associe le CERCLE et le TEXTE à l'ID logique
        self.item_to_id[place_item] = place_id
        self.item_to_id[text_item] = place_id

    def create_transition(self, x, y):
        # 1. Génération de l'ID (T1, T2...)
        self.transition_count += 1
        trans_id = f"T{self.transition_count}"

        # 2. Création de l'objet dans le Backend
        trans_obj = Transition(id=trans_id, name=trans_id)
        self.model.add_transition(trans_obj)

        # 3. Création du rectangle (30 pixels de large pour faciliter le clic)
        trans_item = self.create_rectangle(x-5, y-25, x+5, y+25, fill="black")

        # 4. Association ID Graphique <-> ID Logique
        self.item_to_id[trans_item] = trans_id

    def handle_arc(self, x, y):
        items = self.find_closest(x, y)
        
        if not items:
            return
        item = items[0]
        
        # Récupération de l'ID logique
        item_id = self.item_to_id.get(item)
        if item_id is None:
            return

        # Clic 1 
        if self.arc_start is None:
            self.arc_start = item
            return

        # Clic 2 
        else:
            start_id = self.item_to_id.get(self.arc_start)
            
            #Vérification que la même place n'est pas selectionnée
            if start_id == item_id:
                self.arc_start = None
                return

            #Vérification qu'on sélectionne bien une place vers transition et inversement
            if start_id[0] == item_id[0]: 
                tk.messagebox.showerror("Erreur", "Connexion invalide, vous n'avez selectionné que des places ou transitions")
                self.arc_start = None
                return

            #Dessin de l'arc
            try:
                x1, y1, x2, y2 = self.bbox(self.arc_start)
                start_x, start_y = (x1 + x2) / 2, (y1 + y2) / 2 
                
                x3, y3, x4, y4 = self.bbox(item)
                end_x, end_y = (x3 + x4) / 2, (y3 + y4) / 2
                
                self.create_line(start_x, start_y, end_x, end_y, arrow=tk.LAST, width=2, fill="black")

            except Exception:
                #Exception si erreur graphique
                self.arc_start = None
                return

            #Ajout au Backend
            try:
                arc_obj = Arc(source_id=start_id, target_id=item_id, weight=1)
                self.model.add_arc(arc_obj)
            except ValueError as e:
                # Si le backend refuse, ignorer ou afficher une erreur
                print(f"Erreur Backend : {e}")
            
            #Réinitialisation
            self.arc_start = None

    def erase(self, x, y):
        items = self.find_closest(x, y)

        if not items:
            return
        item = items[0]

        #On oublie l'ID logique associé
        if item in self.item_to_id:
            del self.item_to_id[item]

        self.delete(item)