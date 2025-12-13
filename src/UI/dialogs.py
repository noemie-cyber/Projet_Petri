from tkinter import simpledialog

def ask_tokens():
    return simpledialog.askinteger("Place", "Nombre de jetons :", minvalue=0)
