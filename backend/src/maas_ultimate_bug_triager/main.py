import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from maas_ultimate_bug_triager.api.bugs import router as bugs_router
from maas_ultimate_bug_triager.api.config import router as config_router
from maas_ultimate_bug_triager.config import AppConfig, load_config
from maas_ultimate_bug_triager.services.ai import AIService
from maas_ultimate_bug_triager.services.launchpad import LaunchpadService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger.info("MAAS Ultimate Bug Triager starting...")
    yield
    logger.info("MAAS Ultimate Bug Triager shutting down...")


def create_app(config: AppConfig | None = None) -> FastAPI:
    app = FastAPI(title="MAAS Ultimate Bug Triager", lifespan=lifespan)
    if config is None:
        try:
            config = load_config()
        except Exception:
            config = None
    app.state.config = config
    app.state.launchpad_service = None
    app.state.ai_service = None
    if config is not None:
        try:
            app.state.launchpad_service = LaunchpadService(config.launchpad)
        except Exception:
            pass
        try:
            app.state.ai_service = AIService(config.ai)
        except Exception:
            pass
    origins = ["http://localhost:5173"]
    if config is not None:
        origins = config.server.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(bugs_router)
    app.include_router(config_router)
    return app


def main() -> None:
    import uvicorn

    config = load_config()
    uvicorn.run(create_app(config), host=config.server.host, port=config.server.port)
