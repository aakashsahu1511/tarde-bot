from fastapi import FastAPI

from app.core.logging import setup_logging
from app.routes.health import router as health_router
from app.routes.kite_auth import router as kite_auth_router
from app.routes.kite_webhook import router as kite_webhook_router
from app.routes.sample import router as sample_router


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(
        title="Kite Stop Loss Service",
        version="0.1.0",
        description="A small FastAPI service to accept Kite order postbacks and place sell stop-loss orders for completed buy orders.",
    )
    app.include_router(health_router)
    app.include_router(kite_auth_router)
    app.include_router(kite_webhook_router)
    app.include_router(sample_router)
    return app


app = create_app()
