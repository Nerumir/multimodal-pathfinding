# Manipulation de données et algorithme de pathfinding multi-modal

## Introduction
principe du projet et but. Indiquer que le suivi et les explications détaillées sont dans le PDF de walkthrough

Le but de ce projet est de récolter une quantité importante de données concernant les arrêts de transports en commun en France ainsi que leurs horaires de passage. Le traitement et la réorganisation de ces données servent à calculer des chemins combinant marche à pied et transports en commun de type bus. J'ai ensuite créé un algorithme de pathfinding multi-modal pour calculer ce chemin d'un point de départ vers un point d'arrivée, tous deux aléatoires. Ce projet n'est absolument pas optimisé et sert uniquement de PoC.

## Collecte des données

Les données ont été récoltées sur le site du gouvernement `https://transport.data.gouv.fr` en OSINT à l'aide du script `scraper.py`. Certains noms de dossiers décompressés ont posé problème pour la suite, donc j'ai utilisé `rename_folders.sh` et `txt_to_csv.sh` pour travailler de manière plus confortable. Notons que les données récoltées sont au format `GeoJSON` qui est un format qui consiste à répartir les données sous forme de plusieurs fichiers `JSON` dont les informations sont interconnectées par clés étrangères à la manière de tables relationnelles.

## Manipulation distribuée des données

Pour avoir une idée de la taille des données récupérées, j'ai utilisé les scripts `count_stop_times.sh` et `count_stops.sh`, ce qui m'a permit de conclure que mes données contiennent un peu plus de `62 millions` de passages sur un total de plus de `300 000` arrêts. Réaliser le traitement et la réorganisation de ces données nécessite alors de réaliser plusieurs calculs en parallèle. Disposant d'une seule machine, il aurait été judicieux de ma part de réaliser cela directement avec le module Python `multiprocessing`. Cependant, pour rester dans la philosophie du PoC, il était plus judicieux et réaliste de faire une installation en culsters de containers Docker afin de faire du calcul distribué. Mon choix s'est porté sur `Spark`.

Voici le procédé d'installation que j'ai été amené à suivre :

```bash
# Créer les images docker (portforwarding 8080 et 7077 pour l'interface web des workers et l'accès pour le pyspark)
docker run -it -d -p 8080:8080 -p 7077:7077 --name maitre --hostname maitre debian:latest
docker run -d --name esclave --hostname esclave debian:latest

#Sur la machine maître et les esclaves installer Spark+Hadoop :

apt update
#Télécharger Spark
apt install wget net-tools curl vim iproute2 iputils-ping ssh locate -y
cd /root
wget https://dlcdn.apache.org/spark/spark-3.5.1/spark-3.5.1-bin-hadoop3-scala2.13.tgz
#Installer Java
apt install -y default-jre
apt install -y default-jdk
#Installer Spark
tar vxf spark-3.5.1-bin-hadoop3-scala2.13.tgz
cp -r spark-3.5.1-bin-hadoop3-scala2.13 /usr/local

#Sur le maître :

#Ajouter les PATH nécessaires
export PATH="$PATH:/usr/local/spark-3.5.1-bin-hadoop3-scala2.13/bin"
export PATH="$PATH:/usr/local/spark-3.5.1-bin-hadoop3-scala2.13/sbin"
export SPARK_EXECUTOR_MEMORY=10g
#Vérifier que l'installation s'est bien déroulée
spark-shell
curl localhost:4040

#Sur toutes les machines, setup SSH :

#Autoriser l'accès root dans la config ssh
vim /etc/ssh/sshd_config # Ajouter "PermitRootLogin yes" et "PasswordAuthentication yes" et "PubkeyAuthentication yes"
service ssh restart
#Choisir un mot de passe pour le compte root afin de se connecter en SSH
passwd root
#Générer une clé RSA et autoriser les connexions sans password (Spark en a besoin)
ssh-keygen -o -a 100 -t ed25519 -f ~/.ssh/id_ed25519
ssh-copy-id root@<IP_MACHINE_CIBLE>

#Sur toutes les machines :

locate spark-env.sh #Localiser les différents fichiers qu'on doit modifier
cp /usr/local/spark-3.5.1-bin-hadoop3-scala2.13/conf/spark-env.sh.template /usr/local/spark-3.5.1-bin-hadoop3-scala2.13/conf/spark-env.sh
vim /usr/local/spark-3.5.1-bin-hadoop3-scala2.13/conf/spark-env.sh #Ajouter export SPARK_MASTER_HOST="IP DU MAITRE"
cp /usr/local/spark-3.5.1-bin-hadoop3-scala2.13/conf/workers.template /usr/local/spark-3.5.1-bin-hadoop3-scala2.13/conf/workers
vim /usr/local/spark-3.5.1-bin-hadoop3-scala2.13/conf/workers #Ajouter les IP des workers donc l'esclave et le maître

#Sur la machine maître on démarre le cluster et on le teste avec un petit pyspark bidon :
/usr/local/spark-3.5.1-bin-hadoop3-scala2.13/sbin/start-all.sh # On se rend sur le port 8080 en web pour voir que l'on a accès à l'interface et que notre worker est bien présent
apt install python3 python3-venv
cd /root
mkdir scripts
cd scripts
python3 -m venv venv
source venv/bin/activate
pip install pyspark
vim test.py #Y coller le script de test
python test.py
# Transverser tout mon environnement pyspark
docker cp . maitre:/root/scripts/host
```

