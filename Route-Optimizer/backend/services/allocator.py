from database import supabase

def process_allocation_logic(need_id: str):
    # 1. Get the need request
    need_res = supabase.table("need_cards").select("*").eq("id", need_id).single().execute()
    need = need_res.data
    if not need: return False, "Need not found"
    
    item = need['item_type']
    qty = need['requested_qty']
    target_shelter_id = need['shelter_id']
    hub_id = '00000000-0000-0000-0000-000000000000'

    # 2. Check Hub Stock
    hub_inv = supabase.table("inventory").select("*").eq("shelter_id", hub_id).eq("item_name", item).single().execute().data
    
    if hub_inv and hub_inv['quantity'] >= qty:
        # A: Deduct from Hub
        supabase.table("inventory").update({"quantity": hub_inv['quantity'] - qty}).eq("id", hub_inv['id']).execute()
        
        # B: Add to Target Shelter
        shelter_inv = supabase.table("inventory").select("*").eq("shelter_id", target_shelter_id).eq("item_name", item).single().execute().data
        if shelter_inv:
            supabase.table("inventory").update({"quantity": shelter_inv['quantity'] + qty}).eq("id", shelter_inv['id']).execute()
        
        # C: Mark Need as Approved
        supabase.table("need_cards").update({"status": "approved"}).eq("id", need_id).execute()
        return True, f"Supplies moved: Hub -> Shelter"
    
    return False, "Insufficient stock at Bangalore Hub."