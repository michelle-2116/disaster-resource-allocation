"""
Tool definitions for Gemini function calling.

Defines the schema for tools that the AI agent can call.
"""

import json
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger("TOOLS_DEF")


def verified_news_impl(incident_id: str, incident_type: str, location: str, title: str, severity: int, summary: str) -> Dict[str, Any]:
    """
    Implementation of the verified_news tool.
    Called by Gemini when reporting a verified incident.
    
    Args:
        incident_id: Unique identifier for this incident
        incident_type: Type of incident (NATURAL_DISASTER, CONFLICT, PANDEMIC, etc.)
        location: Primary affected location
        title: Short incident title
        severity: Severity level 1-10
        summary: Concise summary of what happened
    
    Returns:
        Structured incident report with timestamp
    """
    logger.info(f"VERIFIED_NEWS: Tool called - ID={incident_id}, Type={incident_type}, Severity={severity}/10")
    
    report = {
        "incident_id": incident_id,
        "incident": {
            "type": incident_type,
            "location": location,
            "title": title,
            "severity": severity,
            "summary": summary,
        },
        "timestamp": datetime.now().isoformat()
    }
    
    return report


def get_verified_news_tool_definition():
    """
    Define the verified_news tool schema for Gemini function calling.
    
    Returns a Tool object compatible with google-genai SDK.
    """
    from google.genai import types
    
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="verified_news",
                description="Report a verified incident or disaster. Call this tool to report each incident found in the news data.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "incident_id": types.Schema(
                            type=types.Type.STRING,
                            description="Unique identifier for this incident (e.g., INCIDENT_LOCATION_DATE)"
                        ),
                        "incident_type": types.Schema(
                            type=types.Type.STRING,
                            description="Type of incident: NATURAL_DISASTER | CONFLICT | PANDEMIC | POLITICAL_CRISIS | ECONOMIC_COLLAPSE | INFRASTRUCTURE_FAILURE | ENVIRONMENTAL_CATASTROPHE"
                        ),
                        "location": types.Schema(
                            type=types.Type.STRING,
                            description="Primary affected location (city, region, country)"
                        ),
                        "title": types.Schema(
                            type=types.Type.STRING,
                            description="Short incident title (5-10 words)"
                        ),
                        "severity": types.Schema(
                            type=types.Type.INTEGER,
                            description="Severity level 1-10 (1=minor, 10=catastrophic)"
                        ),
                        "summary": types.Schema(
                            type=types.Type.STRING,
                            description="Concise summary of what happened (50-200 words)"
                        ),
                    },
                    required=["incident_id", "incident_type", "location", "title", "severity", "summary"]
                )
            )
        ]
    )


def execute_verified_news_tool(tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the verified_news tool with incident data.
    
    Args:
        tool_input: Dict with incident parameters from Gemini function call
    
    Returns:
        Structured incident report with timestamp
    """
    # Handle both flat and nested structures
    if "incident" in tool_input and isinstance(tool_input["incident"], dict):
        # Nested structure from old format
        incident_id = tool_input.get("incident_id", "UNKNOWN")
        incident_type = tool_input["incident"].get("type", "UNKNOWN")
        location = tool_input["incident"].get("location", "UNKNOWN")
        title = tool_input["incident"].get("title", "")
        severity = tool_input["incident"].get("severity", 0)
        summary = tool_input["incident"].get("summary", "")
    else:
        # Flat structure from Gemini function call
        incident_id = tool_input.get("incident_id", "UNKNOWN")
        incident_type = tool_input.get("incident_type", "UNKNOWN")
        location = tool_input.get("location", "UNKNOWN")
        title = tool_input.get("title", "")
        severity = int(tool_input.get("severity", 0))
        summary = tool_input.get("summary", "")
    
    logger.info(f"VERIFIED_NEWS: Executing tool for ID={incident_id}, Type={incident_type}, Severity={severity}/10")
    
    report = {
        "incident_id": incident_id,
        "incident": {
            "type": incident_type,
            "location": location,
            "title": title,
            "severity": severity,
            "summary": summary,
        },
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"VERIFIED_NEWS: Report generated for '{incident_id}'")
    
    return report


def format_verified_news_as_json(report: Dict[str, Any]) -> str:
    """
    Format the verified news report as nicely formatted JSON.
    
    Args:
        report: The verified news report
    
    Returns:
        Formatted JSON string
    """
    return json.dumps(report, indent=2, ensure_ascii=False)
