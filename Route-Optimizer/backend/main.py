from __future__ import annotations

import math
import re
from copy import deepcopy
from uuid import uuid4
import logging

logger = logging.getLogger("api")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.routing import get_route
from database import supabase


app = FastAPI(title="Aegis Wayanad Route Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


WAYANAD_CENTER = {"lat": 11.6854, "lng": 76.1320}

WAREHOUSES = [
    {
        "id": "wh-kalpetta",
        "name": "Kalpetta District Warehouse",
        "type": "district_hub",
        "lat": 11.6100,
        "lng": 76.0825,
        "access": "NH766",
        "resources": [
            {"item_name": "Water", "quantity": 18000, "unit": "liters", "priority": "critical", "weight_kg": 0.001},
            {"item_name": "Food Rations", "quantity": 8400, "unit": "packs", "priority": "critical", "weight_kg": 0.8},
            {"item_name": "Medical Kits", "quantity": 620, "unit": "kits", "priority": "high", "weight_kg": 3.5},
            {"item_name": "Rescue Teams", "quantity": 14, "unit": "teams", "priority": "critical", "weight_kg": 95},
        ],
    },
    {
        "id": "wh-sulthan-bathery",
        "name": "Sulthan Bathery Relief Depot",
        "type": "forward_depot",
        "lat": 11.6621,
        "lng": 76.2576,
        "access": "NH766 east",
        "resources": [
            {"item_name": "Water", "quantity": 9000, "unit": "liters", "priority": "critical", "weight_kg": 0.001},
            {"item_name": "Food Rations", "quantity": 4700, "unit": "packs", "priority": "critical", "weight_kg": 0.8},
            {"item_name": "Medical Kits", "quantity": 280, "unit": "kits", "priority": "high", "weight_kg": 3.5},
            {"item_name": "Rescue Teams", "quantity": 8, "unit": "teams", "priority": "high", "weight_kg": 95},
        ],
    },
    {
        "id": "wh-manathavady",
        "name": "Mananthavady Taluk Stock Point",
        "type": "north_depot",
        "lat": 11.8014,
        "lng": 76.0041,
        "access": "SH54",
        "resources": [
            {"item_name": "Water", "quantity": 7600, "unit": "liters", "priority": "critical", "weight_kg": 0.001},
            {"item_name": "Food Rations", "quantity": 3600, "unit": "packs", "priority": "critical", "weight_kg": 0.8},
            {"item_name": "Medical Kits", "quantity": 190, "unit": "kits", "priority": "high", "weight_kg": 3.5},
            {"item_name": "Rescue Teams", "quantity": 6, "unit": "teams", "priority": "medium", "weight_kg": 95},
        ],
    },
]

DEFAULT_WAREHOUSES = deepcopy(WAREHOUSES)

SHELTERS = [
    {"id": "sh-meppadi", "name": "Meppadi GHSS Relief Camp", "capacity": 950, "current_occupancy": 720, "lat": 11.5577, "lng": 76.1411, "risk": "landslide and flood isolation"},
    {"id": "sh-vythiri", "name": "Vythiri Community Hall", "capacity": 520, "current_occupancy": 410, "lat": 11.5487, "lng": 76.0364, "risk": "hill road washout"},
    {"id": "sh-panamaram", "name": "Panamaram Panchayat Shelter", "capacity": 780, "current_occupancy": 590, "lat": 11.7407, "lng": 76.0732, "risk": "river overflow"},
    {"id": "sh-mananthavady", "name": "Mananthavady Municipal Camp", "capacity": 640, "current_occupancy": 455, "lat": 11.8010, "lng": 76.0080, "risk": "low-lying inundation"},
    {"id": "sh-sulthan-bathery", "name": "Sulthan Bathery Relief Camp", "capacity": 700, "current_occupancy": 530, "lat": 11.6640, "lng": 76.2608, "risk": "supply corridor congestion"},
]

INCIDENTS = [
    {"id": "inc-kabini", "title": "Kabini tributary overflow near Panamaram", "type": "flood", "severity": "critical", "summary": "Water level rising across low-lying riverbank homes.", "location_lat": 11.7318, "location_lng": 76.0768, "radius_meters": 4200, "status": "active"},
    {"id": "inc-meppadi", "title": "Flash flood and slope failure around Meppadi", "type": "flood", "severity": "high", "summary": "Access roads require high-clearance vehicles and medical support.", "location_lat": 11.5532, "location_lng": 76.1376, "radius_meters": 3600, "status": "active"},
    {"id": "inc-vythiri", "title": "Vythiri ghat section waterlogging", "type": "flood", "severity": "medium", "summary": "Traffic moving slowly with debris on several bends.", "location_lat": 11.5528, "location_lng": 76.0379, "radius_meters": 2300, "status": "monitoring"},
]

NEED_CARDS = [
    {"id": "need-panamaram-water", "incident_id": "inc-kabini", "shelter_id": "sh-panamaram", "item_type": "Water", "requested_qty": 3600, "status": "pending_approval"},
    {"id": "need-meppadi-medical", "incident_id": "inc-meppadi", "shelter_id": "sh-meppadi", "item_type": "Medical Kits", "requested_qty": 90, "status": "pending_approval"},
    {"id": "need-vythiri-food", "incident_id": "inc-vythiri", "shelter_id": "sh-vythiri", "item_type": "Food Rations", "requested_qty": 1800, "status": "pending_approval"},
]

INITIAL_BLOCKS = [
    {"id": "block-chundale", "lat": 11.5797, "lng": 76.0735, "radius_meters": 850, "reason": "Floodwater over Chundale bridge", "source": "district-control", "created_at": "2026-06-03T08:30:00+05:30"},
]

SYNONYMS = {
    "water": "Water",
    "drinking water": "Water",
    "food": "Food Rations",
    "ration": "Food Rations",
    "rations": "Food Rations",
    "medical": "Medical Kits",
    "medicine": "Medical Kits",
    "medicines": "Medical Kits",
    "team": "Rescue Teams",
    "teams": "Rescue Teams",
    "rescue": "Rescue Teams",
    "ndrf": "Rescue Teams",
    "boat": "Rescue Teams",
    "boats": "Rescue Teams",
}

ROAD_LOCATIONS = {
    "chundale": {"lat": 11.5797, "lng": 76.0735},
    "meppadi": {"lat": 11.5577, "lng": 76.1411},
    "vythiri": {"lat": 11.5487, "lng": 76.0364},
    "panamaram": {"lat": 11.7407, "lng": 76.0732},
    "kalpetta": {"lat": 11.6100, "lng": 76.0825},
    "mananthavady": {"lat": 11.8014, "lng": 76.0041},
    "sulthan bathery": {"lat": 11.6621, "lng": 76.2576},
    "bathery": {"lat": 11.6621, "lng": 76.2576},
    "padinjarathara": {"lat": 11.6862, "lng": 75.9944},
}


class RoadBlockInput(BaseModel):
    lat: float | None = None
    lng: float | None = None
    radius_meters: float = 800
    reason: str
    source: str = "admin"


class DiscordInput(BaseModel):
    message: str
    author: str = "discord"


state = {
    "blocked_roads": deepcopy(INITIAL_BLOCKS),
    "need_cards": deepcopy(NEED_CARDS),
    "dispatches": [],
}


def parse_reason_metadata(reason_text: str) -> tuple[str, float, str]:
    """Extract radius_meters and source encoded in the Supabase reason text."""
    radius = 800.0
    source = "admin"
    clean_reason = reason_text
    
    r_match = re.search(r"\[Radius:\s*([\d\.]+)m\]", reason_text)
    if r_match:
        try:
            radius = float(r_match.group(1))
        except ValueError:
            pass
        clean_reason = re.sub(r"\s*\[Radius:\s*[\d\.]+m\]", "", clean_reason)
        
    s_match = re.search(r"\[Source:\s*([^\]]+)\]", reason_text)
    if s_match:
        source = s_match.group(1)
        clean_reason = re.sub(r"\s*\[Source:\s*[^\]]+\]", "", clean_reason)
        
    return clean_reason.strip(), radius, source


def resolve_shelter_id(location_text: str) -> str:
    if not location_text:
        return "sh-meppadi"
    text = location_text.lower()
    if "meppadi" in text:
        return "sh-meppadi"
    if "vythiri" in text:
        return "sh-vythiri"
    if "panamaram" in text:
        return "sh-panamaram"
    if "mananthavady" in text or "mananthavadi" in text:
        return "sh-mananthavady"
    if "bathery" in text or "sulthan" in text:
        return "sh-sulthan-bathery"
    return "sh-meppadi"


def resolve_item_type(item: str) -> str:
    normalized = item.lower()
    for keyword, canonical in SYNONYMS.items():
        if keyword in normalized:
            return canonical
    if "water" in normalized:
        return "Water"
    if "food" in normalized or "meal" in normalized or "ration" in normalized or "biscuit" in normalized:
        return "Food Rations"
    if "kit" in normalized or "med" in normalized or "tablet" in normalized or "ors" in normalized:
        return "Medical Kits"
    if "team" in normalized or "rescue" in normalized or "ndrf" in normalized or "boat" in normalized:
        return "Rescue Teams"
    return "Water"


def resolve_incident_coords(location_text: str) -> tuple[float, float]:
    if not location_text:
        return WAYANAD_CENTER["lat"], WAYANAD_CENTER["lng"]
    text = location_text.lower()
    for name, coords in ROAD_LOCATIONS.items():
        if name in text:
            return coords["lat"], coords["lng"]
    return WAYANAD_CENTER["lat"], WAYANAD_CENTER["lng"]


def map_severity(severity_val: int | None) -> str:
    if not severity_val:
        return "medium"
    if severity_val >= 8:
        return "critical"
    elif severity_val >= 6:
        return "high"
    elif severity_val >= 4:
        return "medium"
    else:
        return "low"


def resolve_warehouse_id(row: dict) -> str:
    loc = row.get("location") or ""
    if not loc or loc.lower() == "unknown":
        loc = row.get("shelter_id") or ""
        
    loc_lower = str(loc).lower()
    if "kalpetta" in loc_lower or "delhi" in loc_lower:
        return "wh-kalpetta"
    elif "bathery" in loc_lower or "lucknow" in loc_lower:
        return "wh-sulthan-bathery"
    elif "manathavady" in loc_lower or "patna" in loc_lower or "mananthavady" in loc_lower:
        return "wh-manathavady"
    else:
        # UUID mapping from shelters
        if loc == "00000000-0000-0000-0000-000000000000":
            return "wh-kalpetta"
        elif loc == "e50c8408-f7c0-42f6-9c9b-1ed6747494e6":
            return "wh-sulthan-bathery"
        elif loc == "eee9ab04-1e8d-4438-9174-faa2e724bb6a":
            return "wh-manathavady"
        elif loc == "3a618815-5a0d-476f-8904-0a51252d3e4b":
            return "wh-kalpetta"
        elif loc == "4f38aacd-98c0-456e-b314-cbc73d556876":
            return "wh-sulthan-bathery"
        else:
            return "wh-kalpetta"


def get_live_warehouses(supabase_client) -> list:
    warehouses = deepcopy(WAREHOUSES)
    if not supabase_client:
        return warehouses
    try:
        res = supabase_client.table("inventory").select("*").execute()
        rows = res.data or []
        stock_by_loc_item = {}
        for row in rows:
            qty_val = row.get("available_quantity")
            if qty_val is None:
                qty_val = row.get("quantity", 0)
            qty = int(qty_val or 0)
            canonical_item = resolve_item_type(row.get("item_name") or "")
            
            wh_id = resolve_warehouse_id(row)
            key = (wh_id, canonical_item)
            stock_by_loc_item[key] = stock_by_loc_item.get(key, 0) + qty
            
        for w in warehouses:
            for res_item in w["resources"]:
                canonical = resolve_item_type(res_item["item_name"])
                key = (w["id"], canonical)
                if key in stock_by_loc_item:
                    res_item["quantity"] = stock_by_loc_item[key]
    except Exception as e:
        logger.error(f"Error in get_live_warehouses: {e}", exc_info=True)
    return warehouses


def choose_warehouse_live(shelter: dict, item_name: str, qty: float, warehouses_list: list) -> dict | None:
    candidates = [w for w in warehouses_list if warehouse_stock(w, item_name) >= qty]
    if not candidates:
        candidates = [w for w in warehouses_list if warehouse_stock(w, item_name) > 0]
    if not candidates:
        return None
    return sorted(candidates, key=lambda w: distance_km(w, shelter))[0]


def deduct_inventory_supabase(item_name: str, quantity: int, warehouse_id: str = None) -> bool:
    if not supabase:
        return False
    try:
        res = supabase.table("inventory").select("*").execute()
        rows = res.data or []
        
        canonical_target = resolve_item_type(item_name)
        matching_rows = []
        for row in rows:
            row_item_name = row.get("item_name") or ""
            if resolve_item_type(row_item_name) == canonical_target or row_item_name == item_name:
                wh_id = resolve_warehouse_id(row)
                if wh_id == warehouse_id or not warehouse_id:
                    matching_rows.append(row)
                    
        if not matching_rows:
            return False
            
        # Pre-check: Verify total available stock across all matching rows
        total_available = 0
        for row in matching_rows:
            quantity_column = "available_quantity" if "available_quantity" in row else "quantity"
            total_available += int(row.get(quantity_column, 0) or 0)
        if total_available < quantity:
            return False
            
        # Deduct from the first matching row that has sufficient quantity
        for row in matching_rows:
            quantity_column = "available_quantity" if "available_quantity" in row else "quantity"
            current = int(row.get(quantity_column, 0) or 0)
            if current >= quantity:
                supabase.table("inventory").update({quantity_column: current - quantity}).eq("id", row["id"]).execute()
                return True
                
        # If no single row has enough, try to deduct partially from matching rows
        for row in matching_rows:
            quantity_column = "available_quantity" if "available_quantity" in row else "quantity"
            current = int(row.get(quantity_column, 0) or 0)
            if current > 0:
                deduct_qty = min(quantity, current)
                supabase.table("inventory").update({quantity_column: current - deduct_qty}).eq("id", row["id"]).execute()
                quantity -= deduct_qty
                if quantity <= 0:
                    return True
                    
        return False
    except Exception as e:
        logger.error(f"Error in deduct_inventory_supabase: {e}", exc_info=True)
        return False


async def rebuild_live_dispatches() -> None:
    if not supabase:
        return
    try:
        b_res = supabase.table("blocked_roads").select("*").execute()
        blocked_roads_list = []
        for r in (b_res.data or []):
            reason, radius, source = parse_reason_metadata(r["reason"])
            blocked_roads_list.append({
                "id": r["id"],
                "lat": float(r["lat"]),
                "lng": float(r["lng"]),
                "radius_meters": radius,
                "reason": reason,
                "source": source,
            })
            
        res = supabase.table("dispatches").select("*, need_cards(*)").execute()
        for r in (res.data or []):
            need_card = r.get("need_cards") or {}
            inc_res = supabase.table("incidents").select("*").eq("id", need_card.get("incident_id")).execute()
            location_text = ""
            if inc_res.data:
                location_text = inc_res.data[0].get("location") or ""
                
            shelter_id = resolve_shelter_id(location_text)
            shelter = next((s for s in SHELTERS if s["id"] == shelter_id), None)
            item_type = resolve_item_type(need_card.get("item") or need_card.get("item_type") or "")
            
            live_warehouses = get_live_warehouses(supabase)
            warehouse = None
            if shelter:
                warehouse = choose_warehouse_live(shelter, item_type, 1, live_warehouses)
                
            if warehouse and shelter:
                route = get_route(
                    warehouse["lat"],
                    warehouse["lng"],
                    shelter["lat"],
                    shelter["lng"],
                    avoid_points=blocked_roads_list,
                )
                if route:
                    supabase.table("dispatches").update({
                        "route_geometry": route["geometry"],
                        "distance": float(route["distance"]),
                        "estimated_time": float(route["duration"]),
                        "status": "rerouted" if route["rerouted"] else "en_route",
                    }).eq("id", r["id"]).execute()
    except Exception:
        pass


def distance_km(a: dict, b: dict) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, [a["lat"], a["lng"], b["lat"], b["lng"]])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    hav = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(hav))


