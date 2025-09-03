# GET /health
from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/", methods=["GET"])
def ok():
    return jsonify({"status": "ok"})
