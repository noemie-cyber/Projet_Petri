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
import os
from backend.petri import Place, Transition, Arc  # pour créer les objets backend


class PetriCanvas(tk.Canvas):
    def __init__(self, master, model):
        super().__init__(master, width=800, height=600, bg="white")

        # Images possibles pour les places (anneaux de couleur)
        script_dir = os.path.dirname(__file__)
        self.place_images = []
        for filename in [
            "pl_vert.png",
            "pl_jaune.png",
            "pl_rouge.png",
            "pl_marron.png",
            "pl_orange.png",
            "pl_bleu.png",
            "pl_violet.png",
        ]:
            path = os.path.join(script_dir, filename)
            self.place_images.append(tk.PhotoImage(file=path))

        self.next_place_img_index = 0


        # Image de fond façon billard (réduite)
        base_image = tk.PhotoImage(file="code_source/UI/FondBillard.png")
        # Réduction de l'image ( on elargie puis on divise pour avoir un ration de 1.5)
        #enlarged = base_image.zoom(3, 3)
        #self.bg_image = enlarged.subsample(2, 2)

        # Taille fixe ( ce qu'on utilise actuellement)
        self.bg_image = tk.PhotoImage(file="code_source/UI/FondBillard.png")

        self.bg_item = self.create_image(0, 0, image=self.bg_image, anchor="nw", tags=("background",))



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

        self.arc_items = {}       # id de la ligne
        self.arc_text_items = {}  # id du texte du poids
                
        self.transition_rects = {}   # item rectangle



        # État pour la simulation continue
        self.simulating = False      # True si le mode auto est en cours
        self.sim_delay = 500         # délai en ms entre deux tirs


        self.bind("<Button-1>", self.on_click)

        self.tag_bind("arc", "<Double-Button-1>", self.on_arc_double_click)

        

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


    def _format_tokens(self, n):
        if n <= 5:
            return "●" * n
        return str(n)



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

        r = 20  # position du texte
        # Image de la place (anneau de couleur), centrée en (x, y)
        img = self.place_images[self.next_place_img_index]
        self.next_place_img_index = (self.next_place_img_index + 1) % len(self.place_images)
        place_item = self.create_image(x, y, image=img)

        # Nom de la place au-dessus de l'image
        name_item = self.create_text(x, y - r - 10, text=place_id)


        # Nombre de jetons au centre du cercle
        tokens_item = self.create_text(x, y, text=self._format_tokens(tokens))

        # On mémorise quel ID logique correspond à cet élément graphique
        self.item_to_id[place_item] = place_id
        

        self.place_token_text[place_id] = tokens_item
        self.current_marking[place_id] = tokens
        self.item_to_id[name_item] = place_id
        self.item_to_id[tokens_item] = place_id
        self.id_to_items[place_id] = {place_item, name_item, tokens_item}

    def create_transition(self, x, y):

        # Recalcule le prochain numéro de transition à partir des IDs existants
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

        # Dessin graphique
        trans_item = self.create_rectangle(x-5, y-25, x+5, y+25, fill="black")
        text_item = self.create_text(x, y-35, text=trans_id)  # texte au-dessus
        

        # Mémorisation du lien graphique == logique
        self.item_to_id[trans_item] = trans_id
        self.item_to_id[text_item] = trans_id
        self.id_to_items[trans_id] = {trans_item, text_item}
        
        # mémoriser le rectangle pour pouvoir changer sa couleur
        self.transition_rects[trans_id] = trans_item

        # mettre à jour les couleurs en fonction du marquage courant
        self.update_transition_colors()


    def update_marking(self, new_marking):
        # Met à jour le marquage courant et les nombres affichés.
        self.current_marking = new_marking
        for place_id, tokens in new_marking.items():
            text_item = self.place_token_text.get(place_id)
            if text_item is not None:
                self.itemconfig(text_item, text=self._format_tokens(tokens))
            
        self.update_transition_colors()



    def update_transition_colors(self):
        marking = dict(self.current_marking)

        # on calcule pre une fois
        pre, _ = self.model.build_pre_post()

        for t_id, rect_id in self.transition_rects.items():
            arcs_entree = pre.get(t_id, [])

            # si la transition n'a aucun arc d'entrée, on la laisse en noir
            if not arcs_entree:
                self.itemconfig(rect_id, fill="black")
                continue

            try:
                if self.model.enabled(t_id, marking):
                    self.itemconfig(rect_id, fill="green")
                else:
                    self.itemconfig(rect_id, fill="red")
            except Exception:
                self.itemconfig(rect_id, fill="black")


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


    def start_auto_simulation(self):
        """Active/désactive le mode simulation continue."""
        # Toggle : si déjà en cours, on arrête
        if self.simulating:
            self.simulating = False
        else:
            self.simulating = True
            self.auto_step()   # lance la première étape

    def auto_step(self):
        """Effectue un tir automatique puis planifie le suivant."""
        if not self.simulating:
            return

        # On travaille sur une copie du marquage courant
        marking = dict(self.current_marking)

        # Liste des transitions franchissables dans ce marquage
        enabled_transitions = [
            t_id for t_id in self.model.transitions.keys()
            if self.model.enabled(t_id, marking)
        ]

        if not enabled_transitions:
            # Plus aucune transition possible : on arrête la simulation
            print("Simulation auto : aucune transition franchissable, arrêt.")
            self.simulating = False
            return

        # Choix simple : on tire la première transition franchissable
        trans_id = enabled_transitions[0]
        print(f"Simulation auto : tir de {trans_id}")

        # Tir dans le backend
        new_marking = self.model.fire(trans_id, marking)

        # Mise à jour de l'affichage
        self.update_marking(new_marking)

        # On planifie l'étape suivante après sim_delay ms
        self.after(self.sim_delay, self.auto_step)



    def handle_arc(self, x, y):
        items = self.find_closest(x, y)
        if not items:
            return
        clicked_item = items[0]

        # On récupère l'ID logique (place_id ou trans_id) associé à l'item cliqué
        logical_id = self.item_to_id.get(clicked_item)
        if logical_id is None:
            # On ne sait pas à quoi correspond cet item, on annule
            self.arc_start = None
            return

        # Si c'est le premier clic, on mémorise simplement la source logique
        if self.arc_start is None:
            self.arc_start = logical_id
            return

        # Deuxième clic : on a déjà une source logique, on récupère la cible logique
        src_id = self.arc_start
        tgt_id = logical_id

        # Empêcher les doublons simples (même source, même cible)
        for a in self.model.arcs:
            if a.source_id == src_id and a.target_id == tgt_id:
                print("Arc doublon ignoré entre", src_id, "et", tgt_id)
                self.arc_start = None
                return

        # Vérif de validité des IDs
        if src_id is None or tgt_id is None:
            self.arc_start = None
            return

        # Création de l'arc dans le backend
        try:
            arc_obj = Arc(source_id=src_id, target_id=tgt_id, weight=1)
            self.model.add_arc(arc_obj)
        except ValueError as e:
            print("Arc refusé :", e)
            self.arc_start = None
            return

        # Dessin graphique : on relie les centres des formes principales
        src_items = self.id_to_items.get(src_id, set())
        tgt_items = self.id_to_items.get(tgt_id, set())

        if not src_items or not tgt_items:
            self.arc_start = None
            return

        def pick_main_item(items):
            # On choisit en priorité ovales et rectangles, sinon n'importe quoi
            for it in items:
                t = self.type(it)
                if t in ("oval", "rectangle"):
                    return it
            return next(iter(items))

        src_item = pick_main_item(src_items)
        tgt_item = pick_main_item(tgt_items)

        src_coords = self.coords(src_item)
        tgt_coords = self.coords(tgt_item)

        # src_coords / tgt_coords peuvent être (x, y) ou (x1, y1, x2, y2)
        if len(src_coords) == 2:
            sx, sy = src_coords
        else:
            x1, y1, x2, y2 = src_coords
            sx = (x1 + x2) / 2
            sy = (y1 + y2) / 2

        if len(tgt_coords) == 2:
            tx, ty = tgt_coords
        else:
            x1, y1, x2, y2 = tgt_coords
            tx = (x1 + x2) / 2
            ty = (y1 + y2) / 2

        import math

        dx = tx - sx
        dy = ty - sy
        dist = math.hypot(dx, dy)
        if dist == 0:
            self.arc_start = None
            return

        ux = dx / dist
        uy = dy / dist

        PLACE_RADIUS = 20
        TRANS_HALF_WIDTH = 5

        def adjust_endpoint(x, y, node_id, direction):
            if node_id in self.model.places:
                r = PLACE_RADIUS
            else:
                r = TRANS_HALF_WIDTH
            return x + direction * ux * r, y + direction * uy * r

        sx2, sy2 = adjust_endpoint(sx, sy, src_id, +1)
        tx2, ty2 = adjust_endpoint(tx, ty, tgt_id, -1)

        line_id = self.create_line(sx2, sy2, tx2, ty2, arrow=tk.LAST, tags=("arc",))
        self.arc_items[(src_id, tgt_id)] = line_id

        if arc_obj.weight != 1:
            mx = (sx2 + tx2) / 2
            my = (sy2 + ty2) / 2
            text_id = self.create_text(mx, my - 10, text=str(arc_obj.weight), fill="white")
            self.arc_text_items[(src_id, tgt_id)] = text_id

        # On réinitialise pour le prochain arc
        self.arc_start = None



        
    def erase(self, x, y):
        items = self.find_closest(x, y)
        if not items:
            return
        item = items[0]

        # Ne jamais supprimer l'image de fond
        if item == self.bg_item or "background" in self.gettags(item):
            return


        logical_id = self.item_to_id.get(item)

        # CAS 1 : on clique sur une ligne d'arc (pas d'ID logique enregistré)
        if logical_id is None:
            # On supprime l'item graphique
            coords = self.coords(item)
            self.delete(item)

            # Si on a bien une ligne (4 coordonnées), on retrouve les nœuds aux extrémités
            if len(coords) == 4:
                x1, y1, x2, y2 = coords

                start_items = self.find_closest(x1, y1)
                end_items = self.find_closest(x2, y2)

                if start_items and end_items:
                    start_id = self.item_to_id.get(start_items[0])
                    end_id = self.item_to_id.get(end_items[0])

                    if start_id is not None and end_id is not None:
                        # On enlève du backend tous les arcs qui relient exactement ces deux IDs
                        self.model.arcs = [
                            a for a in self.model.arcs
                            if not (a.source_id == start_id and a.target_id == end_id)
                        ]
            return

        # CAS 2 : on clique sur une place ou une transition (avec ID logique)
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



    def on_arc_double_click(self, event):
        item = self.find_withtag("current")
        if not item:
            return
        line_id = item[0]

        # retrouver src_id, tgt_id correspondant à cette ligne
        src_tgt = None
        for key, lid in self.arc_items.items():
            if lid == line_id:
                src_tgt = key
                break
        if src_tgt is None:
            return

        src_id, tgt_id = src_tgt

        # retrouver l'objet Arc du backend
        arc_obj = None
        for a in self.model.arcs:
            if a.source_id == src_id and a.target_id == tgt_id:
                arc_obj = a
                break
        if arc_obj is None:
            return

        # demander le nouveau poids
        new_w = simpledialog.askinteger(
            "Poids de l'arc",
            f"Nouveau poids pour {src_id} -> {tgt_id} :",
            minvalue=1,
        )
        if new_w is None:
            return

        arc_obj.weight = new_w

        # mettre à jour le texte
        # recalculer la position milieu de la ligne
        x1, y1, x2, y2 = self.coords(line_id)
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2

        # supprimer l'ancien texte s'il existe
        key = (src_id, tgt_id)
        old_text_id = self.arc_text_items.get(key)
        if old_text_id is not None:
            self.delete(old_text_id)

        # ne rien afficher si poids == 1
        if new_w != 1:
            text_id = self.create_text(mx, my - 10, text=str(new_w), fill="white")
            self.arc_text_items[key] = text_id
        else:
            if key in self.arc_text_items:
                del self.arc_text_items[key]


    def reset_marking(self):
        # remet les jetons au marquage initial du backend
        initial = self.model.initial_marking()
        # met aussi à jour le marquage courant stocké dans le canvas
        self.update_marking(initial)


    def clear_all(self):
        """Efface complètement le réseau (graphique + backend)."""

        # 1) Effacer tout sauf le fond
        for item in self.find_all():
            if item == self.bg_item or "background" in self.gettags(item):
                continue
            self.delete(item)


        # 2) Réinitialiser l'état graphique interne
        self.item_to_id = {}
        self.id_to_items = {}
        self.place_token_text = {}
        self.current_marking = {}
        self.arc_start = None

        # 3) Réinitialiser les compteurs
        self.place_count = 0
        self.transition_count = 0

        # 4) Réinitialiser le backend (PetriNet)
        self.model.places.clear()
        self.model.transitions.clear()
        self.model.arcs.clear()

        # 5) Arrêter une éventuelle simulation auto
        self.simulating = False

