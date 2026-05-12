from pydantic import BaseModel
from typing import List, Optional

class IncidentCreate(BaseModel):
    title: str
    type: str
    severity: str
    summary: str
    location_lat: float
    location_lng: float

class AllocationRequest(BaseModel):
    incident_id: str
    shelter_id: str
    item_type: str
    quantity: int

class BlockedRoad(BaseModel):
    lat: float
    lng: float
    reason: str