def warehouse_stock(warehouse: dict, item_name: str) -> int:
    target_canonical = resolve_item_type(item_name)
    for resource in warehouse["resources"]:
        if resolve_item_type(resource["item_name"]) == target_canonical:
            return resource["quantity"]
    return 0


def choose_warehouse(shelter: dict, item_name: str, qty: int) -> dict | None:
    candidates = [w for w in WAREHOUSES if warehouse_stock(w, item_name) >= qty]
    if not candidates:
        candidates = [w for w in WAREHOUSES if warehouse_stock(w, item_name) > 0]
    if not candidates:
        return None
    return sorted(candidates, key=lambda w: distance_km(w, shelter))[0]


def mutate_inventory(warehouse_id: str, item_name: str, qty: int) -> None:
    for warehouse in WAREHOUSES:
        if warehouse["id"] != warehouse_id:
            continue
        for resource in warehouse["resources"]:
            if resource["item_name"] == item_name:
                resource["quantity"] = max(0, resource["quantity"] - qty)


def dispatch_for_need(need: dict) -> dict:
    shelter = next((s for s in SHELTERS if s["id"] == need["shelter_id"]), None)
    if not shelter:
        raise HTTPException(status_code=404, detail="Shelter not found")

    warehouse = choose_warehouse(shelter, need["item_type"], need["requested_qty"])
    if not warehouse:
        raise HTTPException(status_code=400, detail=f"No warehouse has {need['item_type']} available")

    route = get_route(
        warehouse["lat"],
        warehouse["lng"],
        shelter["lat"],
        shelter["lng"],
        avoid_points=state["blocked_roads"],
    )
    if not route:
        raise HTTPException(status_code=502, detail="Unable to calculate route")

    mutate_inventory(warehouse["id"], need["item_type"], need["requested_qty"])
    need["status"] = "approved"

    explanation = route_explanation(route, warehouse, shelter)

    return {
        "id": f"dispatch-{uuid4()}",
        "need_card_id": need["id"],
        "warehouse_id": warehouse["id"],
        "warehouse_name": warehouse["name"],
        "shelter_id": shelter["id"],
        "shelter_name": shelter["name"],
        "item_type": need["item_type"],
        "quantity": need["requested_qty"],
        "route_geometry": route["geometry"],
        "distance": route["distance"],
        "estimated_time": route["duration"],
        "rerouted": route["rerouted"],
        "blocked_by": route["blocked_by"],
        "blocked_by_reason": route.get("blocked_by_reason"),
        "detour_waypoint": route.get("detour_waypoint"),
        "route_explanation": explanation,
        "status": "en_route",
    }


