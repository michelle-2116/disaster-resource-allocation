import os
import math
import google.generativeai as genai
from database import supabase

class IngestionEngine:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-flash-latest')

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

    async def verify_and_log(self, news_text: str):
        # 1. AI Analysis
        prompt = f"""
        Analyze this disaster news: "{news_text}"
        Return ONLY a JSON object with:
        {{
          "title": "Short title",
          "type": "flood/fire/landslide/earthquake",
          "severity": "low/medium/high/critical",
          "lat": numerical_latitude,
          "lng": numerical_longitude,
          "recommended_resource": "Food Rations/Water/Medical Kits",
          "recommended_qty": 500
        }}
        """
        response = self.model.generate_content(prompt)
        import json
        data = json.loads(response.text.replace('```json', '').replace('```', ''))

        # 2. Save Incident
        incident = supabase.table("incidents").insert({
            "title": data['title'], "type": data['type'], 
            "severity": data['severity'], "location_lat": data['lat'], "location_lng": data['lng']
        }).execute().data[0]

        # 3. AUTO-AGENT LOGIC: Find Closest Shelter
        shelters = supabase.table("shelters").select("*").eq("is_hub", False).execute().data
        
        best_shelter = None
        min_dist = float('inf')
        
        for s in shelters:
            dist = self.calculate_distance(data['lat'], data['lng'], s['lat'], s['lng'])
            if dist < min_dist:
                min_dist = dist
                best_shelter = s

        # 4. Auto-Generate the Need Card
        if best_shelter:
            supabase.table("need_cards").insert({
                "incident_id": incident['id'],
                "shelter_id": best_shelter['id'],
                "item_type": data['recommended_resource'],
                "requested_qty": data['recommended_qty'],
                "status": "pending_approval"
            }).execute()

        return {"status": "Incident verified and Need Card auto-generated for " + best_shelter['name']}