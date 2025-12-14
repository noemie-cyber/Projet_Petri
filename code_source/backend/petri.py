"""
Modèle et moteur de réseau de Petri.

Contient :
- les classes Place, Transition et Arc (définition d'un réseau de Petri),
- la classe PetriNet qui :
  - stocke les places, transitions et arcs,
  - vérifie la cohérence du réseau (types d'arcs, IDs uniques),
  - calcule les tirages possibles et le graphe d'accessibilité (reachability),
  - fournit des fonctions d'analyse (deadlocks, transitions mortes, etc.),
  - permet l'import/export du réseau et du graphe d'accessibilité (dict JSON, format DOT).

Ce fichier est indépendant de l'interface graphique. Il peut être utilisé en ligne de commande
ou par le frontend pour analyser un réseau créé par l'utilisateur.
"""


from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple



#  Modèle (data classes)


#Représente une place du réseau de Petri (avec son nombre initial de jetons).
@dataclass
class Place:
    id: str
    name: str
    initial_tokens: int = 0

    def __post_init__(self) -> None:
        if self.initial_tokens < 0:
            raise ValueError("Une place ne peut pas avoir un nombre de jetons négatif")


@dataclass
class Transition:
    id: str
    name: str

#Représente un arc du réseau de Petri (condition du poid positif).
@dataclass
class Arc:
    source_id: str
    target_id: str
    weight: int = 1

    def __post_init__(self) -> None:
        if self.weight <= 0:
            raise ValueError("Le poids d'un arc doit être strictement positif")



#  PetriNet (moteur)