def route_preview_for_need(need: dict, blocked_roads: list = None, warehouses_list: list = None) -> dict | None:
    if blocked_roads is None:
        blocked_roads = state["blocked_roads"]
    if warehouses_list is None:
        warehouses_list = get_live_warehouses(supabase) if supabase else WAREHOUSES

    shelter = next((s for s in SHELTERS if s["id"] == need["shelter_id"]), None)
    if not shelter:
        return None
    warehouse = choose_warehouse_live(shelter, need["item_type"], need["requested_qty"], warehouses_list)
    if not warehouse:
        return None
    route = get_route(
        warehouse["lat"],
        warehouse["lng"],
        shelter["lat"],
        shelter["lng"],
        avoid_points=blocked_roads,
    )
    if not route:
        return None
    explanation = route_explanation(route, warehouse, shelter)
    return {
        "id": f"preview-{need['id']}",
        "need_card_id": need["id"],
        "warehouse_id": warehouse["id"],
        "warehouse_name": warehouse["name"],
        "shelter_id": shelter["id"],
        "shelter_name": shelter["name"],
        "item_type": need["item_type"],
        "quantity": need["requested_qty"],
        "route_geometry": route["geometry"],
        "distance": route["distance"],
        "estimated_time": route["duration"],
        "rerouted": route["rerouted"],
        "blocked_by": route["blocked_by"],
        "blocked_by_reason": route.get("blocked_by_reason"),
        "detour_waypoint": route.get("detour_waypoint"),
        "route_explanation": explanation,
        "status": "suggested",
    }


