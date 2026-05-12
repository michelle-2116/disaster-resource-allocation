# These are the definitions Gemini uses to understand how to call functions
INCIDENT_TOOL_SCHEMA = {
    "name": "create_incident",
    "description": "Logs a verified disaster incident into the system database",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short descriptive title of the disaster"},
            "type": {"type": "string", "enum": ["flood", "fire", "earthquake", "hurricane"]},
            "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            "summary": {"type": "string", "description": "2-sentence summary of the situation"},
            "lat": {"type": "number", "description": "Latitude of the impact zone"},
            "lng": {"type": "number", "description": "Longitude of the impact zone"}
        },
        "required": ["title", "type", "severity", "lat", "lng"]
    }
}