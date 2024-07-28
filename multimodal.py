from datetime import datetime, timedelta
import osmnx as ox
import dijkstra as dij

class pf:

    VITESSE_PIETON = 4 # Vitesse de marche en km/h
    VITESSE_VOITURE = 30 # Vitesse moyenne d'une voiture en 30km/h
    
    def __init__(self, start, end, start_time, stops, radius,G):
        # Initialiser des variables dont on va se servir dans notre programme
        self.start = start
        self.end = end
        self.radius = radius
        self.G = G
        self.start_node = ox.nearest_nodes(self.G, self.start[1], self.start[0])
        self.end_node = ox.nearest_nodes(self.G, self.end[1], self.end[0])
        self.start_time = start_time
        self.stops = stops
        # Initialiser le tableau des chemins finaux avec le chemin où on fait tout à pied
        seconds = int(int(dij.pathf(self.start_node, self.end_node, self.G))/((1/3.6)*self.VITESSE_PIETON))
        time = self.addToTime(self.start_time, seconds)
        self.car_time = int(int(dij.pathf(self.start_node, self.end_node, self.G))/((1/3.6)*self.VITESSE_VOITURE))
        self.final_paths = [
            [{
                'node': ox.nearest_nodes(self.G, self.end[1], self.end[0]),
                'time': time,
                'wentBy': 'walk'
            }]
        ]

        # Initialiser les noeuds des arrêts
        self.stop_nodes = {}
        for stop in self.stops:
            elem = {
                'time': '23:59:59', # L'heure la plus tard possible
                'node': ox.nearest_nodes(self.G, float(stop['stop_lon']), float(stop['stop_lat']))
            }
            self.stop_nodes[stop['_id']] = elem
        # Initialiser current_paths avec la première étape
        self.current_paths = []
        actual_node = self.start_node
        actual_time = self.start_time
        for stop_id, stop in self.stop_nodes.items():
            # Eviter d'aller d'un point A à un point A...
            if(stop['node'] == actual_node):
                continue
            distance = int(dij.pathf(actual_node, stop['node'], self.G))
            # On suppose qu'on rejoint l'arrêt à un horaire cohérent
            real_stop = self.stopById(self.stopByNode(stop['node']))
            time = real_stop['times'][0]['arrival_time']
            for horaire in real_stop['times']:
                try:
                    if(self.toTime(time) >= self.toTime(horaire['arrival_time'])):
                        time = horaire['arrival_time']
                except Exception:
                    pass
            # Ajouter le node seul comme chemin
            if(self.shorterThanEver(stop['node'], time)):
                self.current_paths.append([{
                    'node': stop['node'],
                    'time': time,
                    'wentBy': 'walk'
                }])

    def pathf(self):
        # Tant que current_paths n'est pas vide
        i = 0
        while(self.current_paths):
            i += 1
            next_paths = []
            for current_path in self.current_paths:
                step = current_path[-1]
                # Si on est à l'arrivée, alors on l'ajoute au final_paths
                if step['node'] == self.end_node:
                    self.final_paths.append(current_path)
                    continue
                stop_of_step = self.stopById(self.stopByNode(step['node']))
                # On prend en compte les arrêts qu'on peut atteindre par le transport
                new_steps = []
                if(stop_of_step):
                    new_steps = self.reachable_stops(stop_of_step, step['time'])
                # On prend en compte le fait de marcher aux autres arrêts mais uniquement si le trajet précédent n'était pas à pied
                if(step['wentBy'] != 'walk'):
                    # On prend en compte la suite du chemin faite à pied
                    distance = int(dij.pathf(step['node'], self.end_node, self.G))
                    time = self.addToTime(step['time'], int(distance/((1/3.6)*self.VITESSE_PIETON)))
                    new_steps.append({
                        'node': self.end_node,
                        'time': time,
                        'wentBy': 'walk'
                    })
                    # Ne pas considérer les arrêts où l'on est moins rapide que déjà fait précédemment
                    for stop_id, stop in self.stop_nodes.items():
                        # Eviter d'aller d'un point A à un point A...
                        if(stop['node'] == step['node']):
                            continue
                        distance = int(dij.pathf(step['node'], stop['node'], self.G))
                        time = self.addToTime(step['time'], int(distance/((1/3.6)*self.VITESSE_PIETON)))
                        # Ajouter le node seul comme chemin
                        if(self.shorterThanEver(stop['node'], time)):
                            new_steps.append({
                                'node': stop['node'],
                                'time': time,
                                'wentBy': 'walk'
                            })
                # Créer les nouveaux chemins grâce aux nouvelles étapes générées
                for new_step in new_steps:
                    next_paths.append(current_path + [new_step])
            self.current_paths = next_paths

        # Sélection du chemin le plus rapide parmi tous ceux calculés
        better_path = self.final_paths[1]
        i = 0
        for path in self.final_paths:
            i += 1
            if(self.toTime(path[-1]['time']) <= self.toTime(better_path[-1]['time']) and path != self.final_paths[0]):
                better_path = path

        #Calcul du temps de trajet en transport
        self.transport_time = self.timeToSec(better_path[-1]['time']) - self.timeToSec(better_path[1]['time'])

        # Génération du résultat
        res = {
            'depart': {
                'type': 'Point',
                'coordinates': [
                    float(self.start[0]),
                    float(self.start[1])
                ]
            },
            'destination': {
                'type': 'Point',
                'coordinates': [
                    float(self.end[0]),
                    float(self.end[1])
                ]
            },
            'time_car': self.car_time + 300,
            'time_transport': self.transport_time,
            'ratio_car_transport': round( self.transport_time/self.car_time, 2),
            # La densité en arrêt par km²
            'stops_density': round(len(self.stops) / (self.radius/1000), 2),
            'steps': better_path
        }
        return res

    # Convertir un temps au format string en secondes
    def timeToSec(self, date_str):
        heures, minutes, secondes = map(int, date_str.split(':'))
        return heures * 3600 + minutes * 60 + secondes

    # Convertir l'heure en temps comparable
    def toTime(self, heure):
        return datetime.strptime(heure, "%H:%M:%S").time()

    def addToTime(self, heure, seconds):
        heure_time = datetime.strptime(heure, "%H:%M:%S")
        new_heure_time = heure_time + timedelta(seconds=seconds)
        return new_heure_time.strftime("%H:%M:%S")

    # Oui ou non si le node a été atteint en un temps plus court que ce qui a été enregistré jusqu'à présent
    # La fonction actualise aussi stop_nodes
    def shorterThanEver(self, node, time):
        for stop_id, stop in self.stop_nodes.items():
            if(stop['node'] == node):
                try:
                    if(self.toTime(time) <= self.toTime(stop['time'])):
                        self.stop_nodes[stop_id] = {
                            'node': node,
                            'time': time
                        }
                        return True
                except Exception:
                    pass
        return False

    # Si l'arrêt à été atteint en un temps plus court que ce qui est déjà présent dans la liste, alors on remplace.
    # Si il n'est pas dans la liste, alors on l'ajoute si il a été atteint plus rapidement qu'indiqué dans stop_nodes.
    # Optimisable car l'ordre est trié par horaire, mais je prends pas de risque.
    def addOrReplaceIfQuickest(self, new_stop, stops):
        exist = False
        for index, stop in enumerate(stops):
            if(new_stop['node'] != stop['node']):
                continue
            exist = True
            if(self.toTime(new_stop['time']) <= self.toTime(stop['time'])):
                stops[index] = new_stop
                return stops
        if(not exist):
            if(self.shorterThanEver(new_stop['node'], new_stop['time'])):
                stops.append(new_stop)
        return stops

    # Obtenir les informations d'un arrêt avec son id
    def stopById(self, stop_id):
        for stop in self.stops:
            if(stop['_id'] == stop_id):
                return stop
        return None
    
    # Obtenir un stop_id à partir du node
    def stopByNode(self, node):
        for stop_id, stop in self.stop_nodes.items():
            if(stop['node'] == node):
                return stop_id 
        return None

    # Obtenir l'horaire d'arrivée à un arrêt à partir du précédent et de l'horaire du précédent
    def nextStopTime(self, previous_stop, previous_time, stop_id):
        stop = self.stopById(stop_id)
        for passage in stop['times']:
            try:
                if(self.toTime(passage['arrival_time']) >= self.toTime(previous_time)):
                    return passage['arrival_time']
            except Exception:
                pass
        return '23:59:59'

    # Obtenir un arrêt par son nom
    def stopByName(self, stop_name):
        for stop in self.stops:
            if(stop['stop_id'] == stop_name):
                return stop
        return None

    # Liste des arrêts atteignables par transport à partir d'un arrêt à un temps donné
    # On prend pas en compte ceux qui sont atteint plus lentement que d'autres chemins
    def reachable_stops(self, stop, time):
        res = []
        for passage in stop['times']:
            new_stop = 'next_stop'
            if('next_stop' not in passage):
                new_stop = 'previous_stop'
                if('previous_stop' not in passage):
                    continue
            try:
                # Si il peut arriver à temps pour l'horaire et que le prochain arrêt est dans le scope on essaye de l'ajouter aux arrêts potentiellement atteignables
                if(self.toTime(passage['arrival_time']) >= self.toTime(time) and self.stopByName(passage[new_stop])):
                    next_stop_id = self.stopByName(passage[new_stop])['_id']
                    time = self.nextStopTime(stop, passage['arrival_time'], next_stop_id)
                    if(time != '23:59:59'):
                        res = self.addOrReplaceIfQuickest({
                            'node': self.stop_nodes[next_stop_id]['node'],
                            'time': time, # On ajoute le prochain arrêt avec son horaire d'arrivée
                            'wentBy': 'transport'
                        }, res)
            except Exception:
                pass
        return res