def rebuild_dispatches() -> None:
    approved = [n for n in state["need_cards"] if n["status"] == "approved"]
    rebuilt = []
    for need in approved:
        shelter = next(s for s in SHELTERS if s["id"] == need["shelter_id"])
        warehouse = next(
            (w for w in WAREHOUSES if any(d["need_card_id"] == need["id"] and d["warehouse_id"] == w["id"] for d in state["dispatches"])),
            choose_warehouse(shelter, need["item_type"], 1),
        )
        route = get_route(warehouse["lat"], warehouse["lng"], shelter["lat"], shelter["lng"], avoid_points=state["blocked_roads"])
        explanation = route_explanation(route, warehouse, shelter)
        rebuilt.append({
            "id": next((d["id"] for d in state["dispatches"] if d["need_card_id"] == need["id"]), f"dispatch-{uuid4()}"),
            "need_card_id": need["id"],
            "warehouse_id": warehouse["id"],
            "warehouse_name": warehouse["name"],
            "shelter_id": shelter["id"],
            "shelter_name": shelter["name"],
            "item_type": need["item_type"],
            "quantity": need["requested_qty"],
            "route_geometry": route["geometry"],
            "distance": route["distance"],
            "estimated_time": route["duration"],
            "rerouted": route["rerouted"],
            "blocked_by": route["blocked_by"],
            "blocked_by_reason": route.get("blocked_by_reason"),
            "detour_waypoint": route.get("detour_waypoint"),
            "route_explanation": explanation,
            "status": "rerouted" if route["rerouted"] else "en_route",
        })
    state["dispatches"] = rebuilt


