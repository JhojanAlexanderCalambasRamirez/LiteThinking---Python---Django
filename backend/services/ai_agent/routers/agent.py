from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from decouple import config

from sqlalchemy import text

from services.embedding_service import semantic_search_productos, upsert_producto_embedding
from services.langchain_agent import run_agent_query

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
async def query_agent(
    payload: AgentQueryRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Natural language query to the LangChain inventory agent.
    The agent uses pgvector semantic search as a tool.
    """
    result = await run_agent_query(db, payload.query, payload.empresa_nit, payload.empresa_nombre)
    return {
        "query": payload.query,
        "response": result["response"],
        "productos_sugeridos": result["productos_sugeridos"],
    }


@router.post("/agent/search/")
def semantic_search(
    payload: SemanticSearchRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Direct pgvector semantic search without agent reasoning.
    Useful for autocomplete and quick product lookups.
    """
    results = semantic_search_productos(
        db, payload.query, payload.empresa_nit, payload.top_k
    )
    return {"query": payload.query, "results": results}


@router.post("/agent/embeddings/upsert/")
def upsert_embedding(
    payload: EmbeddingUpsertRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Generate and store/update embedding for a product.
    Called by Django backend after product create/update.
    """
    from uuid import UUID

    upsert_producto_embedding(
        db,
        UUID(payload.producto_id),
        payload.nombre,
        payload.caracteristicas,
    )
    return {"status": "ok", "producto_id": payload.producto_id}


@router.get("/blockchain/log/")
def get_blockchain_log(
    entity_type: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
) -> dict:
    """
    Return recent blockchain audit log entries.
    Filterable by entity_type: 'inventario' | 'empresa' | 'producto'
    """
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
