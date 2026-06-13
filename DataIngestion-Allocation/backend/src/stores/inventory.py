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
            .select("id, item_type, item_name, available_quantity, location, shelter_id")
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


def deduct_inventory(item_name: str, quantity: int, item_type: str | None = None) -> bool:
    """
    Deduct `quantity` from the inventory rows whose item_type/item_name matches.
    Supports multi-row deduction if the quantity is distributed across duplicates.
    """
    client = _get_client()
    try:
        response = client.table("inventory").select("*").execute()
        rows = response.data or []
        
        canonical_target = item_type or _infer_item_type(item_name)
        matching_rows = []
        
        if canonical_target == "rescue_team":
            # For rescue teams, resolve target warehouse from destination location (item_name)
            dest_warehouse = _resolve_warehouse_name(None, item_name)
            for row in rows:
                row_item_name = row.get("item_name") or ""
                row_item_type = row.get("item_type") or _infer_item_type(row_item_name)
                if row_item_type == "rescue_team":
                    row_warehouse = _resolve_warehouse_name(row.get("shelter_id"), row.get("location"))
                    if row_warehouse == dest_warehouse:
                        matching_rows.append(row)
        else:
            for row in rows:
                row_item_name = row.get("item_name") or ""
                row_item_type = row.get("item_type") or _infer_item_type(row_item_name)
                if row_item_type.lower() == canonical_target.lower() or row_item_name.lower() == item_name.lower():
                    matching_rows.append(row)
                
        if not matching_rows:
            logger.error("No matching inventory rows found for item: %s", item_name)
            return False
            
        # Pre-check: Verify total available stock across all matching rows
        total_available = 0
        for row in matching_rows:
            qty_col = "available_quantity" if "available_quantity" in row else "quantity"
            total_available += int(row.get(qty_col, 0) or 0)
            
        if total_available < quantity:
            logger.error(
                "Insufficient inventory for '%s': total available %d, requested %d",
                item_name, total_available, quantity
            )
            return False
            
        # Deduct from the first matching row that has sufficient quantity
        for row in matching_rows:
            qty_col = "available_quantity" if "available_quantity" in row else "quantity"
            current = int(row.get(qty_col, 0) or 0)
            if current >= quantity:
                client.table("inventory").update({
                    qty_col: current - quantity,
                    "quantity": current - quantity
                }).eq("id", row["id"]).execute()
                logger.info("Deducted %d from single row ID %s", quantity, row["id"])
                return True
                
        # If no single row has enough, try to deduct partially from matching rows
        for row in matching_rows:
            qty_col = "available_quantity" if "available_quantity" in row else "quantity"
            current = int(row.get(qty_col, 0) or 0)
            if current > 0:
                deduct_qty = min(quantity, current)
                client.table("inventory").update({
                    qty_col: current - deduct_qty,
                    "quantity": current - deduct_qty
                }).eq("id", row["id"]).execute()
                quantity -= deduct_qty
                logger.info("Partially deducted %d from row ID %s", deduct_qty, row["id"])
                if quantity <= 0:
                    return True
                    
        return False
    except Exception as e:
        logger.error("Deduct inventory failed: %s", e, exc_info=True)
        return False


def _resolve_warehouse_name(shelter_id: str | None, location: str | None) -> str:
    loc = location or ""
    if not loc or loc.lower() == "unknown":
        loc = shelter_id or ""
        
    loc_lower = str(loc).lower()
    if "kalpetta" in loc_lower or "delhi" in loc_lower:
        return "Kalpetta District Warehouse"
    elif "bathery" in loc_lower or "lucknow" in loc_lower:
        return "Sulthan Bathery Relief Depot"
    elif "manathavady" in loc_lower or "patna" in loc_lower or "mananthavady" in loc_lower:
        return "Mananthavady Taluk Stock Point"
    else:
        # UUID mapping
        if loc == "00000000-0000-0000-0000-000000000000":
            return "Kalpetta District Warehouse"
        elif loc == "e50c8408-f7c0-42f6-9c9b-1ed6747494e6":
            return "Sulthan Bathery Relief Depot"
        elif loc == "eee9ab04-1e8d-4438-9174-faa2e724bb6a":
            return "Mananthavady Taluk Stock Point"
        elif loc == "3a618815-5a0d-476f-8904-0a51252d3e4b":
            return "Kalpetta District Warehouse"
        elif loc == "4f38aacd-98c0-456e-b314-cbc73d556876":
            return "Sulthan Bathery Relief Depot"
        else:
            return "Kalpetta District Warehouse"


def inventory_to_markdown(rows: list[dict[str, Any]]) -> str:
    """
    Format inventory as a markdown table for Gemini context.
    Group duplicates by their resolved warehouse name so Gemini sees aggregated stock.
    """
    if not rows:
        return "No inventory available."

    # Group inventory by (item_type, item_name, resolved_warehouse_name)
    grouped = {}
    for row in rows:
        item_type = row.get("item_type") or _infer_item_type(row.get("item_name") or "")
        item_name = row.get("item_name") or "unknown"
        available = int(row.get("available_quantity") or row.get("quantity") or 0)
        
        # Resolve the location to a friendly warehouse name
        shelter_id = row.get("shelter_id")
        loc_val = row.get("location")
        warehouse_name = _resolve_warehouse_name(shelter_id, loc_val)
        
        key = (item_type, item_name, warehouse_name)
        grouped[key] = grouped.get(key, 0) + available

    lines = [
        "| Item Type | Item Name | Available | Location |",
        "|-----------|-----------|-----------|----------|",
    ]

    # Sort grouped rows for a neat presentation
    for (item_type, item_name, warehouse_name), qty in sorted(grouped.items()):
        lines.append(f"| {item_type} | {item_name} | {qty} | {warehouse_name} |")

    return "\n".join(lines)