> [!TIP]
> Notez que j'ai utilisé la version déjà préparée pour `Hadoop`. Cependant, je ne vais pas l'utiliser car j'ai préféré utiliser `MongoDB` pour le stockage de mes données reformatées, pour des raisons de simplicité. Vous remarquerez d'ailleurs qu'utiliser une base de données de type `Graphe` aurait été un choix judicieux également.

Une fois l'installation terminée, j'ai pu exécuter le script `process_raw_data.py` avec `Spark` pour restructurer les données et ne garder que l'essentiel, sous une forme judicieuse pour la suite.

## Algorithme multi-modal

J'ai d'abord utilisé un algorithme de `pathfinding` basique pour le déplacement à pied présent dans le script `dijkstra.py`. Mon choix s'est porté sur Djikstra bien que l'algorithme soit simple, largement optimisable et pouvant même être considéré de naïf. Cependant, n'importe quel algorithme peut venir se greffer à l'algorithme principal multi-modal, ce n'est pas vraiment important pour la structure de celui-ci. Ainsi, pour calculer le trajet optimal entre deux points, je télécharge d'abord le graphe de la zone alentour (rues et passages faisable en voiture) et puis je me sers des différents arrêts présents en base de données pour calculer le chemin le plus court à l'aide de l'algorithme multi-modal.

### Fonctionnement de l'algorithme

L'idée que j'ai eu pour le fonctionnement de cet algorithme est la suivante :

- Initialiser un tableau vide des chemins complétés `final_paths`.
- Initialiser un tableau des chemins qui sont en train d'être explorés `current_paths`, contenant que le nœud de départ.
- Un tableau contenant tous les arrêts de la zone `stops`.
- Un tableau `stop_nodes` associant les `stop_id` à un temps de chemin minimal pour lequel il a été atteint et son nœud le plus proche sur le graphe.
- On boucle et pour chaque élément de `current_paths` on créé :
  - Un nouveau chemin par arrêt que l'on peut atteindre par transport depuis l'arrêt actuel (position actuelle).
  - Un nouveau chemin par autre arrêt à pied (même si l'arrêt est atteignable via cet arrêt par transport par l'intermédiaire de plusieurs arrêts, il sera éventuellement atteint par un des chemins créé à l'étape d'avant dans les prochaines itérations)
  - Un nouveau chemin qui va directement à l'arrivée à pied.
- Si les arrêts sont atteints en moins de temps que ce qui est indiqué dans `stop_nodes`, alors ils apparaîtront dans le nouveau tableau `current_paths`. Il sera vidé au préalable. Si le chemin est à l'arrivée, alors il sera ajouté dans `final_paths` à la place.
- La boucle s'arrête lorsque `current_paths` est vide.
- On rend finalement le chemin le plus court contenu dans `final_paths`.

