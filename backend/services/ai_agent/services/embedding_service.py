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
    """Generate text embedding using sentence-transformers (local, no API key)."""
    model = _get_model()
    embedding = model.encode(text_input.replace("\n", " "), normalize_embeddings=True)
    return embedding.tolist()


def upsert_producto_embedding(
    db: Session,
    producto_id: UUID,
    nombre: str,
    caracteristicas: str | None,
) -> None:
    """
    Generate and store embedding for a product.
    Text combines nombre + caracteristicas for richer semantic representation.
    """
    combined_text = f"{nombre}. {caracteristicas or ''}"
    embedding = get_embedding(combined_text)

    db.execute(
        text("""
            INSERT INTO producto_embedding (producto_id, embedding, model_name)
            VALUES (:producto_id, :embedding, :model_name)
            ON CONFLICT (producto_id, model_name)
            DO UPDATE SET embedding = EXCLUDED.embedding, updated_at = NOW()
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
    """
    Cosine similarity search using pgvector IVFFlat index.
    Returns top_k most semantically similar products.
    """
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
                1 - (pe.embedding <=> :query_embedding::vector) AS similarity
            FROM producto_embedding pe
            JOIN producto p ON p.id = pe.producto_id
            WHERE p.activo = TRUE
            {empresa_filter}
            ORDER BY pe.embedding <=> :query_embedding::vector
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
            "codigo": row.codigo,
            "nombre": row.nombre,
            "caracteristicas": row.caracteristicas,
            "empresa_nit": row.empresa_nit,
            "similarity": float(row.similarity),
        }
        for row in rows
    ]
