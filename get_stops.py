from pymongo import MongoClient
import ellipse

def getStops(start, end):
    # Spécifier les informations d'identification
    username = "admin"
    password = "password"
    # Se connecter à la base de données MongoDB en incluant l'authentification
    client = MongoClient('localhost', 27017, username=username, password=password)
    db = client.test
    collection = db.stops

    polygone = {
        "type": "Polygon",
        "coordinates": [ ellipse.ellipse(start, end, 20) ]
    }

    resultats = collection.find({
        "location": {
            "$geoWithin": {
                "$geometry": polygone
            }
        }
    })

    return list(resultats)
