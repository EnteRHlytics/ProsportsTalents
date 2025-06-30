from flask import Blueprint

bp = Blueprint('athletes', __name__, url_prefix='/athletes')

from app.athletes import routes
