"""
inventory.py — Inventory store operations
All Supabase inventory reads and writes.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from postgrest.exceptions import APIError
from supabase import create_client, Client

logger = logging.getLogger("INVENTORY_STORE")

# ── Supabase client (lazy singleton) ────────────────────────────────────────

_client: Client | None = None

ITEM_TYPE_BY_NAME = {
    "dry ration packets": "food",
    "ready-to-eat meals": "food",
    "high-energy biscuits": "food",
    "baby food packs": "food",
    "water pouches (500ml)": "water",
    "water purification tabs": "water",
    "bottled water (1L)": "water",
    "ORS kits": "meds",
    "first aid kits": "meds",
    "trauma kits": "meds",
    "anti-cholera tablets": "meds",
    "NDRF team": "rescue_team",
    "State rescue team": "rescue_team",
    "Boat rescue unit": "rescue_team",
}


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _client = create_client(url, key)
    return _client


def _infer_item_type(item_name: str) -> str:
    """Best-effort type inference for legacy inventory schemas."""
    explicit_type = ITEM_TYPE_BY_NAME.get(item_name)
    if explicit_type:
        return explicit_type

    normalized = item_name.lower()
    if any(token in normalized for token in ("water", "purification")):
        return "water"
    if any(token in normalized for token in ("ors", "aid", "kit", "tablet", "med", "trauma")):
        return "meds"
    if any(token in normalized for token in ("team", "rescue", "ndrf", "boat")):
        return "rescue_team"
    return "food"


def _missing_item_type_column(error: APIError) -> bool:
    payload = getattr(error, "args", ())
    message = str(error)
    return ("42703" in message and "inventory.item_type" in message) or (
        bool(payload)
        and isinstance(payload[0], dict)
        and payload[0].get("code") == "42703"
        and "inventory.item_type" in str(payload[0].get("message", ""))
    )


def _normalize_inventory_row(row: dict[str, Any]) -> dict[str, Any]:
    item_name = str(row.get("item_name") or "")
    available_quantity = row.get("available_quantity")
    if available_quantity is None:
        available_quantity = row.get("quantity", 0)

    return {
        **row,
        "item_type": row.get("item_type") or _infer_item_type(item_name),
        "item_name": item_name,
        "available_quantity": int(available_quantity or 0),
        "location": row.get("location") or row.get("shelter_id") or "Unknown",
    }


# ── Public interface ────────────────────────────────────────────────────────

def fetch_inventory() -> list[dict[str, Any]]:
    """
    Return all rows from the inventory table, ordered by item_type then item_name.
    Each row: {id, item_type, item_name, available_quantity, location, updated_at}
    """
    client = _get_client()
    try:
        response = (
            client.table("inventory")
            .select("id, item_type, item_name, available_quantity, location")
            .order("item_type")
            .order("item_name")
            .execute()
        )
    except APIError as error:
        if not _missing_item_type_column(error):
            raise

        logger.warning(
            "inventory.item_type column is missing; using legacy inventory "
            "fallback. Apply migrations/005_fix_inventory_schema.sql."
        )
        response = client.table("inventory").select("*").execute()
        rows = [_normalize_inventory_row(row) for row in response.data or []]
        rows.sort(key=lambda row: (row.get("item_type", ""), row.get("item_name", "")))
        logger.debug("Fetched %d legacy inventory rows from Supabase", len(rows))
        return rows

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
        .select("*")
        .eq("item_name", item_name)
        .execute()
        .data
    )

    if not rows:
        logger.error("Inventory item not found: '%s'", item_name)
        return False

    row = rows[0]
    quantity_column = "available_quantity" if "available_quantity" in row else "quantity"
    if quantity_column not in row:
        logger.error("Inventory quantity column not found for '%s'", item_name)
        return False

    current: int = int(row[quantity_column] or 0)

    if current < quantity:
        logger.error(
            "Insufficient inventory for '%s': have %d, need %d",
            item_name, current, quantity,
        )
        return False

    try:
        client.table("inventory").update(
            {quantity_column: current - quantity}
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
