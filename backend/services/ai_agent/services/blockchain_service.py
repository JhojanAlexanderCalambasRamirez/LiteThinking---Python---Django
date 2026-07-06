"""
Blockchain audit service using web3.py.
Records inventory operations as immutable on-chain events (Polygon Mumbai testnet).
Falls back to local SHA256 hash log if chain is unavailable.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone

from decouple import config
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

_CHAIN_ENABLED = config("BLOCKCHAIN_ENABLED", default=False, cast=bool)
_RPC_URL = config("BLOCKCHAIN_RPC_URL", default="https://rpc-mumbai.maticvigil.com")
_PRIVATE_KEY = config("BLOCKCHAIN_PRIVATE_KEY", default="")
_CONTRACT_ADDRESS = config("BLOCKCHAIN_CONTRACT_ADDRESS", default="")


def _compute_data_hash(data: dict) -> str:
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def record_inventory_event(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    data: dict,
) -> str:
    """
    Record an inventory event.
    1. Computes SHA256 hash of the event data.
    2. Attempts to write the hash on-chain (Polygon Mumbai).
    3. Always persists to blockchain_log table (with or without tx_hash).
    Returns the data_hash for verification.
    """
    data_hash = _compute_data_hash({**data, "entity_type": entity_type, "action": action})
    tx_hash = None
    block_number = None
    network = None

    if _CHAIN_ENABLED and _PRIVATE_KEY:
        try:
            from web3 import Web3

            w3 = Web3(Web3.HTTPProvider(_RPC_URL))
            if w3.is_connected():
                account = w3.eth.account.from_key(_PRIVATE_KEY)
                nonce = w3.eth.get_transaction_count(account.address)
                tx = {
                    "nonce": nonce,
                    "to": account.address,
                    "value": 0,
                    "gas": 21000,
                    "gasPrice": w3.eth.gas_price,
                    "data": w3.to_hex(text=data_hash),
                    "chainId": w3.eth.chain_id,
                }
                signed = account.sign_transaction(tx)
                tx_hash_bytes = w3.eth.send_raw_transaction(signed.rawTransaction)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=30)
                tx_hash = tx_hash_bytes.hex()
                block_number = receipt.blockNumber
                network = "polygon-mumbai"
                logger.info("Blockchain event recorded. tx_hash=%s block=%s", tx_hash, block_number)
        except Exception as exc:
            logger.warning("Blockchain write failed (non-fatal): %s", exc)

    db.execute(
        text("""
            INSERT INTO blockchain_log
                (entity_type, entity_id, accion, data_hash, tx_hash, block_number, network)
            VALUES
                (:entity_type, :entity_id, :accion, :data_hash, :tx_hash, :block_number, :network)
        """),
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "accion": action,
            "data_hash": data_hash,
            "tx_hash": tx_hash,
            "block_number": block_number,
            "network": network,
        },
    )
    db.commit()
    return data_hash
