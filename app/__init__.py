"""Application package for the Plasma Engine Research service.

Detailed comments ensure future contributors can quickly identify the purpose of
each module. See app.main for the FastAPI application factory.
"""

from .main import create_app

__all__ = ["create_app"]

