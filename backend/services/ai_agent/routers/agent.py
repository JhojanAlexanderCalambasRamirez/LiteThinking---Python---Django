from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from decouple import config

from services.embedding_service import semantic_search_productos, upsert_producto_embedding
from services.langchain_agent import run_agent_query

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai-agent"])

DATABASE_URL = config(
    "DATABASE_URL",
    default="postgresql://postgres:postgres@localhost:5432/litethinking_db",
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


class AgentQueryRequest(BaseModel):
    query: str
    empresa_nit: str | None = None
    empresa_nombre: str | None = None


class SemanticSearchRequest(BaseModel):
    query: str
    empresa_nit: str | None = None
    top_k: int = 5


class EmbeddingUpsertRequest(BaseModel):
    producto_id: str
    nombre: str
    caracteristicas: str | None = None


@router.post("/agent/query/")
async def query_agent(payload: AgentQueryRequest, db: DbSession) -> dict:
    result = await run_agent_query(db, payload.query, payload.empresa_nit, payload.empresa_nombre)
    return {
        "query": payload.query,
        "response": result["response"],
        "productos_sugeridos": result["productos_sugeridos"],
    }


@router.post(
    "/agent/search/",
    responses={503: {"description": "Error en búsqueda semántica."}},
)
def semantic_search(payload: SemanticSearchRequest, db: DbSession) -> dict:
    try:
        results = semantic_search_productos(db, payload.query, payload.empresa_nit, payload.top_k)
        return {"query": payload.query, "results": results}
    except Exception:
        logger.exception("Semantic search error")
        raise HTTPException(status_code=503, detail="Error en búsqueda semántica.")


@router.post(
    "/agent/embeddings/upsert/",
    responses={
        422: {"description": "producto_id inválido."},
        503: {"description": "Error al indexar embedding."},
    },
)
def upsert_embedding(payload: EmbeddingUpsertRequest, db: DbSession) -> dict:
    try:
        upsert_producto_embedding(db, UUID(payload.producto_id), payload.nombre, payload.caracteristicas)
        return {"status": "ok", "producto_id": payload.producto_id}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"producto_id inválido: {exc}")
    except Exception:
        logger.exception("Embedding upsert error for %s", payload.producto_id)
        raise HTTPException(status_code=503, detail="Error al indexar embedding.")


@router.get("/blockchain/log/")
def get_blockchain_log(
    db: DbSession,
    entity_type: str | None = Query(None),
    limit: int = Query(50, le=200),
) -> dict:
    condition = "WHERE entity_type = :entity_type" if entity_type else ""
    params: dict = {"limit": limit}
    if entity_type:
        params["entity_type"] = entity_type

    rows = db.execute(
        text(f"""
            SELECT id, entity_type, entity_id, accion, data_hash,
                   tx_hash, block_number, network, created_at
            FROM blockchain_log
            {condition}
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        params,
    ).fetchall()

    return {
        "logs": [
            {
                "id": str(row.id),
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "accion": row.accion,
                "data_hash": row.data_hash,
                "tx_hash": row.tx_hash,
                "block_number": row.block_number,
                "network": row.network,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "on_chain": row.tx_hash is not None,
            }
            for row in rows
        ]
    }
