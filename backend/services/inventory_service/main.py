from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import inventory

app = FastAPI(
    title="LiteThinking Inventory Service",
    description="PDF generation and email delivery for inventory exports",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory.router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": "inventory"}
