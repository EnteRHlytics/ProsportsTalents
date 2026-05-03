"""API blueprint setup using Flask-RESTX for documentation."""

from flask import Blueprint, Response
from flask_restx import Api

bp = Blueprint("api", __name__, url_prefix="/api")


class _PassThroughApi(Api):
    """Flask-RESTX ``Api`` subclass that returns Flask ``Response`` objects untouched.

    Some of our routes (which predate the RESTX migration) return values built
    with ``flask.jsonify(...)`` which yields a fully formed Flask ``Response``.
    Vanilla RESTX would then try to JSON-encode the response object itself and
    blow up with ``Object of type Response is not JSON serializable``. Detecting
    this case and short-circuiting keeps both flavours of return value working
    without rewriting every endpoint.
    """

    def make_response(self, data, *args, **kwargs):
        if isinstance(data, Response):
            # Flask-RESTX may also pass an explicit status code as the first
            # positional arg (``args[0]``) or as ``headers=`` kwarg. Apply
            # them so callers can still do ``return jsonify(x), 201``.
            if args and isinstance(args[0], int):
                data.status_code = args[0]
            headers = kwargs.get('headers') or {}
            for k, v in headers.items():
                data.headers[k] = v
            return data
        # RESTX commonly passes ``(payload, status, headers)`` tuples through
        # ``make_response``; we just need to handle the case where the first
        # element is already a Response.
        if isinstance(data, tuple) and data and isinstance(data[0], Response):
            resp = data[0]
            if len(data) > 1 and isinstance(data[1], int):
                resp.status_code = data[1]
            if len(data) > 2 and isinstance(data[2], dict):
                for k, v in data[2].items():
                    resp.headers[k] = v
            return resp
        return super().make_response(data, *args, **kwargs)


# Configure the RESTX Api with Swagger documentation at /api/swagger
api = _PassThroughApi(
    bp,
    title="Pro Sports API",
    version="1.0",
    description="Operations related to athletes",
    doc="/swagger",
)

# Prospect scouting namespace
prospects_ns = api.namespace('prospects', description='Prospect scouting')

# Import resources to register endpoints with this Api
from app.api import routes, athletes, skills, rankings, keys, prospects, saved_searches, upload_chunked  # noqa: E402
from app.api.exports import ns as exports_ns  # noqa: E402

api.add_namespace(exports_ns, path='/api/exports')