def route_explanation(route: dict, warehouse: dict, shelter: dict) -> str:
    distance_km = route["distance"] / 1000
    eta_min = round(route["duration"] / 60)
    if route.get("rerouted"):
        reason = route.get("blocked_by_reason") or "a reported road block"
        return (
            f"Optimized route from {warehouse['name']} to {shelter['name']} avoids {reason}. "
            f"The path uses a detour waypoint around the blocked radius, then rejoins the fastest available road corridor. "
            f"Estimated travel is {distance_km:.1f} km and {eta_min} min."
        )
    return (
        f"Optimized route from {warehouse['name']} to {shelter['name']} uses the fastest available road corridor. "
        f"No active road block intersects this route. Estimated travel is {distance_km:.1f} km and {eta_min} min."
    )


def parse_discord_message(message: str) -> dict:
    text = message.lower()
    location = None
    for name, coords in ROAD_LOCATIONS.items():
        if name in text:
            location = {"name": name.title(), **coords}
            break

    coordinate_match = re.search(r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", message)
    if coordinate_match:
        location = {
            "name": "Shared coordinates",
            "lat": float(coordinate_match.group(1)),
            "lng": float(coordinate_match.group(2)),
        }

    if not location:
        raise HTTPException(status_code=400, detail="Could not identify a Wayanad road or lat,lng in the Discord message")

    reason = "Discord road report"
    if "landslide" in text:
        reason = "Landslide reported by Discord volunteer"
    elif "bridge" in text:
        reason = "Bridge access blocked by Discord report"
    elif "flood" in text or "water" in text:
        reason = "Floodwater reported by Discord volunteer"
    elif "tree" in text:
        reason = "Fallen tree reported by Discord volunteer"

    return {
        "lat": location["lat"],
        "lng": location["lng"],
        "radius_meters": 900,
        "reason": f"{reason} near {location['name']}",
        "source": "discord",
    }


@app.get("/")
async def root():
    return {"message": "Aegis Wayanad route optimizer is online", "center": WAYANAD_CENTER}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "route-optimizer",
        "supabase_configured": supabase is not None,
        "blocked_roads": len(state["blocked_roads"]),
        "need_cards": len(state["need_cards"]),
        "dispatches": len(state["dispatches"]),
    }


