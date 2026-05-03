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
from app.api import routes, athletes, skills, rankings, keys, prospects, saved_searches  # noqa: E402
from app.api.exports import ns as exports_ns  # noqa: E402

api.add_namespace(exports_ns, path='/api/exports')
