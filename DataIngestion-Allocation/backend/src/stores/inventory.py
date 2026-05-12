"""
inventory.py — Inventory store operations
All Supabase inventory reads and writes.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from supabase import create_client, Client

logger = logging.getLogger("INVENTORY_STORE")

# ── Supabase client (lazy singleton) ────────────────────────────────────────

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _client = create_client(url, key)
    return _client


# ── Public interface ────────────────────────────────────────────────────────

def fetch_inventory() -> list[dict[str, Any]]:
    """
    Return all rows from the inventory table, ordered by item_type then item_name.
    Each row: {id, item_type, item_name, available_quantity, location, updated_at}
    """
    client = _get_client()
    response = (
        client.table("inventory")
        .select("id, item_type, item_name, available_quantity, location")
        .order("item_type")
        .order("item_name")
        .execute()
    )
    rows: list[dict] = response.data or []
    logger.debug("Fetched %d inventory rows from Supabase", len(rows))
    return rows


def deduct_inventory(item_name: str, quantity: int) -> bool:
    """
    Atomically deduct `quantity` from the row whose item_name matches.
    Returns True on success, False if item not found or insufficient stock.

    Uses a Postgres RPC function for atomicity — see migrations/003_rpc_deduct.sql.
    Falls back to a read-modify-write if the RPC is unavailable (dev mode).
    """
    client = _get_client()

    try:
        result = client.rpc(
            "deduct_inventory_quantity",
            {"p_item_name": item_name, "p_quantity": quantity},
        ).execute()

        # The RPC returns True/False via a boolean column named "success"
        if result.data and isinstance(result.data, list):
            return bool(result.data[0].get("success", False))
        return False

    except Exception as rpc_err:
        logger.warning(
            "RPC deduct_inventory_quantity failed (%s), falling back to "
            "read-modify-write.", rpc_err
        )
        return _deduct_fallback(client, item_name, quantity)


def _deduct_fallback(client: Client, item_name: str, quantity: int) -> bool:
    """
    Non-atomic fallback: read current quantity, verify sufficiency, update.
    Acceptable for single-writer dev/test environments.
    """
    rows = (
        client.table("inventory")
        .select("id, available_quantity")
        .eq("item_name", item_name)
        .execute()
        .data
    )

    if not rows:
        logger.error("Inventory item not found: '%s'", item_name)
        return False

    row = rows[0]
    current: int = row["available_quantity"]

    if current < quantity:
        logger.error(
            "Insufficient inventory for '%s': have %d, need %d",
            item_name, current, quantity,
        )
        return False

    try:
        client.table("inventory").update(
            {"available_quantity": current - quantity}
        ).eq("id", row["id"]).execute()
        logger.info("Deducted %d units of '%s'", quantity, item_name)
        return True
    except Exception as e:
        logger.error("Fallback deduction failed: %s", e)
        return False


def inventory_to_markdown(rows: list[dict[str, Any]]) -> str:
    """
    Format inventory as a markdown table for Gemini context.
    """
    if not rows:
        return "No inventory available."

    lines = [
        "| Item Type | Item Name | Available | Location |",
        "|-----------|-----------|-----------|----------|",
    ]

    for row in rows:
        item_type = row.get("item_type", "?")
        item_name = row.get("item_name", "?")
        available = row.get("available_quantity", 0)
        location = row.get("location", "?")
        lines.append(f"| {item_type} | {item_name} | {available} | {location} |")

    return "\n".join(lines)
