from math import radians, sin, cos, sqrt, atan2
import osmnx as ox
import random
import multiprocessing as mp
import multimodal as cust
import get_stops
import json
import sys
import os

# Réunir tous les fichiers json du dossier spécifié en un seul.
def merge_jsons(folder):
    res = []
    for fichier in os.listdir(folder):
        if fichier.endswith(".json"):
            chemin_fichier = os.path.join(folder, fichier)
            with open(chemin_fichier, "r") as file:
                data = json.load(file)
                res.append(data)
    res_file = "result.json"
    with open(res_file, "w") as new_file:
        json.dump(res, new_file, indent=4)

merge_jsons('data')
sys.exit(0)

nb_chemins = 50 # Nombre de chemins à calculer par lieu

locations = [
    # [(45.705807, 5.961191), 2000], # Aix les bains
    # [(46.113739, 5.820108), 1200], # Bellegarde sur Valserine
    # [(43.330422, 5.424058), 1000], # Marseille nord
    # [(43.279111, 5.393982), 1000], # Marseille sud
    [(43.524859, 5.443268), 900] # Aix en Provence
]

def compute_pf(G):
    # On sélectionne deux points au hasard
    start, end = get_start_goal_nodes(G)
    start = (G.nodes[start]['y'], G.nodes[start]['x'])
    end = (G.nodes[end]['y'], G.nodes[end]['x'])
    # Récupérer les arrêts de manière optimisée
    stops = get_stops.getStops((start[1], start[0]), (end[1], end[0]))
    # On approxime le rayon pour le calcul de densité des arrêts à la distance entre le point d'arrivée et de départ
    radius = int(haversine_distance(start[1], start[0], end[1], end[0])*1.5)
    # Calculer le chemin avec l'algorithme de pathfinding
    if(len(stops) >= 200):
        return
    print(f"Calcul avec {len(stops)} arrêts..")
    path = cust.pf(start, end, '11:20:00', stops, radius, G)
    result = path.pathf()
    print(result)
    print("Calcul terminé !")
    # enregistrer le résultat dans un json
    with open(f"data/part-{str(random.randint(1, 999999)).zfill(6)}.json", "w") as fichier:
        json.dump(result, fichier)

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Rayon de la Terre en mètres
    # Conversion des degrés en radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    # Calcul des écarts en latitudes et longitudes
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    # Formule de la distance haversine
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# Je choisis deux noeuds aléatoires sur le graphe donné
def get_start_goal_nodes(G):
    nodes = list(G.nodes)
    start = random.choice(nodes)
    goal = random.choice(nodes)
    while start == goal:
        goal = random.choice(nodes)
    return start, goal

# On boucle sur tous les lieux
for location in locations:
    # On calcule le graphe pour le lieu
    G = ox.graph_from_point(location[0], location[1], network_type='walk', simplify=True)
    # On calcule "nb_chemins" chemins en parallèle
    with mp.Pool() as p:
        p.starmap(compute_pf, [(G,) for i in range(nb_chemins)])
