#!/bin/bash

# Compter le nombre total de lignes dans les fichiers CSV
total_lines=0
find data -type f -name "stops.csv" | while read file; do
    lines=$(wc -l < "$file")
    total_lines=$((total_lines + lines))
    echo $total_lines
done
