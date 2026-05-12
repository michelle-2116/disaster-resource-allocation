from database import supabase

def create_incident(title, type, severity, summary, lat, lng):
    """
    Actual database logic to store the incident.
    """
    try:
        data = {
            "title": title,
            "type": type,
            "severity": severity,
            "summary": summary,
            "location_lat": float(lat),
            "location_lng": float(lng),
            "status": "verified"
        }
        supabase.table("incidents").insert(data).execute()
        return f"Successfully logged incident: {title}"
    except Exception as e:
        return f"Database error: {str(e)}"