from __future__ import annotations

import hashlib
import json
import logging

from django.db import connection, transaction

logger = logging.getLogger(__name__)


def log_blockchain(entity_type: str, entity_id: str, action: str, data: dict) -> None:
    payload = {**data, "entity_type": entity_type, "action": action}
    data_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO blockchain_log (entity_type, entity_id, accion, data_hash)
                       VALUES (%s, %s, %s, %s)""",
                    [entity_type, entity_id, action, data_hash],
                )
    except Exception as exc:
        logger.warning("Blockchain log write failed (non-fatal): %s", exc)
