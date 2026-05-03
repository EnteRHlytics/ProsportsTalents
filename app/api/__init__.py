"""API blueprint setup using Flask-RESTX for documentation."""

from flask import Blueprint
from flask_restx import Api

bp = Blueprint("api", __name__, url_prefix="/api")

# Configure the RESTX Api with Swagger documentation at /api/swagger
api = Api(
    bp,
    title="Pro Sports API",
    version="1.0",
    description="Operations related to athletes",
    doc="/swagger",
)

# Prospect scouting namespace
prospects_ns = api.namespace('prospects', description='Prospect scouting')

# Import resources to register endpoints with this Api
from app.api import routes, athletes, skills, rankings, keys, prospects, upload_chunked  # noqa: E402
