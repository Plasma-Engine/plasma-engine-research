"""FastAPI application bootstrap for the Research service.

The goal of this file is to provide a tiny yet production-friendly scaffold
that Phase 1 engineers can extend with ingestion pipelines and GraphRAG APIs.
Every function carries descriptive comments to aid knowledge transfer.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ResearchSettings, get_settings


def create_app(settings: ResearchSettings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Parameters
    ----------
    settings:
        Optional override used primarily by tests to inject custom configuration.
    """

    # Prefer explicitly provided settings (mainly in tests); otherwise construct
    # a fresh instance so mutations in cached settings from other tests do not
    # leak into this application instance.
    resolved_settings = settings or ResearchSettings()

    app = FastAPI(title=resolved_settings.app_name)

    # Allow browser-based tooling to call the service while respecting configured origins.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.api_route("/health", methods=["GET", "HEAD"], tags=["health"])
    def health_check() -> dict[str, str]:
        """Simple health probe for Kubernetes and CI smoke tests."""

        return {"status": "ok", "service": resolved_settings.app_name}

    return app


app = create_app(get_settings())

