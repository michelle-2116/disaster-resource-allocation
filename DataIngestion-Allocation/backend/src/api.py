"""
api.py — Unified Disaster Relief Backend API
Integrates Layer 1 (Data Verification) + Layer 2 (Allocator) + Public Dashboard APIs
"""

import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpx").propagate = False

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# FastAPI
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Data/Allocator layers
from .agent import analyze_disaster, create_disaster_agent
from .allocator import run_allocator_agent
from .discord_adapter import analyze_discord_message

# Database stores
from .stores.incidents import create_incident, get_incident_by_id
from .stores.need_cards import (
    create_need_card,
    get_all_need_cards,
    approve_need_card,
    reject_need_card,
    take_up_need_card,
)

# Setup
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("API")


# ── Request/Response Models ──────────────────────────────────────────────────


class NeedCardResponse(BaseModel):
    id: str
    incident_id: str
    type: str
    item: str
    qty: float
    note: str | None
    explanation: str
    done_by: str | None
    fulfilled: bool
    pending_approval: bool
    show_pd: bool


class NeedCardDecisionRequest(BaseModel):
    need_card_id: str
    approved: bool


class NeedCardTakeUpRequest(BaseModel):
    id: str
    name: str
    ph_num: int
    email: str


class IncidentNewRequest(BaseModel):
    incident_name: str
    demo_mode: bool = False


class DiscordAttachmentRequest(BaseModel):
    url: str
    filename: str | None = None
    content_type: str | None = None
    size: int | None = None


class DiscordMessageRequest(BaseModel):
    content: str = ""
    username: str
    timestamp: str
    channel_id: str
    channel_name: str
    attachments: list[DiscordAttachmentRequest] = Field(default_factory=list)


# Global state
_current_demo_mode = False


def is_supabase_configured() -> bool:
    """Return whether the production Supabase store can be used."""
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))


def get_effective_demo_mode() -> bool:
    """Use demo storage when explicitly enabled or when Supabase is unavailable locally."""
    return get_demo_mode() or not is_supabase_configured()


def set_demo_mode(enabled: bool):
    """Set the global demo mode state."""
    global _current_demo_mode
    _current_demo_mode = enabled
    logger.info(f"Demo mode set to: {enabled}")


def get_demo_mode() -> bool:
    """Get the current demo mode state."""
    return _current_demo_mode


def verify_discord_secret(provided_secret: str | None):
    """Validate optional Discord listener shared secret."""
    expected_secret = os.getenv("DISCORD_INGEST_SECRET")
    if expected_secret and provided_secret != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid Discord ingest secret")


