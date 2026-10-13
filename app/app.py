import random
import time

from flask import Flask, Response, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)

REQUESTS = Counter(
    "app_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
LATENCY = Histogram(
    "app_request_duration_seconds", "Request latency in seconds", ["endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)


@app.before_request
def _start_timer():
    request._start = time.perf_counter()


@app.after_request
def _record(response):
    if request.path != "/metrics":
        LATENCY.labels(request.path).observe(time.perf_counter() - request._start)
        REQUESTS.labels(request.method, request.path, response.status_code).inc()
    return response


@app.get("/")
def index():
    return jsonify(service="demo-app", status="ok")


@app.get("/health")
def health():
    return jsonify(status="healthy")


@app.get("/api/items")
def items():
    return jsonify(items=[{"id": i, "name": f"item-{i}"} for i in range(5)])


@app.get("/slow")
def slow():
    time.sleep(random.uniform(0.2, 1.5))
    return jsonify(status="done")


@app.get("/error")
def error():
    if random.random() < 0.5:
        return jsonify(error="simulated failure"), 500
    return jsonify(status="lucky")


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
