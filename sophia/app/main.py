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

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sophia.db.database import Base, build_engine, build_session_factory

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
        load AI objects (retriever, OpenRouter client, orchestrator).
        Shutdown: dispose the engine.
    """
    logger.info("SophiaAI starting up ...")

    database_url = os.environ.get("DATABASE_URL", "sqlite:///./sophia_memory.db")
    engine = build_engine(database_url)
    Base.metadata.create_all(bind=engine)
    app.state.session_factory = build_session_factory(engine)
    app.state.jwt_secret = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
    app.state.upload_dir = os.environ.get("FILES_UPLOAD_DIR", "data/user_uploads")

    from sophia.core import Sophia
    from sophia.llm import OpenRouterClient
    from sophia.rag import SophiaRetriever

    retriever = SophiaRetriever()
    llm_client = OpenRouterClient()
    app.state.sophia = Sophia(retriever=retriever, llm_client=llm_client)

    from sophia.core.corpus import CorpusLibrary
    app.state.corpus = CorpusLibrary()

    logger.info("SophiaAI ready. Listening for requests.")
    yield

    engine.dispose()
    logger.info("SophiaAI shut down.")


def create_app() -> FastAPI:
    """
    Executive Brief:
        Factory that assembles the FastAPI application as an API-only
        backend. Registers the JSON routers, adds CORS middleware for the
        Next.js client origin, and binds the lifespan. The HTML/Jinja2
        frontend has been retired in favour of the decoupled web/ client.
    """
    application = FastAPI(
        title="SophiaAI",
        description="A bridge between the Divine and Technology.",
        version="0.12.2",
        lifespan=lifespan,
    )

    # The browser talks to the Next.js BFF (same origin); the BFF talks to
    # this API server-side, so cross-origin browser calls are not the norm.
    # We allow the dev client origin for any direct calls during development.
    allowed_origins = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in allowed_origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from sophia.app.routers import auth, chat, corpus, files, images
    application.include_router(auth.router)
    application.include_router(chat.router)
    application.include_router(corpus.router)
    application.include_router(files.router)
    application.include_router(images.router)

    return application


app = create_app()
