#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${1:-latest}"
PREVIOUS_TAG="${2:-previous}"
PORT=5000

echo "Deploiement de l'image tag : $IMAGE_TAG"

# 1. Creer le reseau Docker s'il n'existe pas encore
docker network create app-net 2>/dev/null || true

# 2. Demarrer le nouveau conteneur
docker stop api-app 2>/dev/null || true
docker rm api-app 2>/dev/null || true
docker run -d --name api-app --network app-net -e REDIS_HOST=redis -p ${PORT}:5000 "$IMAGE_TAG"

# 3. Verification post-deploiement : boucle curl avec 3 retries (Section 3.3)
READY=0
echo "Verification post-deploiement sur /health (3 essais)..."
for i in 1 2 3; do
    echo "Tentative $i/3..."
    if curl -sf "http://localhost:${PORT}/health" >/dev/null 2>&1; then
        READY=1
        echo "Healthcheck OK !"
        break
    fi
    sleep 3
done

# 4. Si echec : Rollback automatique vers l'ancien tag (Section 3.3)
if [ "$READY" -ne 1 ]; then
    echo "ERREUR : Le healthcheck a echoue apres 3 tentatives."
    echo "ROLLBACK AUTOMATIQUE : Re-demarrage de la version precedente ($PREVIOUS_TAG)..."
    docker stop api-app 2>/dev/null || true
    docker rm api-app 2>/dev/null || true
    docker run -d --name api-app --network app-net -e REDIS_HOST=redis -p ${PORT}:5000 "$PREVIOUS_TAG" || true
    exit 1
fi

echo "Deploiement reussi avec succes !"