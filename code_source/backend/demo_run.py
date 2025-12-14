"""
Exemple d'utilisation du backend de réseau de Petri.

- construit un petit réseau en dur (2 places, 1 transition, 2 arcs),
- appelle la fonction d'analyse,
- affiche dans la console un résumé et les états atteignables.

Ce fichier sert uniquement de démonstration / test manuel.
"""

from petri import analyze_from_dict

data = {
    "places": [
        {"id": "P1", "name": "Input", "initial_tokens": 1},
        {"id": "P2", "name": "Output", "initial_tokens": 0},
    ],
    "transitions": [
        {"id": "T1", "name": "Move"},
    ],
    "arcs": [
        {"source_id": "P1", "target_id": "T1", "weight": 1},
        {"source_id": "T1", "target_id": "P2", "weight": 1},
    ],
}

# Appel du backend : analyse de reachability sur ce réseau simple
result = analyze_from_dict(data, max_states=1000)

# Affiche le résumé d'analyse et la liste des marquages atteints
print(result["analysis"])
print(result["reachability"]["states"])
