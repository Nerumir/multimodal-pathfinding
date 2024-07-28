from pymongo import MongoClient

# Spécifier les informations d'identification
username = "admin"
password = "password"
# Se connecter à la base de données MongoDB en incluant l'authentification
client = MongoClient('localhost', 27017, username=username, password=password)
db = client.test

locations = [
    [(45.705807, 5.961191), 5000, 'Aix les bains' ], # Aix les bains
    [(46.113739, 5.820108), 5000, 'Bellegarde sur Valserine'], # Bellegarde sur Valserine
    [(43.330422, 5.424058), 2500, 'Marseille nord'], # Marseille nord
    [(43.279111, 5.393982), 2500, 'Marseille sud'], # Marseille sud
    [(43.524859, 5.443268), 5000, 'Aix en Provence'] # Aix en Provence
]

for location in locations:
    # Requête mongodb pour assigner la ville à chacun des éléments en fonction de leur position géographique
    cursor = db.paths.find({
        "depart": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [location[0][0], location[0][1]]
                },
                "$maxDistance": location[1]
            }
        }
    })
    for doc in cursor:
        db.paths.update_one(
            {"_id": doc["_id"]},
            {"$set": {"zone": location[2]}}
        )
