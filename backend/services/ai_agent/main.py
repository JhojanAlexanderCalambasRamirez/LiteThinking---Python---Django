from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import agent

app = FastAPI(
    title="LiteThinking AI Agent",
    description="Semantic search and AI agent for inventory queries using pgvector + LangChain",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent.router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": "ai-agent"}
