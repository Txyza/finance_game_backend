"""Collection of Celery task modules."""

# Import task modules so Celery can register them on startup.
from . import daily, energy, monitoring  # noqa: F401