# ── Lifespan 
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup."""
    # Initialize demo database
    from .demo_db import init_demo_db
    init_demo_db()
    logger.info("Demo database initialized")
    logger.info("=" * 80)
    logger.info("DISASTER RELIEF UNIFIED BACKEND - STARTING")
    logger.info("=" * 80)
    logger.info("Layer 1 (Data Verification) + Layer 2 (Allocator) + Public Dashboard")
    yield
    logger.info("Backend shutdown complete")


# ── FastAPI App 

app = FastAPI(
    title="Disaster Relief Unified Backend",
    description="Integrates incident verification, resource allocation, and public dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper functions ─────────────────────────────────────────────────────────


def process_incident(incident_json: dict, demo_mode: bool = False) -> dict:
    """
    Process a single incident through Layer 1 + Layer 2.

    1. Create incident record
    2. Call Layer 2 allocator with the incident
    3. Create need-cards from allocations
    """
    incident_id = incident_json.get("incident_id", "UNKNOWN")
    incident_type = incident_json.get("incident", {}).get("type", "UNKNOWN")
    location = incident_json.get("incident", {}).get("location", "UNKNOWN")
    title = incident_json.get("incident", {}).get("title")
    severity = incident_json.get("incident", {}).get("severity", 5)
    summary = incident_json.get("incident", {}).get("summary")

    logger.info(f"Processing incident: {incident_id} (demo_mode={demo_mode})")

    # 1. Create incident record
    try:
        create_incident(
            incident_id=incident_id,
            incident_type=incident_type,
            location=location,
            title=title,
            severity=severity,
            summary=summary,
            demo_mode=demo_mode,
        )
        logger.info(f"Incident record created: {incident_id}")
    except Exception as e:
        logger.error(f"Failed to create incident record: {e}")
        raise

    # 2. Prepare context for Layer 2
    context_packet = {
        "incident_id": incident_id,
        "incident": incident_json.get("incident", {}),
        "needs_summary": f"Incident: {title}\n{summary}",
        "map_description": "Map data available",
    }

    # 3. Call Layer 2 allocator
    try:
        allocations_result = run_allocator_agent(context_packet)
        allocations = allocations_result.get("allocations", [])
        logger.info(f"Allocator returned {len(allocations)} allocations")
    except Exception as e:
        logger.error(f"Allocator failed: {e}")
        raise

    # 4. Create need-cards from allocations
    need_cards = []
    for allocation in allocations:
        tool_name = allocation.get("tool_name", "unknown")
        card_type = allocation.get("type", tool_name)
        item = allocation.get("item", "unknown")
        qty = allocation.get("quantity", 0)
        note = allocation.get("note")
        explanation = allocation.get("explanation", "")
        status = allocation.get("status", "pending")

        # Determine fulfilled status and done_by
        fulfilled = status == "executed"
        done_by = "us" if fulfilled else None
        pending_approval = status == "pending_approval"

        try:
            card = create_need_card(
                incident_id=incident_id,
                card_type=card_type,
                item=item,
                qty=qty,
                explanation=explanation,
                note=note,
                fulfilled=fulfilled,
                done_by=done_by,
                pending_approval=pending_approval,
                demo_mode=demo_mode,
            )
            need_cards.append(card)
            logger.info(f"Created need-card: {card_type} × {qty}")
        except Exception as e:
            logger.error(f"Failed to create need-card: {e}")
            # Continue with other cards

    return {
        "incident_id": incident_id,
        "need_cards_created": len(need_cards),
        "allocations_status": "completed",
    }


# ── Endpoints ──


@app.get("/need-cards", response_model=list[dict])
async def get_need_cards():
    """
    GET /need-cards
    Fetch all need-cards for the public dashboard.
    Uses the current demo_mode state set by /incident/new endpoint.
    """
    try:
        demo_mode = get_effective_demo_mode()
        cards = get_all_need_cards(demo_mode=demo_mode)
        logger.info(f"Fetched {len(cards)} need-cards (demo_mode={demo_mode})")
        return cards
    except Exception as e:
        logger.error(f"Failed to fetch need-cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/need-cards/decision")
async def decide_need_card(request: NeedCardDecisionRequest):
    """
    POST /need-cards/decision
    Admin approves or rejects a pending need-card.

    {
        "need_card_id": "...",
        "approved": true/false
    }
    """
    try:
        demo_mode = get_effective_demo_mode()
        if request.approved:
            card = approve_need_card(request.need_card_id, demo_mode=demo_mode)
            logger.info(f"Approved need-card: {request.need_card_id}")
            return {
                "status": "approved",
                "need_card_id": request.need_card_id,
                "card": card,
            }
        else:
            card = reject_need_card(request.need_card_id, demo_mode=demo_mode)
            logger.info(f"Rejected need-card: {request.need_card_id}")
            return {
                "status": "rejected",
                "need_card_id": request.need_card_id,
                "card": card,
            }
    except Exception as e:
        logger.error(f"Decision failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/need-cards/take-up")
async def handle_take_up_need_card(request: NeedCardTakeUpRequest):
    """
    POST /need-cards/take-up
    Volunteer takes up a need-card and commits to fulfill it.

    {
        "id": "need-card-id",
        "name": "Volunteer Name",
        "ph_num": 9876543210,
        "email": "volunteer@example.com"
    }
    """
    try:
        demo_mode = get_effective_demo_mode()
        card = take_up_need_card(request.id, request.name, demo_mode=demo_mode)
        logger.info(f"Volunteer {request.name} took up need-card {request.id}")
        return {
            "status": "taken_up",
            "need_card_id": request.id,
            "volunteer_name": request.name,
            "volunteer_email": request.email,
            "volunteer_ph_num": request.ph_num,
            "card": card,
        }
    except Exception as e:
        logger.error(f"Take-up failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/incident/new")
async def process_new_incident(request: IncidentNewRequest):
    """
    POST /incident/new
    Start processing a new disaster incident.

    Triggers Layer 1 (data verification) and Layer 2 (allocator).

    {
        "incident_name": "us iran war 2026",
        "demo_mode": false
    }
    """
    try:
        incident_name = request.incident_name
        requested_demo_mode = request.demo_mode
        
        # Set global demo mode
        set_demo_mode(requested_demo_mode)
        demo_mode = get_effective_demo_mode()
        
        logger.info(f"New incident request: {incident_name} (demo_mode={demo_mode})")

        # Trigger Layer 1 data verification
        logger.info(f"Triggering Layer 1 (Data Verification) for: {incident_name}")
        agent_client = create_disaster_agent()
        verified_incident = analyze_disaster(incident_name, agent_client, demo_mode=demo_mode, incident_name=incident_name)

        logger.info(f"Layer 1 returned: {verified_incident}")

        # Handle both single incident and multiple incidents
        incidents_to_process = []
        if isinstance(verified_incident, dict):
            if "incidents" in verified_incident:
                # Multiple incidents
                incidents_to_process = verified_incident.get("incidents", [])
            else:
                # Single incident
                incidents_to_process = [verified_incident]
        
        logger.info(f"Processing {len(incidents_to_process)} incident(s)")
        
        # Process all incidents through Layer 2
        all_results = []
        for incident in incidents_to_process:
            try:
                result = process_incident(incident, demo_mode=demo_mode)
                all_results.append(result)
            except Exception as e:
                logger.error(f"Failed to process incident {incident.get('incident_id')}: {e}")
                # Continue with other incidents
        
        # Return the first incident's ID for the response
        first_incident_id = incidents_to_process[0].get("incident_id") if incidents_to_process else "UNKNOWN"

        return {
            "status": "processing_complete",
            "incident_name": incident_name,
            "incident_id": first_incident_id,
            "incidents_processed": len(all_results),
            "allocation_summary": all_results,
            "verified_incidents": incidents_to_process,
            "demo_mode": demo_mode,
        }
    except Exception as e:
        logger.error(f"Incident processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/discord/messages")
async def ingest_discord_message(
    request: DiscordMessageRequest,
    x_discord_ingest_secret: str | None = Header(default=None, alias="X-Discord-Ingest-Secret"),
):
    """
    POST /discord/messages
    Ingest a Discord message captured by the standalone listener.

    The message is analyzed as a direct field report. Disaster-related messages
    are converted into verified incidents and passed through the existing
    allocator/need-card pipeline.
    """
    verify_discord_secret(x_discord_ingest_secret)

    payload = request.model_dump() if hasattr(request, "model_dump") else request.dict()
    demo_mode = get_effective_demo_mode()
    logger.info(
        "Discord message received from #%s by %s (attachments=%d, demo_mode=%s)",
        request.channel_name,
        request.username,
        len(request.attachments),
        demo_mode,
    )

    try:
        verified_incident = analyze_discord_message(payload)
        if not verified_incident:
            return {
                "status": "ignored",
                "reason": "message_not_classified_as_disaster",
                "demo_mode": demo_mode,
            }

        incidents_to_process = []
        if isinstance(verified_incident, dict):
            if "incidents" in verified_incident:
                incidents_to_process = verified_incident.get("incidents", [])
            else:
                incidents_to_process = [verified_incident]

        all_results = []
        for incident in incidents_to_process:
            try:
                all_results.append(process_incident(incident, demo_mode=demo_mode))
            except Exception as e:
                logger.error(
                    "Failed to process Discord incident %s: %s",
                    incident.get("incident_id"),
                    e,
                    exc_info=True,
                )

        return {
            "status": "processed" if all_results else "no_incidents_processed",
            "source": "discord",
            "incidents_processed": len(all_results),
            "allocation_summary": all_results,
            "verified_incidents": incidents_to_process,
            "demo_mode": demo_mode,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Discord message ingestion failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Disaster Relief Unified Backend",
        "version": "1.0.0",
        "demo_mode_enabled": get_effective_demo_mode(),
        "supabase_configured": is_supabase_configured(),
    }


@app.post("/demo/reset")
async def reset_demo(cascade: bool = True):
    """
    POST /demo/reset
    Reset the demo database to initial state (clears all data).
    """
    try:
        from .demo_db import reset_demo_db
        reset_demo_db()
        logger.info("Demo database reset via API")
        
        # Trigger Route-Optimizer system reset if cascade is True
        if cascade:
            import urllib.request
            try:
                req = urllib.request.Request(
                    "http://127.0.0.1:8001/system/reset?cascade=false",
                    method="POST",
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=3) as response:
                    pass
            except Exception as e:
                logger.warning(f"Could not ping Route-Optimizer reset: {e}")

        # Also clear Supabase if configured
        if is_supabase_configured():
            try:
                from .stores.need_cards import _get_client
                supabase = _get_client()
                # Delete dispatches first
                supabase.table("dispatches").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                # Delete blocked roads
                supabase.table("blocked_roads").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                # Delete need_cards
                supabase.table("need_cards").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                # Delete incidents
                supabase.table("incidents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                # Reset inventory in Supabase
                supabase.table("inventory").update({"quantity": 10000, "available_quantity": 10000}).neq("id", "00000000-0000-0000-0000-000000000000").execute()
                logger.info("Supabase database cleared and inventory reset via DataIngestion reset API")
            except Exception as e:
                logger.error(f"Failed to clear Supabase database from DataIngestion reset: {e}")

        return {
            "status": "reset_complete",
            "message": "Demo and database reset complete"
        }
    except Exception as e:
        logger.error(f"Failed to reset demo database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/status")
async def get_demo_status():
    """
    GET /demo/status
    Get the current demo mode status.
    """
    return {
        "demo_mode_enabled": get_effective_demo_mode(),
        "requested_demo_mode_enabled": get_demo_mode(),
        "supabase_configured": is_supabase_configured(),
    }


@app.get("/activity-feed")
async def get_activity_feed():
    """
    GET /activity-feed
    Get the activity feed (system logs).
    In demo mode, returns logs from demo database.
    In real mode, returns empty list (not implemented for Supabase).
    """
    try:
        demo_mode = get_effective_demo_mode()
        
        if demo_mode:
            from .demo_db import get_activity_feed_demo
            items = get_activity_feed_demo()
            logger.info(f"Fetched {len(items)} activity feed items from demo DB")
            return items
        
        # Real mode: activity feed not implemented yet
        logger.info("Activity feed requested in real mode (not implemented)")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch activity feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
