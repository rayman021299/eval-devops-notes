# Evaluation DevOps - ESIEA

[![CI](https://github.com/rayman021299/eval-devops-notes/actions/workflows/ci.yml/badge.svg)](https://github.com/rayman021299/eval-devops-notes/actions/workflows/ci.yml)
[![CD](https://github.com/rayman021299/eval-devops-notes/actions/workflows/cd.yml/badge.svg)](https://github.com/rayman021299/eval-devops-notes/actions/workflows/cd.yml)

Sylvain Bourgeois (S09-CSI)
Dépot GitHub : https://github.com/rayman021299/eval-devops-notes

--

## Commandes pour lancer le projet en local

Pour tester le projet, il faut avoir Docker et Docker Compose installés.


# Lancer toute la stack (app, redis et prometheus)
docker compose up -d --build

# Verifier l'état des conteneurs
docker compose ps

# Tester les routes de l'API
curl http://localhost:5000/health
curl -X POST http://localhost:5000/notes -H "Content-Type: application/json" -d '{"text": "premiere note"}'
curl http://localhost:5000/notes

# Arrêter les conteneurs
docker compose down

--

Les interfaces disponibles :
- API Flask : http://localhost:5000
- Metriques Prometheus brutes : http://localhost:5000/metrics
- Prometheus et alertes : http://localhost:9090/alerts

## Architecture et fonctionnement

- Application : API Flask qui enregistre et lit des notes dans un conteneur Redis.
- Docker : Dockerfile multi-stage avec une image finale python:3.12-slim et un utilisateur non-root (appuser). Gunicorn sert de serveur web et le healthcheck verifie /health avec urllib en Python.
- Docker Compose : orchestre web et redis (avec un volume redis-data pour garder les donnees) et attend que Redis soit prêt avec condition service_healthy.
- CI (ci.yml) : tourne à chaque PR et push sur main. Il lance 4 jobs :
  1. lint : flake8 pour le Python et yamllint pour les fichiers yaml.
  2. test : lance pytest sur Python 3.11 et 3.12 avec un conteneur service Redis, et sauvegarde le rapport de tests.
  3. build : vérifie la construction de l'image Docker.
  4. ci-ok : vérifie que tout est vert avant d'autoriser le merge.
  Une action locale dans .github/actions/setup-python-deps evite de dupliquer l'installation de Python, le cache pip et les dependances.
- CD (cd.yml) : tourne sur push sur main ou à la main avec workflow_dispatch. Il build et push l'image sur ghcr.io avec les tags latest, le SHA court du commit et 1.0.0. Ensuite le script deploy.sh teste le healthcheck avec 3 retries et fait un rollback automatique si le conteneur ne repond pas.

## Règles d'alerte Prometheus

Les regles sont dans observability/prometheus/alert_rules.yml :
- TauxErreurEleve : se déclenche si le taux d'erreur 5xx dépasse 5% pendant au moins 30 secondes (pour éviter les fausses alertes sur un glitch court).
- LatenceDegradee : se déclenche si le p95 de latence dépasse 500ms pendant plus de 1 minute.