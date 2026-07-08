from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
_EMBEDDING_DIM = 384

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_EMBEDDING_MODEL)
    return _model


def get_embedding(text_input: str) -> list[float]:
    model = _get_model()
    embedding = model.encode(text_input.replace("\n", " "), normalize_embeddings=True)
    return embedding.tolist()


def upsert_producto_embedding(
    db: Session,
    producto_id: UUID,
    nombre: str,
    caracteristicas: str | None,
) -> None:
    combined_text = f"{nombre}. {caracteristicas or ''}"
    embedding = get_embedding(combined_text)

    db.execute(
        text("""
            INSERT INTO producto_embedding (producto_id, embedding, model_name)
            VALUES (:producto_id, CAST(:embedding AS vector), :model_name)
            ON CONFLICT (producto_id, model_name)
            DO UPDATE SET embedding = CAST(EXCLUDED.embedding AS vector), updated_at = NOW()
        """),
        {
            "producto_id": str(producto_id),
            "embedding": str(embedding),
            "model_name": _EMBEDDING_MODEL,
        },
    )
    db.commit()
    logger.info("Embedding upserted for producto %s", producto_id)


def semantic_search_productos(
    db: Session,
    query: str,
    empresa_nit: str | None = None,
    top_k: int = 5,
) -> list[dict]:
    query_embedding = get_embedding(query)

    empresa_filter = "AND p.empresa_nit = :empresa_nit" if empresa_nit else ""

    rows = db.execute(
        text(f"""
            SELECT
                p.id,
                p.codigo,
                p.nombre,
                p.caracteristicas,
                p.empresa_nit,
                e.nombre AS empresa_nombre,
                inv.id AS inventario_id,
                inv.cantidad AS stock,
                1 - (pe.embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM producto_embedding pe
            JOIN producto p ON p.id = pe.producto_id
            JOIN empresa e ON e.nit = p.empresa_nit
            LEFT JOIN inventario inv ON inv.producto_id = p.id
            WHERE p.activo = TRUE
            {empresa_filter}
            ORDER BY pe.embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """),
        {
            "query_embedding": str(query_embedding),
            "empresa_nit": empresa_nit,
            "top_k": top_k,
        },
    ).fetchall()

    return [
        {
            "id": str(row.id),
            "inventario_id": str(row.inventario_id) if row.inventario_id else None,
            "codigo": row.codigo,
            "nombre": row.nombre,
            "caracteristicas": row.caracteristicas,
            "empresa_nit": row.empresa_nit,
            "empresa_nombre": row.empresa_nombre,
            "stock": int(row.stock) if row.stock is not None else 0,
            "similarity": float(row.similarity),
        }
        for row in rows
    ]
