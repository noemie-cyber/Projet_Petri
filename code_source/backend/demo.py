import json
from petri import analyze_from_dict

def main():
    print(" Petri quick tester")
    path = input("Chemin du JSON (ex: example.json) : ").strip()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = analyze_from_dict(data)

    print("\n ANALYSIS ")
    print(json.dumps(result["analysis"], indent=2, ensure_ascii=False))

    # Sauvegarde reachability + dot
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    with open("graph.dot", "w", encoding="utf-8") as f:
        f.write(result["dot"])

    print("\n Fichiers générés : result.json, graph.dot")

    # Optionnel : générer graph.png si graphviz est installé
    try:
        import subprocess
        subprocess.run(["dot", "-Tpng", "graph.dot", "-o", "graph.png"], check=True)
        print(" Image générée : graph.png")
    except Exception:
        print(" Impossible de générer graph.png automatiquement (Graphviz pas dispo ou dot pas dans PATH).")

if __name__ == "__main__":
    main()