@app.get("/map-data")
async def get_map_data():
    live_warehouses = get_live_warehouses(supabase) if supabase else WAREHOUSES

    live_incidents = []
    if supabase:
        try:
            res = supabase.table("incidents").select("*").execute()
            for r in (res.data or []):
                location_text = r.get("location") or r.get("incident_name") or ""
                lat, lng = resolve_incident_coords(location_text)
                severity_val = r.get("severity")
                severity_str = map_severity(severity_val)
                
                radius = 2000
                if severity_str == "critical":
                    radius = 4200
                elif severity_str == "high":
                    radius = 3600
                elif severity_str == "medium":
                    radius = 2300
                else:
                    radius = 1000
                    
                live_incidents.append({
                    "id": r.get("incident_id") or r.get("id"),
                    "title": r.get("title") or f"Incident near {location_text}",
                    "type": r.get("incident_type") or r.get("type") or "flood",
                    "severity": severity_str,
                    "summary": r.get("summary") or "",
                    "location_lat": lat,
                    "location_lng": lng,
                    "radius_meters": radius,
                    "status": r.get("status") or "active",
                })
        except Exception:
            live_incidents = INCIDENTS
    else:
        live_incidents = INCIDENTS

    blocked_roads_list = []
    if supabase:
        try:
            res = supabase.table("blocked_roads").select("*").execute()
            for r in (res.data or []):
                reason, radius, source = parse_reason_metadata(r["reason"])
                blocked_roads_list.append({
                    "id": r["id"],
                    "lat": float(r["lat"]),
                    "lng": float(r["lng"]),
                    "radius_meters": radius,
                    "reason": reason,
                    "source": source,
                    "created_at": "live",
                })
        except Exception:
            blocked_roads_list = state["blocked_roads"]
    else:
        blocked_roads_list = state["blocked_roads"]

    live_need_cards = []
    if supabase:
        try:
            res = supabase.table("need_cards").select("*, incidents(*)").eq("pending_approval", False).eq("fulfilled", False).execute()
            for row in (res.data or []):
                incident = row.get("incidents") or {}
                location_text = incident.get("location") or ""
                shelter_id = resolve_shelter_id(location_text)
                item_type = resolve_item_type(row.get("item") or row.get("item_type") or "")
                
                live_need_cards.append({
                    "id": row["id"],
                    "incident_id": incident.get("incident_id") or row.get("incident_id") or "unknown",
                    "shelter_id": shelter_id,
                    "item_type": item_type,
                    "requested_qty": float(row.get("qty") or row.get("requested_qty") or 0),
                    "status": "pending_approval",
                })
        except Exception as e:
            logger.error(f"Error fetching need_cards from Supabase: {e}", exc_info=True)
            live_need_cards = [n for n in state["need_cards"] if n["status"] == "pending_approval"]
    else:
        live_need_cards = [n for n in state["need_cards"] if n["status"] == "pending_approval"]

    live_dispatches = []
    if supabase:
        try:
            res = supabase.table("dispatches").select("*, need_cards(*, incidents(*))").execute()
            for r in (res.data or []):
                need_card = r.get("need_cards") or {}
                incident = need_card.get("incidents") or {}
                location_text = incident.get("location") or ""
                
                shelter_id = resolve_shelter_id(location_text)
                shelter_name = next((s["name"] for s in SHELTERS if s["id"] == shelter_id), "Unknown Shelter")
                item_type = resolve_item_type(need_card.get("item") or need_card.get("item_type") or "")
                qty = float(need_card.get("qty") or need_card.get("requested_qty") or 0)
                
                shelter = next((s for s in SHELTERS if s["id"] == shelter_id), None)
                warehouse = choose_warehouse_live(shelter, item_type, 1, live_warehouses) if shelter else None
                
                wh_id = warehouse["id"] if warehouse else "wh-kalpetta"
                wh_name = warehouse["name"] if warehouse else "Kalpetta District Warehouse"
                
                geom = r.get("route_geometry") or {}
                route_dict = {
                    "distance": float(r.get("distance") or 0),
                    "duration": float(r.get("estimated_time") or 0),
                    "geometry": geom,
                    "rerouted": r.get("status") == "rerouted",
                    "blocked_by": "road block",
                    "blocked_by_reason": None,
                }
                
                explanation = ""
                if warehouse and shelter:
                    explanation = route_explanation(route_dict, warehouse, shelter)
                
                live_dispatches.append({
                    "id": r["id"],
                    "need_card_id": r["need_card_id"],
                    "warehouse_id": wh_id,
                    "warehouse_name": wh_name,
                    "shelter_id": shelter_id,
                    "shelter_name": shelter_name,
                    "item_type": item_type,
                    "quantity": qty,
                    "route_geometry": geom,
                    "distance": float(r.get("distance") or 0),
                    "estimated_time": float(r.get("estimated_time") or 0),
                    "rerouted": route_dict["rerouted"],
                    "blocked_by": route_dict["blocked_by"],
                    "blocked_by_reason": route_dict["blocked_by_reason"],
                    "route_explanation": explanation,
                    "status": r.get("status") or "en_route",
                })
        except Exception as e:
            logger.error(f"Error fetching dispatches from Supabase: {e}", exc_info=True)
            live_dispatches = state["dispatches"]
    else:
        live_dispatches = state["dispatches"]

    suggested_routes = []
    for need in live_need_cards:
        route = route_preview_for_need(need, blocked_roads_list, live_warehouses)
        if route:
            suggested_routes.append(route)

    inventory_items = [
        {**resource, "id": f"{warehouse['id']}-{resource['item_name']}", "warehouse_id": warehouse["id"], "warehouse_name": warehouse["name"]}
        for warehouse in live_warehouses
        for resource in warehouse["resources"]
    ]

    return {
        "center": WAYANAD_CENTER,
        "warehouses": live_warehouses,
        "shelters": SHELTERS,
        "incidents": live_incidents,
        "need_cards": live_need_cards,
        "dispatches": live_dispatches,
        "suggested_routes": suggested_routes,
        "blocked_roads": blocked_roads_list,
        "inventory": inventory_items,
    }


