"""Mock ServiceNow API server for testing."""

from typing import Dict, Any, List
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Header, Response
from pydantic import BaseModel, Field


# In-memory storage for incidents
incidents_db: Dict[str, Dict[str, Any]] = {}


class IncidentCreate(BaseModel):
    """Incident creation request model."""

    short_description: str = Field(..., description="Brief description of the incident")
    description: str | None = Field(None, description="Detailed description")
    assignment_group: str | None = Field(None, description="Assignment group")
    category: str | None = Field(None, description="Incident category")
    urgency: int = Field(3, ge=1, le=5, description="Urgency level (1-5)")
    impact: int = Field(3, ge=1, le=5, description="Impact level (1-5)")
    caller_id: str | None = Field(None, description="Caller/Reporter ID")
    contact_type: str = Field("email", description="Contact type")


class IncidentResponse(BaseModel):
    """Incident response model."""

    sys_id: str
    number: str
    short_description: str
    description: str | None
    assignment_group: str | None
    category: str | None
    urgency: int
    impact: int
    priority: int
    state: str
    caller_id: str | None
    contact_type: str
    sys_created_on: str
    sys_updated_on: str


app = FastAPI(title="Mock ServiceNow API", version="1.0.0")


def calculate_priority(urgency: int, impact: int) -> int:
    """
    Calculate priority based on urgency and impact.

    ServiceNow priority matrix:
    - Critical (1): Urgency 1-2, Impact 1-2
    - High (2): Urgency 1-3, Impact 1-3
    - Moderate (3): Urgency 2-4, Impact 2-4
    - Low (4): Urgency 3-5, Impact 3-5
    - Planning (5): Urgency 4-5, Impact 4-5
    """
    avg = (urgency + impact) / 2
    if avg <= 2:
        return 1  # Critical
    elif avg <= 2.5:
        return 2  # High
    elif avg <= 3.5:
        return 3  # Moderate
    elif avg <= 4.5:
        return 4  # Low
    else:
        return 5  # Planning


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "servicenow-mock"}


@app.post("/api/now/table/incident", response_model=Dict[str, IncidentResponse])
async def create_incident(
    incident: IncidentCreate,
    authorization: str | None = Header(None),
    response: Response = None,
) -> Dict[str, IncidentResponse]:
    """
    Create a new incident in ServiceNow.

    Mimics ServiceNow Table API POST /api/now/table/incident endpoint.
    """
    # Generate unique identifiers
    sys_id = str(uuid.uuid4())
    incident_number = f"INC{len(incidents_db) + 1:07d}"
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Calculate priority
    priority = calculate_priority(incident.urgency, incident.impact)

    # Create incident record
    incident_record = {
        "sys_id": sys_id,
        "number": incident_number,
        "short_description": incident.short_description,
        "description": incident.description or "",
        "assignment_group": incident.assignment_group or "",
        "category": incident.category or "Incident",
        "urgency": incident.urgency,
        "impact": incident.impact,
        "priority": priority,
        "state": "1",  # New
        "caller_id": incident.caller_id or "system",
        "contact_type": incident.contact_type,
        "sys_created_on": timestamp,
        "sys_updated_on": timestamp,
    }

    # Store in database
    incidents_db[sys_id] = incident_record

    # Set response status code
    if response:
        response.status_code = 201

    return {"result": IncidentResponse(**incident_record)}


@app.get("/api/now/table/incident/{sys_id}", response_model=Dict[str, IncidentResponse])
async def get_incident(
    sys_id: str, authorization: str | None = Header(None)
) -> Dict[str, IncidentResponse]:
    """Get incident by sys_id."""
    if sys_id not in incidents_db:
        raise HTTPException(status_code=404, detail=f"Incident {sys_id} not found")

    return {"result": IncidentResponse(**incidents_db[sys_id])}


@app.get("/api/now/table/incident", response_model=Dict[str, List[IncidentResponse]])
async def list_incidents(
    sysparm_limit: int = 100,
    sysparm_offset: int = 0,
    sysparm_query: str | None = None,
    authorization: str | None = Header(None),
) -> Dict[str, List[IncidentResponse]]:
    """
    List incidents with optional filtering.

    Supports basic query parameters for filtering.
    """
    incidents = list(incidents_db.values())

    # Apply simple filtering (if query provided)
    if sysparm_query:
        # Simple implementation - just check if query term is in description
        query_lower = sysparm_query.lower()
        incidents = [
            inc
            for inc in incidents
            if query_lower in inc["short_description"].lower()
            or query_lower in inc.get("description", "").lower()
        ]

    # Pagination
    total = len(incidents)
    paginated = incidents[sysparm_offset : sysparm_offset + sysparm_limit]

    return {"result": [IncidentResponse(**inc) for inc in paginated]}


@app.patch("/api/now/table/incident/{sys_id}", response_model=Dict[str, IncidentResponse])
async def update_incident(
    sys_id: str, updates: Dict[str, Any], authorization: str | None = Header(None)
) -> Dict[str, IncidentResponse]:
    """Update an existing incident."""
    if sys_id not in incidents_db:
        raise HTTPException(status_code=404, detail=f"Incident {sys_id} not found")

    # Update incident
    incident = incidents_db[sys_id]
    incident.update(updates)
    incident["sys_updated_on"] = datetime.utcnow().isoformat() + "Z"

    return {"result": IncidentResponse(**incident)}


@app.delete("/api/now/table/incident/{sys_id}")
async def delete_incident(
    sys_id: str, authorization: str | None = Header(None)
) -> Dict[str, str]:
    """Delete an incident (for testing purposes)."""
    if sys_id not in incidents_db:
        raise HTTPException(status_code=404, detail=f"Incident {sys_id} not found")

    del incidents_db[sys_id]
    return {"status": "success", "message": f"Incident {sys_id} deleted"}


@app.get("/api/now/table/incident/stats")
async def get_incident_stats(authorization: str | None = Header(None)) -> Dict[str, Any]:
    """Get incident statistics (custom endpoint for testing)."""
    total = len(incidents_db)

    if total == 0:
        return {
            "total": 0,
            "by_priority": {},
            "by_state": {},
            "by_category": {},
        }

    # Calculate statistics
    by_priority: Dict[int, int] = {}
    by_state: Dict[str, int] = {}
    by_category: Dict[str, int] = {}

    for incident in incidents_db.values():
        priority = incident.get("priority", 3)
        by_priority[priority] = by_priority.get(priority, 0) + 1

        state = incident.get("state", "1")
        by_state[state] = by_state.get(state, 0) + 1

        category = incident.get("category", "Incident")
        by_category[category] = by_category.get(category, 0) + 1

    return {
        "total": total,
        "by_priority": by_priority,
        "by_state": by_state,
        "by_category": by_category,
    }


@app.delete("/api/now/table/incident")
async def clear_all_incidents(authorization: str | None = Header(None)) -> Dict[str, str]:
    """Clear all incidents (for testing purposes)."""
    count = len(incidents_db)
    incidents_db.clear()
    return {"status": "success", "message": f"Cleared {count} incidents"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