class PetriNet:
    def __init__(self) -> None:
        self.places: Dict[str, Place] = {}
        self.transitions: Dict[str, Transition] = {}
        self.arcs: List[Arc] = []

    # Edition / cohérence 

    # Ajoute une place au réseau, en vérifiant que son ID n'est pas déjà utilisé.
    def add_place(self, place: Place) -> None:
        if place.id in self.places or place.id in self.transitions:
            raise ValueError(f"ID déjà utilisé: {place.id}")
        self.places[place.id] = place

    #Ajoute une transition au réseau, et vérifie l'ID.
    def add_transition(self, transition: Transition) -> None:
        if transition.id in self.transitions or transition.id in self.places:
            raise ValueError(f"ID déjà utilisé: {transition.id}")
        self.transitions[transition.id] = transition

    def add_arc(self, arc: Arc) -> None:
        src_is_place = arc.source_id in self.places
        src_is_trans = arc.source_id in self.transitions
        tgt_is_place = arc.target_id in self.places
        tgt_is_trans = arc.target_id in self.transitions

        if not (src_is_place or src_is_trans):
            raise ValueError(f"Source inconnue: {arc.source_id}")
        if not (tgt_is_place or tgt_is_trans):
            raise ValueError(f"Cible inconnue: {arc.target_id}")

        if (src_is_place and tgt_is_place) or (src_is_trans and tgt_is_trans):
            raise ValueError(
                "Un arc doit relier Place->Transition ou Transition->Place "
                "(pas Place->Place ni Transition->Transition)"
            )

        self.arcs.append(arc)

    # Marquage / tables pre-post 

    #Construit le marquage initial à partir des jetons initiaux de chaque place.
    def initial_marking(self) -> Dict[str, int]:
        return {pid: p.initial_tokens for pid, p in self.places.items()}

    """
        Construit les tables pre et post :
        - pre[t]  = liste des (place, poids) consommés par la transition t,
        - post[t] = liste des (place, poids) produits par la transition t.
        """
    
    def build_pre_post(self) -> Tuple[Dict[str, List[Tuple[str, int]]], Dict[str, List[Tuple[str, int]]]]:
        pre: Dict[str, List[Tuple[str, int]]] = {tid: [] for tid in self.transitions}
        post: Dict[str, List[Tuple[str, int]]] = {tid: [] for tid in self.transitions}

        for arc in self.arcs:
            if arc.source_id in self.places and arc.target_id in self.transitions:
                pre[arc.target_id].append((arc.source_id, arc.weight))
            elif arc.source_id in self.transitions and arc.target_id in self.places:
                post[arc.source_id].append((arc.target_id, arc.weight))
            else:
                raise ValueError("Arc incohérent: il ne relie pas Place->Transition ou Transition->Place")

        return pre, post

    # Moteur : enabled / fire / step

    #Teste si la transition est franchissable pour un marquage donné.
    def enabled(self, transition_id: str, marking: Dict[str, int]) -> bool:
        
        # Option A : une transition sans pré-arc (pre vide) est considérée franchissable.
        
        if transition_id not in self.transitions:
            raise ValueError(f"Transition inconnue: {transition_id}")

        pre, _ = self.build_pre_post()

        for place_id, weight in pre[transition_id]:
            if marking.get(place_id, 0) < weight:
                return False

        return True
    
    #Applique le tir de la transition : consomme et produit des jetons.
    def fire(self, transition_id: str, marking: Dict[str, int]) -> Dict[str, int]:
        if not self.enabled(transition_id, marking):
            raise ValueError(f"Transition non franchissable (not enabled): {transition_id}")

        pre, post = self.build_pre_post()
        new_marking = dict(marking)

        for place_id, weight in pre[transition_id]:
            new_marking[place_id] = new_marking.get(place_id, 0) - weight

        for place_id, weight in post[transition_id]:
            new_marking[place_id] = new_marking.get(place_id, 0) + weight

        return new_marking

    #Calcule toutes les transitions franchissables et retourne la liste (transition, nouveau marquage) possible depuis ce marquage.
    def step(self, marking: Dict[str, int]) -> List[Tuple[str, Dict[str, int]]]:
        results: List[Tuple[str, Dict[str, int]]] = []
        for transition_id in self.transitions:
            if self.enabled(transition_id, marking):
                results.append((transition_id, self.fire(transition_id, marking)))
        return results

    # Utilitaires reachability

    #Ordre fixe des places.
    def place_order(self) -> List[str]:
        return sorted(self.places.keys())

    #Code un marquage en tuple d'entiers, pour pouvoir le stocker dans un set/dict.
    def marking_key(self, marking: Dict[str, int]) -> Tuple[int, ...]:
        order = self.place_order()
        return tuple(marking.get(pid, 0) for pid in order)


    # Reachability BFS 
    """
        Explore l'espace d'états par BFS à partir du marquage initial.
        Renvoie :
        - la liste des marquages atteints,
        - les arêtes (état source, transition, état cible),
        - les états en deadlock,
        - un indicateur de troncature si on dépasse max_states.
        """
    
    def reachability_bfs(self, max_states: int = 10000) -> Dict[str, object]:
        if max_states <= 0:
            raise ValueError("max_states doit être > 0")

        order = self.place_order()
        m0 = self.initial_marking()
        k0 = self.marking_key(m0)

        visited: Dict[Tuple[int, ...], int] = {k0: 0}
        states: List[Dict[str, int]] = [m0]
        edges: List[Tuple[int, str, int]] = []
        queue: List[int] = [0]
        deadlocks: List[int] = []

        while queue:
            sid = queue.pop(0)
            marking = states[sid]

            succ = self.step(marking)

            if len(succ) == 0:
                deadlocks.append(sid)

            for tid, new_marking in succ:
                key = self.marking_key(new_marking)

                if key in visited:
                    to_id = visited[key]
                else:
                    if len(states) >= max_states:
                        return {
                            "place_order": order,
                            "states": states,
                            "edges": edges,
                            "deadlocks": deadlocks,
                            "truncated": True,
                        }

                    to_id = len(states)
                    visited[key] = to_id
                    states.append(new_marking)
                    queue.append(to_id)

                edges.append((sid, tid, to_id))

        return {
            "place_order": order,
            "states": states,
            "edges": edges,
            "deadlocks": deadlocks,
            "truncated": False,
        }


    # Analyse 
    """
    Résumé d'analyse du graphe d'accessibilité :
    - nombre d'états et d'arêtes,
    - listes des deadlocks,
    - nombre max de jetons observés par place,
    - transitions qui ont tiré / jamais tiré.
    """

    def analyze_reachability(self, max_states: int = 10000) -> Dict[str, object]:
        res = self.reachability_bfs(max_states=max_states)

        order: List[str] = res["place_order"] 
        states: List[Dict[str, int]] = res["states"] 
        edges: List[Tuple[int, str, int]] = res["edges"] 

        max_tokens = {pid: 0 for pid in order}
        for m in states:
            for pid in order:
                max_tokens[pid] = max(max_tokens[pid], m.get(pid, 0))

        fired = {tid for (_, tid, _) in edges}
        never_fired = sorted(set(self.transitions.keys()) - fired)

        return {
            "truncated": res["truncated"],
            "num_states": len(states),
            "num_edges": len(edges),
            "deadlocks": res["deadlocks"],
            "max_tokens": max_tokens,
            "fired_transitions": sorted(fired),
            "never_fired_transitions": never_fired,
        }

    def liveness_summary(self, max_states: int = 10000) -> Dict[str, object]:
        res = self.reachability_bfs(max_states=max_states)
        edges: List[Tuple[int, str, int]] = res["edges"] 

        fired = {tid for (_, tid, _) in edges}
        all_t = set(self.transitions.keys())
        dead = sorted(all_t - fired)

        return {
            "truncated": res["truncated"],
            "fired_transitions": sorted(fired),
            "dead_transitions": dead,
            "num_fired": len(fired),
            "num_dead": len(dead),
        }


    # Export 
    # Exporte la structure du réseau sous forme de dictionnaire JSON-sérialisable.

    def to_dict(self) -> Dict[str, object]:
        return {
            "places": [
                {"id": p.id, "name": p.name, "initial_tokens": p.initial_tokens}
                for p in self.places.values()
            ],
            "transitions": [{"id": t.id, "name": t.name} for t in self.transitions.values()],
            "arcs": [
                {"source_id": a.source_id, "target_id": a.target_id, "weight": a.weight}
                for a in self.arcs
            ],
        }

    #Exporte le graphe d'accessibilité au format DOT (Graphviz).
    def reachability_to_dict(self, max_states: int = 10000) -> Dict[str, object]:
        res = self.reachability_bfs(max_states=max_states)
        return {
            "place_order": res["place_order"],
            "states": res["states"],
            "edges": [{"from": f, "transition": t, "to": to} for (f, t, to) in res["edges"]],
            "deadlocks": res["deadlocks"],
            "truncated": res["truncated"],
        }

    #Exporte le graphe d'accessibilité au format DOT (Graphviz).
    def reachability_to_dot(self, max_states: int = 10000) -> str:
        res = self.reachability_bfs(max_states=max_states)

        order: List[str] = res["place_order"] 
        states: List[Dict[str, int]] = res["states"]
        edges: List[Tuple[int, str, int]] = res["edges"]
        deadlocks: List[int] = res["deadlocks"] 

        lines: List[str] = []
        lines.append("digraph Reachability {")
        lines.append("  rankdir=LR;")

        for i, m in enumerate(states):
            label = "\\n".join(f"{pid}={m.get(pid, 0)}" for pid in order)
            shape = "doublecircle" if i in deadlocks else "circle"
            lines.append(f'  S{i} [label="{label}", shape={shape}];')

        for f, t, to in edges:
            lines.append(f'  S{f} -> S{to} [label="{t}"];')

        if res.get("truncated"):
            lines.append('  truncated [label="TRUNCATED"];')

        lines.append("}")
        return "\n".join(lines)


