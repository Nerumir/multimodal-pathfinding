import heapq
from functools import lru_cache

# Fonction pour retrouver le chemin jusqu'au départ une fois l'arrivée atteinte.
def reconstruct_path(start, goal, predecessors):
    path = [goal]
    while path[-1] != start:
        path.append(predecessors[path[-1]])
    path.reverse()
    return path

# Déterminer les prochains nodes à partir du précédent pour la propagation du dijkstra
@lru_cache(maxsize=None)
def successors(G,node):
    neighbors = list(G.neighbors(node))
    successors = [(neighbor, G[node][neighbor][0]['length'])
                  for neighbor in neighbors]
    return successors
 
# Fonction de l'algo de Dijkstra
def dijkstra(G, start, goal):
    # Calculer la distance de chaque noeud par rapport à celui de départ
    distances = {node: float('inf') for node in G.nodes}
    distances[start] = 0  # Distance du noeud de départ, c'est forcément 0
    visited = set()  # Pour stocker les noeuds déjà visités
    queue = [(0, start)]  # Queue de priorité (avec les éléments distance/noeud)
    predecessors = {node: None for node in G.nodes}
	# Tant qu'il y a au moins un élément dans la queue
    while queue:
	    # On traite le prochain élément de la queue
        current_distance, current_node = heapq.heappop(queue)
		 # Si c'est l'arrivée, on arrête et on rend la distance, donc le résultat
        if current_node == goal:
            return distances[goal]
		 # Si le noeud a traiter a déjà été visité, on ignore
        if current_node in visited:
            continue
		 #On ajoute ce noeud à la liste des noeuds visités
        visited.add(current_node)
		 # On boucle sur les prochains noeuds après celui-ci
        for neighbor, weight in successors(G, current_node):
	        # On calcul la distance si on atteint le noeud suivant concerné
            new_distance = current_distance + weight
            # Si la distance est inférieur à celle que l'on avait mis pour ce voisin
            # (ça fonctionne car au début on avait mis les valeurs de distances à l'infini)
            if new_distance < distances[neighbor]:
		        # Alors on rempli la case des distances et les predecessors.
                distances[neighbor] = new_distance
                predecessors[neighbor] = current_node
                # On ajoute également les prochains noeuds à la pile pour continuer la propagation de l'algo
                heapq.heappush(queue, (new_distance, neighbor))
 
    return float('inf'), []  # Si on arrive ici, aucun chemin n'a été trouvé
 
# Renvoie le nombre de mètres à parcourir
def pathf(start,end,G):

    # Lancer l'alogirthme de Dijkstra sur les deux noeuds
    dijkstra_cost = dijkstra(G, start, end)
    # Rendre le résultat
    if dijkstra_cost != float('inf'):
        return dijkstra_cost
    else:
        return None
