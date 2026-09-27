import os
from flask import Flask, jsonify, request
import redis

app = Flask(__name__)


def get_redis_client():
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    return redis.Redis(host=redis_host, port=redis_port, decode_responses=True)


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