@app.post("/allocate/approve/{need_id}")
async def approve_allocation(need_id: str):
    if supabase:
        try:
            res = supabase.table("need_cards").select("*, incidents(*)").eq("id", need_id).execute()
            if not res.data:
                raise HTTPException(status_code=404, detail="Need not found")
            row = res.data[0]
            if row.get("fulfilled"):
                return {"status": "already_approved"}
                
            incident = row.get("incidents") or {}
            location_text = incident.get("location") or ""
            shelter_id = resolve_shelter_id(location_text)
            item_type = resolve_item_type(row.get("item") or row.get("item_type") or "")
            qty = float(row.get("qty") or row.get("requested_qty") or 0)
            
            b_res = supabase.table("blocked_roads").select("*").execute()
            blocked_roads_list = []
            for r in (b_res.data or []):
                reason, radius, source = parse_reason_metadata(r["reason"])
                blocked_roads_list.append({
                    "id": r["id"],
                    "lat": float(r["lat"]),
                    "lng": float(r["lng"]),
                    "radius_meters": radius,
                    "reason": reason,
                    "source": source,
                })
                
            shelter = next((s for s in SHELTERS if s["id"] == shelter_id), None)
            if not shelter:
                raise HTTPException(status_code=404, detail="Shelter not found")
                
            live_warehouses = get_live_warehouses(supabase)
            warehouse = choose_warehouse_live(shelter, item_type, qty, live_warehouses)
            if not warehouse:
                raise HTTPException(status_code=400, detail=f"No warehouse has {item_type} available")
                
            route = get_route(
                warehouse["lat"],
                warehouse["lng"],
                shelter["lat"],
                shelter["lng"],
                avoid_points=blocked_roads_list,
            )
            if not route:
                raise HTTPException(status_code=502, detail="Unable to calculate route")
                
            explanation = route_explanation(route, warehouse, shelter)
            
            db_item_name = row.get("item") or item_type
            deducted = deduct_inventory_supabase(db_item_name, int(qty), warehouse_id=warehouse["id"])
                            
            supabase.table("need_cards").update({"fulfilled": True, "done_by": "Route Optimizer"}).eq("id", need_id).execute()
            
            dispatch_id = str(uuid4())
            dispatch_row = {
                "id": dispatch_id,
                "need_card_id": need_id,
                "route_geometry": route["geometry"],
                "distance": float(route["distance"]),
                "estimated_time": float(route["duration"]),
                "status": "rerouted" if route["rerouted"] else "en_route",
            }
            supabase.table("dispatches").insert(dispatch_row).execute()
            
            return {
                "status": "approved",
                "dispatch": {
                    "id": dispatch_id,
                    "need_card_id": need_id,
                    "warehouse_id": warehouse["id"],
                    "warehouse_name": warehouse["name"],
                    "shelter_id": shelter["id"],
                    "shelter_name": shelter["name"],
                    "item_type": item_type,
                    "quantity": qty,
                    "route_geometry": route["geometry"],
                    "distance": route["distance"],
                    "estimated_time": route["duration"],
                    "rerouted": route["rerouted"],
                    "blocked_by": route["blocked_by"],
                    "blocked_by_reason": route.get("blocked_by_reason"),
                    "detour_waypoint": route.get("detour_waypoint"),
                    "route_explanation": explanation,
                    "status": dispatch_row["status"],
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database approved dispatch failed: {e}")
            
    need = next((n for n in state["need_cards"] if n["id"] == need_id), None)
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")
    if need["status"] == "approved":
        return {"status": "already_approved"}
        
    dispatch = dispatch_for_need(need)
    state["dispatches"].append(dispatch)
    return {"status": "approved", "dispatch": dispatch}


@app.post("/blocked-roads")
async def add_blocked_road(payload: RoadBlockInput):
    if payload.lat is None or payload.lng is None:
        raise HTTPException(status_code=400, detail="lat and lng are required")
        
    block_id = str(uuid4())
    db_reason = f"{payload.reason} [Radius: {payload.radius_meters}m] [Source: {payload.source}]"
    
    if supabase:
        try:
            db_row = {
                "id": block_id,
                "lat": payload.lat,
                "lng": payload.lng,
                "reason": db_reason,
            }
            supabase.table("blocked_roads").insert(db_row).execute()
            await rebuild_live_dispatches()
        except Exception:
            pass
            
    block = {
        "id": f"block-{block_id}",
        "lat": payload.lat,
        "lng": payload.lng,
        "radius_meters": payload.radius_meters,
        "reason": payload.reason,
        "source": payload.source,
        "created_at": "live",
    }
    state["blocked_roads"].append(block)
    rebuild_dispatches()
    
    map_data = await get_map_data()
    return {"status": "blocked_road_added", "block": block, "dispatches": map_data["dispatches"]}


@app.post("/discord/road-report")
async def ingest_discord_report(payload: DiscordInput):
    parsed = parse_discord_message(payload.message)
    block = RoadBlockInput(**parsed)
    return await add_blocked_road(block)


class InventoryUpdateInput(BaseModel):
    quantity: int


@app.patch("/inventory/{warehouse_id}/{item_name}")
async def update_inventory(warehouse_id: str, item_name: str, payload: InventoryUpdateInput):
    """Admin endpoint: set the quantity for a specific item in a specific warehouse."""
    if payload.quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")

    # 1. Update in-memory WAREHOUSES state
    wh = next((w for w in WAREHOUSES if w["id"] == warehouse_id), None)
    if not wh:
        raise HTTPException(status_code=404, detail=f"Warehouse '{warehouse_id}' not found")

    resource = next((r for r in wh["resources"] if r["item_name"] == item_name), None)
    if not resource:
        raise HTTPException(status_code=404, detail=f"Item '{item_name}' not found in warehouse '{warehouse_id}'")

    old_qty = resource["quantity"]
    resource["quantity"] = payload.quantity

    # 2. Persist to Supabase if connected
    if supabase:
        try:
            canonical = resolve_item_type(item_name)
            res = supabase.table("inventory").select("*").execute()
            matching_rows = []
            for row in (res.data or []):
                row_canonical = resolve_item_type(row.get("item_name") or "")
                row_wh = resolve_warehouse_id(row)
                if row_canonical == canonical and row_wh == warehouse_id:
                    matching_rows.append(row)
            
            if matching_rows:
                num_rows = len(matching_rows)
                base_qty = payload.quantity // num_rows
                remainder = payload.quantity % num_rows
                
                for i, row in enumerate(matching_rows):
                    qty_col = "available_quantity" if "available_quantity" in row else "quantity"
                    qty_to_set = base_qty + (1 if i < remainder else 0)
                    supabase.table("inventory").update({
                        qty_col: qty_to_set,
                        "quantity": qty_to_set
                    }).eq("id", row["id"]).execute()
        except Exception as e:
            logger.warning(f"Supabase inventory sync failed (in-memory still updated): {e}")

    return {
        "status": "updated",
        "warehouse_id": warehouse_id,
        "item_name": item_name,
        "old_quantity": old_qty,
        "new_quantity": payload.quantity,
    }


@app.post("/system/reset")
async def reset_system(cascade: bool = True):
    import urllib.request

    state["blocked_roads"] = []
    state["need_cards"] = []
    state["dispatches"] = []
    
    # Reset WAREHOUSES in-memory to original defaults
    WAREHOUSES.clear()
    for w in deepcopy(DEFAULT_WAREHOUSES):
        WAREHOUSES.append(w)
    
    # Trigger DataIngestion demo reset if it's active and cascade is True
    if cascade:
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:8000/demo/reset?cascade=false",
                method="POST",
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                pass
        except Exception:
            pass

    if supabase:
        try:
            # Delete dispatches first
            supabase.table("dispatches").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            # Delete blocked roads
            supabase.table("blocked_roads").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            # Delete need_cards
            supabase.table("need_cards").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            # Delete incidents
            supabase.table("incidents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            
            # Reset inventory in Supabase by distributing DEFAULT_WAREHOUSES quantities
            res = supabase.table("inventory").select("*").execute()
            rows = res.data or []
            
            # Find all unique shelter_ids currently registered in the database
            shelter_ids = set()
            for row in rows:
                sid = row.get("shelter_id") or row.get("location")
                if sid:
                    shelter_ids.add(sid)
            
            # Ensure each shelter has all resources defined in its corresponding warehouse template
            for shelter_id in shelter_ids:
                wh_id = resolve_warehouse_id({"shelter_id": shelter_id})
                wh_default = next((w for w in DEFAULT_WAREHOUSES if w["id"] == wh_id), None)
                if not wh_default:
                    continue
                
                for res_item in wh_default["resources"]:
                    item_name = res_item["item_name"]
                    canonical = resolve_item_type(item_name)
                    
                    # Find all database rows matching this shelter and item type
                    matching_rows = []
                    for row in rows:
                        row_sid = row.get("shelter_id") or row.get("location")
                        row_canonical = resolve_item_type(row.get("item_name") or "")
                        if row_sid == shelter_id and row_canonical == canonical:
                            matching_rows.append(row)
                    
                    default_qty = res_item["quantity"]
                    
                    if matching_rows:
                        # Distribute default quantity among duplicate rows if they exist
                        num_rows = len(matching_rows)
                        base_qty = default_qty // num_rows
                        remainder = default_qty % num_rows
                        for i, row in enumerate(matching_rows):
                            qty_col = "available_quantity" if "available_quantity" in row else "quantity"
                            qty_to_set = base_qty + (1 if i < remainder else 0)
                            supabase.table("inventory").update({
                                qty_col: qty_to_set,
                                "quantity": qty_to_set
                            }).eq("id", row["id"]).execute()
                    else:
                        # Insert missing inventory row (e.g., Rescue Teams)
                        new_row = {
                            "item_name": item_name,
                            "item_type": canonical.lower(),
                            "quantity": default_qty,
                            "available_quantity": default_qty,
                            "unit": res_item["unit"],
                            "shelter_id": shelter_id,
                            "location": "Unknown"
                        }
                        # Normalize item_type field
                        if "water" in item_name.lower():
                            new_row["item_type"] = "water"
                        elif "food" in item_name.lower():
                            new_row["item_type"] = "food"
                        elif "med" in item_name.lower():
                            new_row["item_type"] = "meds"
                        elif "team" in item_name.lower():
                            new_row["item_type"] = "rescue_team"
                            
                        logger.info(f"Self-healing: Inserting missing {item_name} row for shelter {shelter_id}")
                        supabase.table("inventory").insert(new_row).execute()
        except Exception as e:
            logger.error(f"Failed to reset Supabase inventory: {e}", exc_info=True)
            
    return {"status": "success"}
