#!/bin/bash

# Fonction récursive pour renommer les dossiers
rename_folders() {
    local dir="$1"
    local count=1

    # Parcours de tous les dossiers dans le répertoire spécifié
    for folder in "$dir"/*/; do
        if [ -d "$folder" ]; then
            # Renommer le dossier avec un numéro
            new_name="$dir/$count"
            mv "$folder" "$new_name"

            echo "Renommé : $folder en $new_name"
            ((count++))

            # Appel récursif sur chaque sous-dossier
            rename_folders "$new_name"
        fi
    done
}

# Appeler la fonction pour démarrer le processus de renommage
rename_folders "data"
