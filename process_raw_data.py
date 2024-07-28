from pyspark.sql import SparkSession
from pyspark.sql.functions import collect_list, struct
from pyspark.sql.window import Window
from pyspark.sql.functions import lag, lead
import os

def recup_doss(dossier):
    tab = os.listdir(dossier)
    res = []
    for i in range(len(tab)):
        if (os.path.isdir(dossier + "/" + tab[i])):
            res.append(tab[i])
    return(res)

def navig_rec(dossier,res,visited):
    subs = recup_doss(dossier)
    for i in range(len(subs)):
        res.append(dossier + "/" + subs[i])
        if ((dossier + "/" + subs[i]) not in visited):
            visited.append(dossier + "/" + subs[i])
            res = navig_rec(dossier + "/" + subs[i],res,visited)
    return(res)

def csv_groups(dossier):
    folders = navig_rec(dossier,[],[])
    res = []
    for folder in folders:
        if os.path.isfile(folder+'/stop_times.csv'):
            res.append(folder)
    return res

def compute_jsons(dossier):

    # Créer une session Spark
    spark = SparkSession.builder \
        .appName("Réunir nos CSV dans un unique JSON") \
        .master("spark://172.17.0.2:7077") \
        .getOrCreate()

    for folder in csv_groups('data'):

        if(os.path.isfile(folder+'/stops.csv') and os.path.isfile(folder+'/stop_times.csv') and os.path.isfile(folder+'/trips.csv')):

            # Liste des arrêts
            df_stops = spark.read.option("header", "true").csv(folder+'/stops.csv')

            # Liste des horaires des arrêts pour les différentes lignes
            # Déjà trié par trip_id puis arrival_time, donc c'est parfait pour nous.
            df_stop_times = spark.read.option("header", "true").csv(folder+'/stop_times.csv')

            # Lister les différentes lignes, on va y récupérer la direction.
            df_trips = spark.read.option("header", "true").csv(folder+'/trips.csv')

            # Définir la fenêtre de partition par trip_id et trié par arrival_time
            windowSpec = Window.partitionBy("trip_id").orderBy("arrival_time")

            # Ajouter les colonnes previous_stop et next_stop à notre df
            df_stop_times = df_stop_times.withColumn("previous_stop", lag("stop_id", 1).over(windowSpec)).withColumn("next_stop", lead("stop_id", 1).over(windowSpec))

            # Ajouter la colonne direction à notre df
            combined_df = df_stop_times.join(df_trips, df_stop_times["trip_id"] == df_trips["trip_id"], "inner")
            df_stop_times = combined_df.select(
        df_stop_times["trip_id"],
        df_stop_times["arrival_time"],
        df_stop_times["departure_time"],
        df_stop_times["stop_id"],
        df_stop_times["previous_stop"],
        df_stop_times["next_stop"],
        df_trips["direction_id"]
    )
            df_stop_times = df_stop_times.withColumnRenamed("direction_id", "direction")

            # Sélectionner les colonnes nécessaires dans les tables
            df_stops_data = df_stops.select("stop_id", "stop_name", "stop_lon", "stop_lat")
            df_stop_times_data = df_stop_times.select("stop_id", "arrival_time", "direction", "next_stop", "previous_stop")

            # Joindre les données des deux tables sur stop_id
            combined_data = df_stops_data.join(df_stop_times_data, "stop_id", "inner")

            # Regrouper les données par stop_id et collecter les valeurs dans une colonne
            grouped_data = combined_data.groupBy("stop_id", "stop_name", "stop_lon", "stop_lat") \
                                        .agg(collect_list(struct("arrival_time", "direction", "next_stop", "previous_stop")).alias("times"))

            # Convertir les données regroupées en format JSON et afficher le résultat
            json_data = grouped_data.toJSON().collect()


            # Ajout de des stops en JSON dans le fichier de sortie
            with open(output_file_path, 'a') as file:
                for line in json_data:
                    file.write("\n" + line)
                    file.write(",")

    spark.stop()

#Chemin pour sauvegarder en fichier JSON
output_file_path = "formatted.json"

# Initialisation du JSON dans le fichier de sortie
with open(output_file_path, 'w') as file:
    file.write("[")

compute_jsons('data')

# Fermeture du JSON dans le fichier de sortie
with open(output_file_path, 'rb+') as file:
    file.seek(-1, os.SEEK_END)  # Positionner le curseur sur l'avant-dernier caractère
    last_char = file.read(1).decode()  # Lire le dernier caractère
    if last_char == ",":
        file.truncate()  # Supprimer le dernier caractère s'il s'agit d'une virgule
with open(output_file_path, 'a') as file:
    file.write("]")

