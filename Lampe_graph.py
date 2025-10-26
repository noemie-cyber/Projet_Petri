class Place:
    def __init__(self, name, tokens=0): #constructeur reçoit --> nom de la place, nombre de jetons
        self.name = name
        self.tokens = tokens

class Transition:
    def __init__(self, name):
        self.name = name
        self.input_arcs = [] #liste stockant les arcs en entrée
        self.output_arcs = [] # '' sortie 

    def ajoute_entree(self, place, poids=1): #ajoute un arc d’entrée
        self.input_arcs.append((place, poids))

    def ajoute_sortie(self, place, poids=1): #ajoute un arc de sortie
        self.output_arcs.append((place, poids))

    def est_franchissable(self): #vérifie s’il y a assez de jetons dans toutes les places en entrée
        return all(place.tokens >= poids for (place, poids) in self.input_arcs)

    def franchir(self): 
        if self.est_franchissable(): #si transition franchissable
            for (place, poids) in self.input_arcs:
                place.tokens -= poids  #retire les jetons de leur place en entrée
            for (place, poids) in self.output_arcs: 
                place.tokens += poids   #ajoute les jetons dans les places en sortie 
            return True
        return False

#ex : lampe torche
P1 = Place("Éteinte", tokens=1)
P2 = Place("Allumée", tokens=0)
T1 = Transition("Allumer")
T2 = Transition("Éteindre")

T1.ajoute_entree(P1)
T1.ajoute_sortie(P2)
T2.ajoute_entree(P2)
T2.ajoute_sortie(P1)

#franchir la transition Allumer
if T1.franchir():
    print(f"Lamp state: P1={P1.tokens}, P2={P2.tokens}")  #doit donner P1=0, P2=1
else:
    print("Allumer non possible")
