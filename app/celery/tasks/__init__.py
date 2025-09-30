"""Collection of Celery task modules."""

# Import task modules so Celery can register them on startup.
from . import daily, energy, inventory, monitoring  # noqa: F401
