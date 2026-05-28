"""
FastAPI application entry point for SophiaAI.

Executive Brief:
    create_app() builds the FastAPI instance: mounts routers, adds CORS
    middleware, and binds the lifespan context manager. The lifespan
    initializes all heavy objects once at startup — database engine,
    session factory, SophiaRetriever (FAISS + embedding model),
    GroqClient, and the Sophia orchestrator — and stores them on
    app.state so every request shares them.

Run:
    uvicorn sophia.app.main:app --reload
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sophia.db.database import Base, build_engine, build_session_factory

_APP_DIR = Path(__file__).resolve().parent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sophia.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executive Brief:
        Startup: create DB engine, create tables, build session factory,
        load AI objects (retriever, LLM client, orchestrator).
        Shutdown: dispose the engine.
    """
    logger.info("SophiaAI starting up ...")

    database_url = os.environ.get("DATABASE_URL", "sqlite:///./sophia_memory.db")
    engine = build_engine(database_url)
    Base.metadata.create_all(bind=engine)
    app.state.session_factory = build_session_factory(engine)
    app.state.jwt_secret = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")

    from sophia.core import Sophia
    from sophia.llm import GroqClient
    from sophia.rag import SophiaRetriever

    retriever = SophiaRetriever()
    llm_client = GroqClient()
    app.state.sophia = Sophia(retriever=retriever, llm_client=llm_client)

    logger.info("SophiaAI ready. Listening for requests.")
    yield

    engine.dispose()
    logger.info("SophiaAI shut down.")


def configure_assets(application: FastAPI) -> None:
    """
    Executive Brief:
        Mount static files at /static and attach a Jinja2Templates
        instance to app.state. Shared by create_app() and the test
        harness so both serve pages identically.

    Mental Model:
        Templates and static assets are resolved relative to this file
        (_APP_DIR), so they load the same regardless of the working
        directory the app is launched from.
    """
    application.mount(
        "/static",
        StaticFiles(directory=_APP_DIR / "static"),
        name="static",
    )
    application.state.templates = Jinja2Templates(directory=str(_APP_DIR / "templates"))


def create_app() -> FastAPI:
    """
    Executive Brief:
        Factory that assembles the FastAPI application.
        Registers routers, adds CORS middleware, binds the lifespan.
    """
    application = FastAPI(
        title="SophiaAI",
        description="A bridge between the Divine and Technology.",
        version="0.11.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    configure_assets(application)

    from sophia.app.routers import auth, chat, pages
    application.include_router(auth.router)
    application.include_router(chat.router)
    application.include_router(pages.router)

    return application


app = create_app()
