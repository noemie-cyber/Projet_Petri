"""
Canvas graphique pour dessiner un réseau de Petri.

Pour l'instant :
- dessine des places (cercles + nombre de jetons),
- dessine des transitions (rectangles),
- dessine des arcs (flèches) en reliant deux éléments,
- permet d'effacer un élément.

"""

import tkinter as tk
from tkinter import simpledialog
from backend.petri import Place, Transition, Arc  # pour créer les objets backend

class PetriCanvas(tk.Canvas):
    def __init__(self, master, model):
        super().__init__(master, width=800, height=600, bg="white")

        self.model = model  # référence vers le PetriNet du backend
        self.tool_var = None
        self.arc_start = None

        # Compteurs simples pour générer des IDs uniques
        self.place_count = 0
        self.transition_count = 0

        # Lien entre l'ID graphique tkinter et l'ID logique (P1, T1, etc.)
        self.item_to_id = {}
        
        self.current_marking = {}      # place_id -> nb de jetons
        self.place_token_text = {}     # place_id -> id de l'objet texte
        # Inverse : ID logique -> items graphiques
        self.id_to_items = {}

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

        elif tool == "fire":
            self.fire_transition_at(event.x, event.y)

    def create_place(self, x, y):
        tokens = simpledialog.askinteger(
            "Création Place", "Nombre de jetons :", minvalue=0
        )
        if tokens is None:
            return

        # Recalcule le prochain numéro de place à partir des IDs existants
        if self.model.places:
            nums = []
            for pid in self.model.places.keys():
                if pid.startswith("P"):
                    try:
                        nums.append(int(pid[1:]))
                    except ValueError:
                        pass
            self.place_count = max(nums) if nums else 0
        else:
            self.place_count = 0


        # Génération d'un ID de place unique (P1, P2, ...)
        self.place_count += 1
        place_id = f"P{self.place_count}"

        # Création de l'objet Place dans le backend
        place_obj = Place(id=place_id, name=place_id, initial_tokens=tokens)
        self.model.add_place(place_obj)

        r = 20
        place_item = self.create_oval(x-r, y-r, x+r, y+r, fill="white", outline="black")
        # Nom de la place au-dessus du cercle
        name_item = self.create_text(x, y - r - 10, text=place_id)

        # Nombre de jetons au centre du cercle
        tokens_item = self.create_text(x, y, text=str(tokens))

        # On mémorise quel ID logique correspond à cet élément graphique
        self.item_to_id[place_item] = place_id
        

        self.place_token_text[place_id] = tokens_item
        self.current_marking[place_id] = tokens
        self.item_to_id[name_item] = place_id
        self.item_to_id[tokens_item] = place_id
        self.id_to_items[place_id] = {place_item, name_item, tokens_item}

    def create_transition(self, x, y):
        
        if self.model.transitions:
            nums = []
            for tid in self.model.transitions.keys():
                if tid.startswith("T"):
                    try:
                        nums.append(int(tid[1:]))
                    except ValueError:
                        pass
            self.transition_count = max(nums) if nums else 0
        else:
            self.transition_count = 0

        
         # Génération d'un ID de transition unique (T1, T2, ...)
        self.transition_count += 1
        trans_id = f"T{self.transition_count}"

        # Création de l'objet Transition dans le backend
        trans_obj = Transition(id=trans_id, name=trans_id)
        self.model.add_transition(trans_obj)

        trans_item = self.create_rectangle(x-5, y-25, x+5, y+25, fill="black")
        text_item = self.create_text(x, y-35, text=trans_id)  # texte au-dessus

        # Mémorisation du lien graphique == logique
        self.item_to_id[trans_item] = trans_id
        self.item_to_id[text_item] = trans_id
        self.id_to_items[trans_id] = {trans_item, text_item}

    def update_marking(self, new_marking):
        # Met à jour le marquage courant et les nombres affichés.
        self.current_marking = new_marking
        for place_id, tokens in new_marking.items():
            text_item = self.place_token_text.get(place_id)
            if text_item is not None:
                self.itemconfig(text_item, text=str(tokens))

    def fire_transition_at(self, x, y):
        # On récupère l'item le plus proche du clic
        items = self.find_closest(x, y)
        if not items:
            return
        item = items[0]

        # On regarde si c'est une transition connue du backend
        trans_id = self.item_to_id.get(item)
        if trans_id is None:
            return

        # On travaille sur une copie du marquage courant
        marking = dict(self.current_marking)

        # Si la transition n'est pas franchissable, on ne fait rien
        if not self.model.enabled(trans_id, marking):
            print(f"Transition {trans_id} non franchissable pour ce marquage")
            return

        # Tir de la transition dans le backend
        new_marking = self.model.fire(trans_id, marking)

        # Mise à jour de l'affichage (nombres dans les places)
        self.update_marking(new_marking)

    def handle_arc(self, x, y):
        items = self.find_closest(x, y)

        if not items:
            return
        item = items[0]

        if self.arc_start is None:
            self.arc_start = item
        else:
            src_id = self.item_to_id.get(self.arc_start)
            tgt_id = self.item_to_id.get(item)

            # Empêcher les doublons simples (même source, même cible)
            for a in self.model.arcs:
                if a.source_id == src_id and a.target_id == tgt_id:
                    print("Arc doublon ignoré entre", src_id, "et", tgt_id)
                    self.arc_start = None
                    return

            if src_id is None or tgt_id is None:
                # Si on ne connaît pas les IDs, on annule simplement
                self.arc_start = None
                return
            
            try:
                arc_obj = Arc(source_id=src_id, target_id=tgt_id, weight=1)
                self.model.add_arc(arc_obj)
            except ValueError as e:
                # Arc non valide
                print("Arc refusé :", e)
                self.arc_start = None
                return

            # Si tout est ok côté backend, alors on dessine la ligne
            x1, y1, x2, y2 = self.coords(self.arc_start)
            self.create_line((x1 + x2) / 2, (y1 + y2) / 2, x, y, arrow=tk.LAST)

            self.arc_start = None

        

    def erase(self, x, y):
        items = self.find_closest(x, y)

        if not items:
            return
        item = items[0]

        logical_id = self.item_to_id.get(item)
        if logical_id is None:
            # Si l'item n'a pas d'ID (arc), on efface juste la ligne
            self.delete(item)
            return
        
        if logical_id in self.model.places:
            # supprimer la place et tous les arcs incidents
            del self.model.places[logical_id]
            self.model.arcs = [
                a for a in self.model.arcs
                if a.source_id != logical_id and a.target_id != logical_id
            ]
        elif logical_id in self.model.transitions:
            # supprimer la transition et tous les arcs incidents
            del self.model.transitions[logical_id]
            self.model.arcs = [
                a for a in self.model.arcs
                if a.source_id != logical_id and a.target_id != logical_id
            ]

        # Suppression des items graphiques liés à l'ID
        items_to_delete = self.id_to_items.get(logical_id, set())
        for it in items_to_delete:
            if it in self.item_to_id:
                del self.item_to_id[it]
            self.delete(it)

        # On nettoie les maps
        if logical_id in self.id_to_items:
            del self.id_to_items[logical_id]