> [!TIP]
> J'aurais pu m'épargner le stockage de tous les chemins terminés et donc le calcul du plus court en ne retenant un chemin complet uniquement en remplaçant le dernier sauvegardé si celui-ci était plus long. Je n'y avais pas pensé lors de la conception de l'algorithme, mais le code est de toute manière optimisable à bien des égards. Le principe en revanche, me semble assez optimal. Le GIF ci-dessous illustre son fonctionnement.

![Pathfinding multi-modal](https://github.com/Nerumir/multimodal-pathfinding/blob/main/pf-multimodal.gif)

L'algorithme est présent dans le script `multimodal.py`. Il est ensuite utilisé pour générer plusieurs chemins afin de créer des données qui pourront, à terme, être utilisées et interprétées.

### Optimisations

Une chose qui a été faite pour optimiser la rapidité de l'algorithme est de diminuer le nombre d'arrêts (complexité quadratique par rapport à ces derniers) en les choisissant de manière judicieuse. Pour cela, j'ai créé une ellipse avec comme centres, les deux points (départ et arrivée).

![Ellipse](https://github.com/Nerumir/multimodal-pathfinding/blob/main/ellipse_vs_circle.png)

J'ai réalisé cet algorithme en 8 heures, il est donc fortement optimisable sur le plan technique du code, plusieurs astuces me sont déjà venu en tête après l'avoir terminé. Cependant, le projet en lui même peut être optimisé également et de plusieurs manières. Voici quelques améliorations possibles en l'état :

- Il aurait été possible de fusionner la position de certains arrêts qui sont assez proches et de simplement concaténer leurs horaires, sans oublier de modifier les `stop_id` pour conserver la cohérence de cette fusion.
- Il aurait été possible de supprimer les arrêts de gare par exemple et de garder seulement les bus. Cependant, cela demande des opérations de filtre avancées en fonction par exemple de la distance relative des arrêts entre eux.
- En parallélisant les calculs sur plusieurs serveurs, nous aurions aussi pu diviser le temps de calcul pour les masses et pré-calculer un nombre important de trajets afin de créer un graphe prenant directement en compte les transports.
- Avec plus de temps, il aurait été possible d'apporter ce genre d'optimisation, mais surtout avec beaucoup plus de ressources système. Cependant, je ne pense pas que l'algorithme soit plus améliorable, à cause des horaires, il est nécessaire de parcourir au moins chaque arrêt par étape et le considérer si nous y arrivons en un temps inférieur à ce qui a déjà été fait.

Et quelques améliorations possibles avec beaucoup plus de temps et de ressources :

- Evaluer de manière précise la pertinence de la zone elliptique.
- Amélioration de la qualité du `dataset` de départ.
- Calcul distribué sur plusieurs machines pour une croissance horizontale des performances.
- Création de plusieurs graphes dépendant du temps avec les trajets possibles à l'horaire du graphe en tant qu'arêtes.
- Amélioration  de l'algorithme de `pathfinding` de marche à pied en implémentant par exemple du bidirectionnel.
- Mise au propre de l'algorithme et optimisation des calculs.
- Ignorer les arrêts isolés de l'ellipse. (pour lesquels aucun trajets ne sont possibles dans la zone)
- Modifier la structure de stockage des données pour s'orienter sur du graphe.
- Si l'algorithme sert dans le cadre d'une utilisation de navigation GPS, un système de cache mutualisé peut être mis en place pour se servir des calculs passés et augmenter la rapidité de service tout en réduisant la charge de calcul.

## Visualisation

Il est possible ensuite, selon la pertinence des données générées, de tirer des conclusions et d'interpréter les résultats. Sur le principe, une version aboutie de ce projet pourrait servir pour optimiser la disposition des arrêts de transport en commun en milieu urbain, mais aussi la répartition de leurs horaires, en recoupant les données avec des informations supplémentaires comme la densité d'usagers en fonction du temps. Cela permettrait alors d'évaluer de manière efficace la pertinence de la disposition des arrêts.
