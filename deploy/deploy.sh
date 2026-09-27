#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${1:-latest}"
PREVIOUS_TAG="${2:-previous}"
PORT=5000

echo "Déploiement de l'image tag : $IMAGE_TAG"

docker stop api-app 2>/dev/null || true
docker rm api-app 2>/dev/null || true
docker run -d --name api-app --network eval-devops-app_app-net -p ${PORT}:5000 "$IMAGE_TAG"

READY=0
echo "Vérification post-déploiement sur /health (3 essais)..."
for i in 1 2 3; do
    echo "Tentative $i/3..."
    if curl -sf "http://localhost:${PORT}/health" >/dev/null 2>&1; then
        READY=1
        echo "Healthcheck OK !"
        break
    fi
    sleep 3
done

if [ "$READY" -ne 1 ]; then
    echo "ERREUR : Le healthcheck a échoué après 3 tentatives."
    echo "Rollback auto vers la version précédente ($PREVIOUS_TAG)..."
    docker stop api-app 2>/dev/null || true
    docker rm api-app 2>/dev/null || true
    docker run -d --name api-app --network eval-devops-app_app-net -p ${PORT}:5000 "$PREVIOUS_TAG" || true
    exit 1
fi

echo "Déploiement réussi avec succès !"