#  Façade Frontend (JSON)

#Construit un objet PetriNet à partir d'un dictionnaire JSON (clé 'places','transitions', 'arcs'). 
#Sert de point d'entrée pour le frontend ou la ligne de commande.
def load_petri_from_dict(data: Dict[str, Any]) -> PetriNet:
    if not isinstance(data, dict):
        raise ValueError("data doit être un dict")

    for key in ("places", "transitions", "arcs"):
        if key not in data:
            raise ValueError(f"Clé manquante dans data: '{key}'")

    net = PetriNet()

    for p in data["places"]:
        if not isinstance(p, dict):
            raise ValueError("Chaque place doit être un dict")
        net.add_place(
            Place(
                id=p["id"],
                name=p.get("name", p["id"]),
                initial_tokens=int(p.get("initial_tokens", 0)),
            )
        )

    for t in data["transitions"]:
        if not isinstance(t, dict):
            raise ValueError("Chaque transition doit être un dict")
        net.add_transition(
            Transition(
                id=t["id"],
                name=t.get("name", t["id"]),
            )
        )

    for a in data["arcs"]:
        if not isinstance(a, dict):
            raise ValueError("Chaque arc doit être un dict")
        net.add_arc(
            Arc(
                source_id=a["source_id"],
                target_id=a["target_id"],
                weight=int(a.get("weight", 1)),
            )
        )

    return net


"""
Point d'entrée :
- charge le réseau à partir d'un dict,
- effectue l'analyse de reachability,
- renvoie à la fois le réseau, l'analyse, le graphe d'états (dict) et le DOT.
"""
def analyze_from_dict(data: Dict[str, Any], max_states: int = 10000) -> Dict[str, Any]:
    net = load_petri_from_dict(data)
    return {
        "network": net.to_dict(),
        "analysis": net.analyze_reachability(max_states=max_states),
        "reachability": net.reachability_to_dict(max_states=max_states),
        "dot": net.reachability_to_dot(max_states=max_states),
    }


def analyze_from_json_file(path: str, max_states: int = 10000) -> Dict[str, Any]:
    import json
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return analyze_from_dict(data, max_states=max_states)
