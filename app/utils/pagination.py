from sqlalchemy.orm import Query
from typing import Union


def paginate_query(query: Union[Query, object], page: int = 1, per_page: int = 10):
    """Return pagination for a SQLAlchemy query."""
    return query.paginate(page=page, per_page=per_page, error_out=False)
