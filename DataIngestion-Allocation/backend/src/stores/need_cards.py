"""
need_cards.py — Need-cards store
Database operations for need-cards (resource allocation tracking).
"""

import logging
from typing import Any
import os
from supabase import create_client, Client

logger = logging.getLogger("NEED_CARDS_STORE")

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _client = create_client(url, key)
    return _client


def create_need_card(
    incident_id: str,
    card_type: str,
    item: str,
    qty: float,
    explanation: str,
    note: str | None = None,
    fulfilled: bool = False,
    done_by: str | None = None,
    pending_approval: bool = False,
    demo_mode: bool = False,
) -> dict[str, Any]:
    """Create a new need-card in the database."""
    
    if demo_mode:
        from ..demo_db import create_need_card_demo, create_incident_demo, add_activity_log_demo
        import uuid
        
        # First, ensure the incident exists in demo DB
        try:
            create_incident_demo({
                "incident_id": incident_id,
                "incident_name": incident_id,
                "incident_type": "disaster",
                "location": "Unknown",
                "title": f"Incident: {incident_id}",
                "severity": 5,
                "summary": "Auto-created incident for demo mode",
                "status": "active"
            })
        except Exception as e:
            # Incident might already exist, that's ok
            logger.debug(f"Incident creation skipped: {e}")
        
        card_data = {
            "id": str(uuid.uuid4()),
            "incident_id": incident_id,
            "type": card_type,
            "item": item,
            "qty": qty,
            "note": note,
            "explanation": explanation,
            "done_by": done_by,
            "fulfilled": fulfilled,
            "pending_approval": pending_approval,
            "show_pd": not pending_approval,
        }
        result = create_need_card_demo(card_data)
        
        # Log activity
        add_activity_log_demo("system", f"Created need card: {card_type} × {qty} ({item})")
        
        return result
    
    client = _get_client()

    # First get the incidents UUID from incident_id string
    incident = client.table("incidents").select("id").eq("incident_id", incident_id).execute()
    if not incident.data:
        logger.error(f"Incident not found: {incident_id}")
        raise ValueError(f"Incident not found: {incident_id}")

    incident_uuid = incident.data[0]["id"]

    data = {
        "incident_id": incident_uuid,
        "type": card_type,
        "item": item,
        "qty": qty,
        "note": note,
        "explanation": explanation,
        "done_by": done_by,
        "fulfilled": fulfilled,
        "pending_approval": pending_approval,
        "show_pd": not pending_approval,  # Only show on PD if not pending approval
    }

    result = client.table("need_cards").insert(data).execute()
    logger.info(f"Created need-card: {card_type} × {qty} for incident {incident_id}")
    return result.data[0] if result.data else None


def get_all_need_cards(demo_mode: bool = False) -> list[dict[str, Any]]:
    """Fetch all need-cards with incident details."""
    
    if demo_mode:
        from ..demo_db import get_all_need_cards_demo
        return get_all_need_cards_demo()
    
    client = _get_client()
    result = (
        client.table("need_cards")
        .select("*, incidents(incident_id, location)")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


def get_need_cards_by_incident(incident_id: str, demo_mode: bool = False) -> list[dict[str, Any]]:
    """Fetch need-cards for a specific incident."""
    
    if demo_mode:
        from ..demo_db import get_all_need_cards_demo
        all_cards = get_all_need_cards_demo()
        return [card for card in all_cards if card["incident_id"] == incident_id]
    
    client = _get_client()

    incident = client.table("incidents").select("id").eq("incident_id", incident_id).execute()
    if not incident.data:
        return []

    incident_uuid = incident.data[0]["id"]
    result = (
        client.table("need_cards")
        .select("*")
        .eq("incident_id", incident_uuid)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


def approve_need_card(card_id: str, demo_mode: bool = False) -> dict[str, Any]:
    """Admin approves a need-card (sets pending_approval=false, show_pd=true)."""
    
    if demo_mode:
        from ..demo_db import approve_need_card_demo, add_activity_log_demo
        result = approve_need_card_demo(card_id, approved=True)
        if result:
            add_activity_log_demo("admin", f"Approved need card: {result.get('item')}")
        return result
    
    client = _get_client()
    result = (
        client.table("need_cards")
        .update({"pending_approval": False, "show_pd": True})
        .eq("id", card_id)
        .execute()
    )
    logger.info(f"Approved need-card: {card_id}")
    return result.data[0] if result.data else None


def reject_need_card(card_id: str, demo_mode: bool = False) -> dict[str, Any]:
    """Admin rejects a need-card (sets show_pd=false)."""
    
    if demo_mode:
        from ..demo_db import approve_need_card_demo, add_activity_log_demo
        result = approve_need_card_demo(card_id, approved=False)
        if result:
            add_activity_log_demo("admin", f"Rejected need card: {result.get('item')}")
        return result
    
    client = _get_client()
    result = (
        client.table("need_cards")
        .update({"pending_approval": False, "show_pd": False})
        .eq("id", card_id)
        .execute()
    )
    logger.info(f"Rejected need-card: {card_id}")
    return result.data[0] if result.data else None


def take_up_need_card(card_id: str, volunteer_name: str, demo_mode: bool = False) -> dict[str, Any]:
    """Volunteer takes up a need-card (fulfills it)."""
    
    if demo_mode:
        from ..demo_db import take_up_need_card_demo, add_activity_log_demo
        result = take_up_need_card_demo(card_id, volunteer_name)
        if result:
            add_activity_log_demo("volunteer", f"{volunteer_name} took up: {result.get('item')}")
        return result
    
    client = _get_client()
    result = (
        client.table("need_cards")
        .update({"fulfilled": True, "done_by": volunteer_name})
        .eq("id", card_id)
        .execute()
    )
    logger.info(f"Need-card {card_id} taken up by {volunteer_name}")
    return result.data[0] if result.data else None
