import os
import time
from flask import Flask, jsonify, request, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
import redis

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Nombre total de requetes HTTP recues",
    ["method", "endpoint", "code"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Duree de traitement d'une requete HTTP, en secondes",
    ["method", "endpoint"],
)

APP_VERSION = Gauge(
    "app_version_info",
    "Version et commit SHA actuellement deployes",
    ["version", "commit_sha"],
)

APP_VERSION.labels(
    version=os.getenv("APP_VERSION", "1.0.0"),
    commit_sha=os.getenv("COMMIT_SHA", "dev"),
).set(1)


def get_redis_client():
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    return redis.Redis(host=redis_host, port=redis_port, decode_responses=True)


@app.before_request
def start_timer():
    request._metrics_start = time.perf_counter()


@app.after_request
def record_metrics(response):
    if request.path == "/metrics":
        return response
    endpoint = request.url_rule.rule if request.url_rule else "unmatched"
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        code=response.status_code,
    ).inc()
    if hasattr(request, "_metrics_start"):
        duration = time.perf_counter() - request._metrics_start
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)
    return response


@app.route("/health")
def health():
    try:
        client = get_redis_client()
        client.ping()
        return jsonify(status="ok", redis="up"), 200
    except redis.RedisError:
        return jsonify(status="error", redis="down"), 503


@app.route("/notes", methods=["GET"])
def get_notes():
    client = get_redis_client()
    notes = client.lrange("notes", 0, -1)
    return jsonify(notes=notes, count=len(notes)), 200


@app.route("/notes", methods=["POST"])
def add_note():
    data = request.get_json()
    if not data or not data.get("text"):
        return jsonify(error="Le champ text est requis"), 400

    client = get_redis_client()
    client.rpush("notes", data["text"])
    return jsonify(status="added", note=data["text"]), 201


@app.route("/simulate-error")
def simulate_error():
    return jsonify(error="Erreur simulee"), 500


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
