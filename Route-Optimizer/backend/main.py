from __future__ import annotations

import math
import re
from copy import deepcopy
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.routing import get_route


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
            {"item_name": "Blankets", "quantity": 2100, "unit": "units", "priority": "medium", "weight_kg": 1.1},
            {"item_name": "Rescue Boats", "quantity": 14, "unit": "boats", "priority": "critical", "weight_kg": 95},
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
            {"item_name": "Fuel", "quantity": 3200, "unit": "liters", "priority": "high", "weight_kg": 0.74},
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
            {"item_name": "Tarpaulins", "quantity": 850, "unit": "sheets", "priority": "medium", "weight_kg": 2.2},
        ],
    },
]

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
    "blanket": "Blankets",
    "blankets": "Blankets",
    "boat": "Rescue Boats",
    "boats": "Rescue Boats",
    "fuel": "Fuel",
    "tarpaulin": "Tarpaulins",
    "tarpaulins": "Tarpaulins",
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


def distance_km(a: dict, b: dict) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, [a["lat"], a["lng"], b["lat"], b["lng"]])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    hav = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(hav))


def warehouse_stock(warehouse: dict, item_name: str) -> int:
    for resource in warehouse["resources"]:
        if resource["item_name"] == item_name:
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


def route_preview_for_need(need: dict) -> dict | None:
    shelter = next((s for s in SHELTERS if s["id"] == need["shelter_id"]), None)
    if not shelter:
        return None
    warehouse = choose_warehouse(shelter, need["item_type"], need["requested_qty"])
    if not warehouse:
        return None
    route = get_route(
        warehouse["lat"],
        warehouse["lng"],
        shelter["lat"],
        shelter["lng"],
        avoid_points=state["blocked_roads"],
    )
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
        "blocked_roads": len(state["blocked_roads"]),
        "need_cards": len(state["need_cards"]),
        "dispatches": len(state["dispatches"]),
    }


@app.get("/map-data")
async def get_map_data():
    suggested_routes = [
        route
        for route in (route_preview_for_need(need) for need in state["need_cards"] if need["status"] == "pending_approval")
        if route
    ]
    return {
        "center": WAYANAD_CENTER,
        "warehouses": WAREHOUSES,
        "shelters": SHELTERS,
        "incidents": INCIDENTS,
        "need_cards": state["need_cards"],
        "dispatches": state["dispatches"],
        "suggested_routes": suggested_routes,
        "blocked_roads": state["blocked_roads"],
        "inventory": [
            {**resource, "id": f"{warehouse['id']}-{resource['item_name']}", "warehouse_id": warehouse["id"], "warehouse_name": warehouse["name"]}
            for warehouse in WAREHOUSES
            for resource in warehouse["resources"]
        ],
    }


@app.post("/allocate/approve/{need_id}")
async def approve_allocation(need_id: str):
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
    block = {
        "id": f"block-{uuid4()}",
        "lat": payload.lat,
        "lng": payload.lng,
        "radius_meters": payload.radius_meters,
        "reason": payload.reason,
        "source": payload.source,
        "created_at": "live",
    }
    state["blocked_roads"].append(block)
    rebuild_dispatches()
    return {"status": "blocked_road_added", "block": block, "dispatches": state["dispatches"]}


@app.post("/discord/road-report")
async def ingest_discord_report(payload: DiscordInput):
    parsed = parse_discord_message(payload.message)
    block = RoadBlockInput(**parsed)
    return await add_blocked_road(block)


@app.post("/system/reset")
async def reset_system():
    state["blocked_roads"] = deepcopy(INITIAL_BLOCKS)
    state["need_cards"] = deepcopy(NEED_CARDS)
    state["dispatches"] = []
    return {"status": "success"}
