from flask_sqlalchemy import BaseQuery


def paginate_query(query: BaseQuery, page: int = 1, per_page: int = 10):
    """Return pagination for a SQLAlchemy query."""
    return query.paginate(page=page, per_page=per_page, error_out=False)
