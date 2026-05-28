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

    from sophia.app.routers import auth, chat, pages
    application.include_router(auth.router)
    application.include_router(chat.router)
    application.include_router(pages.router)

    return application


app = create_app()
