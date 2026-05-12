"""
incidents.py — Incidents audit log store
Database operations for incident records.
"""

import logging
from typing import Any
import os
from supabase import create_client, Client

logger = logging.getLogger("INCIDENTS_STORE")

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _client = create_client(url, key)
    return _client


def create_incident(
    incident_id: str,
    incident_type: str,
    location: str,
    title: str | None = None,
    severity: int = 5,
    summary: str | None = None,
    demo_mode: bool = False,
) -> dict[str, Any]:
    """Create a new incident record in the audit log."""
    
    if demo_mode:
        from ..demo_db import create_incident_demo
        return create_incident_demo({
            "incident_id": incident_id,
            "incident_name": incident_id,
            "incident_type": incident_type,
            "location": location,
            "title": title,
            "severity": severity,
            "summary": summary,
            "status": "active"
        })
    
    client = _get_client()

    data = {
        "incident_id": incident_id,
        "incident_type": incident_type,
        "location": location,
        "title": title,
        "severity": severity,
        "summary": summary,
        "status": "active",
    }

    try:
        result = client.table("incidents").insert(data).execute()
        logger.info(f"Created incident record: {incident_id}")
        return result.data[0] if result.data else None
    except Exception as e:
        # If incident already exists, just return it
        logger.warning(f"Incident creation failed (may already exist): {e}")
        existing = get_incident_by_id(incident_id, demo_mode=demo_mode)
        if existing:
            return existing
        raise


def get_incident_by_id(incident_id: str, demo_mode: bool = False) -> dict[str, Any] | None:
    """Fetch an incident by its incident_id string."""
    
    if demo_mode:
        from ..demo_db import get_demo_connection
        conn = get_demo_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "incident_id": row["incident_id"],
                    "incident_name": row["incident_name"],
                    "incident_type": row["incident_type"],
                    "location": row["location"],
                    "title": row["title"],
                    "severity": row["severity"],
                    "summary": row["summary"],
                    "status": row["status"],
                }
            return None
        finally:
            conn.close()
    
    client = _get_client()
    result = (
        client.table("incidents")
        .select("*")
        .eq("incident_id", incident_id)
        .single()
        .execute()
    )
    return result.data if result.data else None


def update_incident(incident_id: str, demo_mode: bool = False, **updates) -> dict[str, Any]:
    """Update an incident record."""
    
    if demo_mode:
        from ..demo_db import get_demo_connection
        conn = get_demo_connection()
        cursor = conn.cursor()
        try:
            # Build update query
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [incident_id]
            cursor.execute(f"UPDATE incidents SET {set_clause} WHERE incident_id = ?", values)
            conn.commit()
            logger.info(f"Updated incident: {incident_id}")
            return get_incident_by_id(incident_id, demo_mode=True)
        finally:
            conn.close()
    
    client = _get_client()
    result = (
        client.table("incidents")
        .update(updates)
        .eq("incident_id", incident_id)
        .execute()
    )
    logger.info(f"Updated incident: {incident_id}")
    return result.data[0] if result.data else None


def get_all_incidents(demo_mode: bool = False) -> list[dict[str, Any]]:
    """Fetch all incident records."""
    
    if demo_mode:
        from ..demo_db import get_demo_connection
        conn = get_demo_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM incidents ORDER BY created_at DESC")
            rows = cursor.fetchall()
            incidents = []
            for row in rows:
                incidents.append({
                    "incident_id": row["incident_id"],
                    "incident_name": row["incident_name"],
                    "incident_type": row["incident_type"],
                    "location": row["location"],
                    "title": row["title"],
                    "severity": row["severity"],
                    "summary": row["summary"],
                    "status": row["status"],
                })
            return incidents
        finally:
            conn.close()
    
    client = _get_client()
    result = (
        client.table("incidents")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []
