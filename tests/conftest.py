"""Pytest fixtures shared across the test suite (Agent5).

This module:
- Adds the project root to ``sys.path`` so ``app`` is importable.
- Patches ``TestingConfig`` to use a SQLite-friendly engine option set,
  because ``Config.SQLALCHEMY_ENGINE_OPTIONS`` includes ``pool_size`` /
  ``max_overflow`` which the SQLite (StaticPool) driver rejects.

The patch is intentionally scoped to the ``testing`` config so production
behavior is unaffected.
"""

import os
import sys

# Ensure repository root is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import TestingConfig  # noqa: E402

# Override engine options that don't apply to sqlite/static pool
TestingConfig.SQLALCHEMY_ENGINE_OPTIONS = {}

# Many tests follow the pattern::
#
#     with app_instance.app_context():
#         athlete = create_athlete()  # commits the row
#     # Then use ``athlete.athlete_id`` outside the with-block.
#
# After a commit SQLAlchemy expires loaded attributes, and once the context
# (and its session) closes, the instance becomes detached - any attribute
# access would attempt a refresh and raise ``DetachedInstanceError``. Disable
# expire-on-commit for the testing session so detached objects retain the
# values that were last loaded/refreshed; production behavior is unaffected.
TestingConfig.SQLALCHEMY_SESSION_OPTIONS = {"expire_on_commit": False}
