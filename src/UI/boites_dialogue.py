import tkinter as tk
from tkinter import simpledialog

def _init_tk():
    """
    Initialiser Tkinter sans afficher 
    la fenêtre principale vide (le problème 'fantôme').
    """
    root = tk.Tk()
    root.withdraw() # Cache la fenêtre principale
    return root

def ask_tokens():
    """
    Boîte de dialogue pour demander le nombre de jetons.
    Règles : Entier positif ou nul (>= 0).
    Retourne : L'entier saisi, ou None si l'utilisateur annule.
    """
    root = _init_tk()
    # minvalue=0 est important pour ne pas faire planter le backend
    val = simpledialog.askinteger("Place", "Nombre de jetons initiaux :", minvalue=0, initialvalue=0)
    root.destroy() # Nettoyage propre
    return val

def ask_weight():
    """
    Demander le poids d'un arc
    Règles : Entier strictement positif (>= 1).
    Retourne : L'entier saisi, ou None si l'utilisateur annule.
    """
    root = _init_tk()
    # minvalue=1 est OBLIGATOIRE (le backend refuse le poids 0)
    val = simpledialog.askinteger("Arc", "Poids de l'arc :", minvalue=1, initialvalue=1)
    root.destroy()
    return val