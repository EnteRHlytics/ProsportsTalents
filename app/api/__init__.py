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

# Import resources to register endpoints with this Api
from app.api import routes, athletes, skills, rankings, keys  # noqa: E402
