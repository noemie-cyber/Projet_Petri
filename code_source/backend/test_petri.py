"""
Tests unitaires pour le modèle de réseau de Petri (backend).

Vérifie que :
- les places ne peuvent pas avoir un nombre négatif de jetons,
- les arcs ont un poids strictement positif,
- on peut construire un petit réseau cohérent (places, transitions, arcs),
- les tables pre/post sont correctes,
- le tir d'une transition modifie bien le marquage sans toucher au marquage initial,
- le graphe d'accessibilité est correctement calculé (états, deadlocks),
- l'export JSON et DOT contient les informations attendues.

À lancer avec pytest.
"""

import pytest

from petri import PetriNet, Place, Transition, Arc



# Tests de base : Place / Transition / Arc


def test_place_cannot_have_negative_tokens():
    # Une place ne peut pas démarrer avec des tokens négatifs
    with pytest.raises(ValueError):
        Place("P1", "BadPlace", -1)


def test_arc_weight_must_be_positive():
    # Un arc doit avoir un poids >= 1
    with pytest.raises(ValueError):
        Arc("P1", "T1", 0)



# Construction d’un réseau simple


def test_can_add_places_transitions_and_arcs():
    net = PetriNet()

    net.add_place(Place("P1", "Input", 1))
    net.add_transition(Transition("T1", "Move"))
    net.add_arc(Arc("P1", "T1", 1))

    # On vérifie juste que tout est bien enregistré
    assert "P1" in net.places
    assert "T1" in net.transitions
    assert len(net.arcs) == 1



# Pre / Post : consommation et production


def test_build_pre_post_tables():
    """
    P1 --(2)--> T1 --(1)--> P2
    """
    net = PetriNet()
    net.add_place(Place("P1", "Input", 2))
    net.add_place(Place("P2", "Output", 0))
    net.add_transition(Transition("T1", "Move"))

    net.add_arc(Arc("P1", "T1", 2))   # consomme 2 tokens
    net.add_arc(Arc("T1", "P2", 1))   # produit 1 token

    pre, post = net.build_pre_post()

    assert pre["T1"] == [("P1", 2)]
    assert post["T1"] == [("P2", 1)]



# Tir d’une transition (fire)


def test_fire_changes_marking_but_not_original():
    """
    P1=2, P2=0
    après tir de T1 :
    P1=0, P2=1
    """
    net = PetriNet()
    net.add_place(Place("P1", "Input", 2))
    net.add_place(Place("P2", "Output", 0))
    net.add_transition(Transition("T1", "Move"))

    net.add_arc(Arc("P1", "T1", 2))
    net.add_arc(Arc("T1", "P2", 1))

    initial = net.initial_marking()
    result = net.fire("T1", initial)

    # Le marquage initial ne doit pas changer
    assert initial == {"P1": 2, "P2": 0}

    # Le nouveau marquage est correct
    assert result == {"P1": 0, "P2": 1}



# Reachability : graphe des états


def test_reachability_finds_deadlock():
    """
    Réseau très simple :
    P1=1 -> T1 -> P2=1
    Aucun tir possible après : deadlock
    """
    net = PetriNet()
    net.add_place(Place("P1", "Input", 1))
    net.add_place(Place("P2", "Output", 0))
    net.add_transition(Transition("T1", "Move"))

    net.add_arc(Arc("P1", "T1", 1))
    net.add_arc(Arc("T1", "P2", 1))

    res = net.reachability_bfs()

    assert res["truncated"] is False
    assert len(res["states"]) == 2
    assert res["deadlocks"] == [1]



# Analyse globale (résumé)


def test_analyze_reachability_summary():
    """
    Vérifie que l’analyse retourne les infos principales :
    - nombre d’états
    - deadlocks
    - max tokens par place
    """
    net = PetriNet()
    net.add_place(Place("P1", "Input", 1))
    net.add_place(Place("P2", "Output", 0))
    net.add_transition(Transition("T1", "Move"))

    net.add_arc(Arc("P1", "T1", 1))
    net.add_arc(Arc("T1", "P2", 1))

    analysis = net.analyze_reachability()

    assert analysis["num_states"] == 2
    assert analysis["max_tokens"]["P1"] == 1
    assert analysis["max_tokens"]["P2"] == 1



# Exports (JSON / DOT)


def test_export_json_and_dot():
    """
    Le backend doit pouvoir exporter :
    - la structure du réseau (JSON)
    - le graphe d’accessibilité (DOT)
    """
    net = PetriNet()
    net.add_place(Place("P1", "Input", 1))
    net.add_place(Place("P2", "Output", 0))
    net.add_transition(Transition("T1", "Move"))

    net.add_arc(Arc("P1", "T1", 1))
    net.add_arc(Arc("T1", "P2", 1))

    data = net.to_dict()
    dot = net.reachability_to_dot()

    assert "places" in data
    assert "transitions" in data
    assert "arcs" in data

    assert "digraph Reachability" in dot
    assert "S0" in dot
    assert "S1" in dot
