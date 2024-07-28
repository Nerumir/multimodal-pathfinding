import folium
from pymongo import MongoClient

# Spécifier les informations d'identification
username = "admin"
password = "password"
# Se connecter à la base de données MongoDB en incluant l'authentification
client = MongoClient('localhost', 27017, username=username, password=password)
db = client.test
collection = db.stops

resultats = collection.find({
    "location": {
        "$near": {
            "$geometry": {
                "type": "Point",
                "coordinates": [4.843649, 45.843649]  # Latitude et longitude de référence
            },
            "$maxDistance": 2000 # 5 kilomètres
        }
    }
})

data = list(resultats)
print(f"Nombre d'arrêts: {len(data)}")

# Créer une carte centrée
mymap = folium.Map(location=[data[0]['stop_lat'], data[0]['stop_lon']], zoom_start=12)

# Ajouter des marqueurs pour chaque élément dans les données
for point in data:
    folium.Marker([point['stop_lat'], point['stop_lon']], popup=point['stop_name']).add_to(mymap)

# Sauvegarder la carte dans un fichier HTML
mymap.save('map.html')
