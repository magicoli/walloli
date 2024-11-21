#!/bin/bash

# Nombre de vidéos à générer, utiliser $1 si c'est un nombre, sinon 10
[ "$1" -eq "$1" ] 2>/dev/ && TOTAL_VIDEOS=$1 && shift || TOTAL_VIDEOS=10

# Répertoire de sortie pour les vidéos générées
OUTPUT_DIR="test_videos"
mkdir -p "$OUTPUT_DIR"

# Répertoire temporaire pour les images
TEMP_DIR="tests/temp_frames"
mkdir -p "$TEMP_DIR"

for i in $(seq 1 "$TOTAL_VIDEOS"); do
    filename="$OUTPUT_DIR/test-video-$i.mp4"
    [ -f "$filename" ] && echo Skiping $filename && continue
    # Durée aléatoire entre 5 et 20 secondes
    DURATION=$(( RANDOM % 16 + 5 ))

    echo "Génération de la vidéo $i avec une durée de $DURATION secondes."

    # Calculer le hue pour cette vidéo
    if [ "$TOTAL_VIDEOS" -gt 0 ]; then
        HUE=$(( (360 / TOTAL_VIDEOS) * (i - 1) ))
    else
        HUE=0
    fi
    HUE=$(( HUE % 360 ))  # S'assurer que le hue reste dans 0-359
    HSL_COLOR="hsl($HUE,50%,50%)"

    echo "Couleur de fond pour Vidéo $i : $HSL_COLOR"

    # Génération de résolutions aléatoires
    MIN_SIZE=720
    MAX_SIZE=1280

    # Générer des résolutions aléatoires multiples de 10 pour éviter des tailles non standard
    WIDTH=$(( (RANDOM % (MAX_SIZE - MIN_SIZE +1) + MIN_SIZE) / 10 * 10 ))  # 640 à 1920, multiple de 10
    HEIGHT=$(( (RANDOM % (MAX_SIZE - MIN_SIZE +1) + MIN_SIZE) / 10 * 10 ))  # 360 à 1080, multiple de 10

    echo "Résolution pour Vidéo $i : ${WIDTH}x${HEIGHT}"

    printf "Création des images : "
    # Génération des images pour la vidéo actuelle
    for (( s=0; s<DURATION; s++ )); do
        printf "."
        COUNTDOWN=$(( DURATION - s ))
        FRAME_NUMBER=$(printf "%03d" "$s")

        # Création de l'image avec ImageMagick
        magick -size "${WIDTH}x${HEIGHT}" "xc:$HSL_COLOR" \
            -gravity center \
            -font Arial -pointsize 100 -fill white \
            -annotate +0-100 "Test video $i\n${WIDTH}x${HEIGHT}" \
            -font Arial -pointsize 80 -fill yellow \
            -annotate +0+100 "Décompte: $COUNTDOWN" \
            "$TEMP_DIR/frame_${FRAME_NUMBER}.png"
    done
    echo

    # Assemblage des images en vidéo avec ffmpeg
    ffmpeg -y -framerate 1 \
        -i "$TEMP_DIR/frame_%03d.png" \
        -c:v libx264 -r 30 -pix_fmt yuv420p \
        "$filename"

    echo "Vidéo $i créée : $filename"

    # Nettoyage des images temporaires
    rm -f "$TEMP_DIR"/*.png
    sleep 0.1 # Allow quitting with Ctrl+C
done

# Suppression du répertoire temporaire
rmdir "$TEMP_DIR"

echo "Toutes les vidéos ont été générées dans le répertoire '$OUTPUT_DIR'."
