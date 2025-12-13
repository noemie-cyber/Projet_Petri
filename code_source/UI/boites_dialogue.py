"""
Boîtes de dialogue simples pour demander des informations à l'utilisateur,
par exemple le nombre de jetons d'une place.
"""

from tkinter import simpledialog

def ask_tokens():
    return simpledialog.askinteger("Place", "Nombre de jetons :", minvalue=0)
