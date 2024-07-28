#!/bin/bash

# Renommer les fichiers .txt en .csv de manière récursive
find data -type f -name "*.txt" | while read file; do
    mv "$file" "${file%.*}.csv"
done
