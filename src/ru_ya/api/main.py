from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ru_ya import __version__
from ru_ya.api.routes_sessions import router as sessions_router
from ru_ya.api.routes_sources import router as sources_router

app = FastAPI(
    title="Ru-ya API",
    version=__version__,
    description="Cite-or-abstain Islamic dream interpretation assistant",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router, prefix="/api/v1")
app.include_router(sources_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "version": __version__}
