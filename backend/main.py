from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import models
from database import supabase
from services.ingestion import IngestionEngine 
from services.allocator import process_allocation_logic
from services.routing import get_route
from services.allocator import process_allocation_logic

app = FastAPI(title="Aegis Disaster API")

# Initialize AI Ingestion
ingestion_engine = IngestionEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Aegis API is online"}

@app.post("/ingest")
async def ingest_news(payload: dict):
    if "text" not in payload:
        raise HTTPException(status_code=400, detail="Missing 'text' in payload")
    result = await ingestion_engine.verify_and_log(payload['text'])
    return {"status": "processed", "data": result}

@app.get("/map-data")
async def get_map_data():
    return {
        "incidents": supabase.table("incidents").select("*").execute().data,
        "shelters": supabase.table("shelters").select("*").execute().data,
        "dispatches": supabase.table("dispatches").select("*").execute().data,
        "need_cards": supabase.table("need_cards").select("*").execute().data,
        "inventory": supabase.table("inventory").select("*, shelters(name)").execute().data, # Joined data
        "blocked_roads": supabase.table("blocked_roads").select("*").execute().data
    }
@app.post("/system/reset")
async def reset_system():
    # Clear all dynamic data
    supabase.table("dispatches").delete().neq("status", "clear").execute()
    supabase.table("need_cards").delete().neq("status", "clear").execute()
    supabase.table("incidents").delete().neq("status", "clear").execute()
    
    # Reset Inventory: Hub to 5000, others to 0
    hub_id = '00000000-0000-0000-0000-000000000000'
    supabase.table("inventory").update({"quantity": 5000}).eq("shelter_id", hub_id).execute()
    supabase.table("inventory").update({"quantity": 0}).neq("shelter_id", hub_id).execute()
    
    return {"status": "success"}

@app.post("/allocate/approve/{need_id}")
async def approve_allocation(need_id: str):
    success, msg = process_allocation_logic(need_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    # Try to fetch route after approval
    need = supabase.table("need_cards").select("*, shelters(*)").eq("id", need_id).single().execute()
    if need.data:
        warehouse = {"lat": 12.9716, "lng": 77.5946} # Bangalore Hub 
        route_data = get_route(warehouse['lat'], warehouse['lng'], 
                               need.data['shelters']['lat'], need.data['shelters']['lng'])
        
        if route_data:
            supabase.table("dispatches").insert({
                "need_card_id": need_id,
                "route_geometry": route_data['geometry'],
                "distance": route_data['distance'],
                "estimated_time": route_data['duration']
            }).execute()
    
    return {"status": "approved", "message": msg}

@app.post("/needs")
async def create_need(payload: dict):
    # payload: {incident_id, shelter_id, item_type, requested_qty}
    result = supabase.table("need_cards").insert({
        "incident_id": payload['incident_id'],
        "shelter_id": payload['shelter_id'],
        "item_type": payload['item_type'],
        "requested_qty": int(payload['requested_qty']),
        "status": "pending_approval"
    }).execute()
    return {"status": "success", "data": result.data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)