# main.py or routes/map.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from database import get_db
from models import User, IncidentReport, EvacuationRequest
from pydantic import BaseModel

router = APIRouter()

class GeoPoint(BaseModel):
    name: str
    lat: float
    lng: float

class IncidentPoint(BaseModel):
    description: str
    lat: float
    lng: float

class EvacuationPoint(BaseModel):
    description: str
    lat: float
    lng: float
    priority: str = "normal"

class IntelligenceMapResponse(BaseModel):
    citizens: List[GeoPoint]
    incidents: List[IncidentPoint]
    evacuations: List[EvacuationPoint]

@router.get("/intelligence-map/{country}", response_model=IntelligenceMapResponse)
async def get_intelligence_map(country: str, db: Session = Depends(get_db)):
    """
    Get geospatial data for diaspora intelligence mapping
    """
    try:
        # Fetch citizens with location data
        citizens = db.query(User).filter(
            User.country == country,
            User.lat.isnot(None),
            User.lng.isnot(None)
        ).all()

        # Fetch incidents
        incidents = db.query(IncidentReport).filter(
            IncidentReport.embassy_country == country,
            IncidentReport.status == "active"
        ).all()

        # Fetch evacuation requests
        evacuations = db.query(EvacuationRequest).filter(
            EvacuationRequest.country == country,
            EvacuationRequest.status.in_(["pending", "approved"])
        ).all()

        # Return formatted response
        return {
            "citizens": [
                {"name": c.full_name or "Anonymous", "lat": float(c.lat), "lng": float(c.lng)}
                for c in citizens
            ],
            "incidents": [
                {
                    "description": i.description[:100],  # Truncate long descriptions
                    "lat": float(i.lat),
                    "lng": float(i.lng),
                    "severity": i.severity if hasattr(i, 'severity') else "medium"
                }
                for i in incidents
            ],
            "evacuations": [
                {
                    "description": f"Priority: {e.priority} - {e.description[:50]}",
                    "lat": float(e.lat),
                    "lng": float(e.lng),
                    "priority": e.priority if hasattr(e, 'priority') else "normal"
                }
                for e in evacuations
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/intelligence-map/hotspots/{country}")
async def get_hotspots(country: str, db: Session = Depends(get_db)):
    """
    Get incident hotspots for warning generation
    """
    # Group incidents by geographic clusters
    incidents = db.query(IncidentReport).filter(
        IncidentReport.embassy_country == country,
        IncidentReport.status == "active"
    ).all()

    # Simple clustering logic (you might want to use DBSCAN or similar)
    hotspots = []
    if incidents:
        # Group by approximate location (simplified)
        clusters = {}
        for incident in incidents:
            # Round to 2 decimal places for clustering (~1km accuracy)
            key = f"{round(incident.lat, 2)}_{round(incident.lng, 2)}"
            if key not in clusters:
                clusters[key] = {
                    "lat": incident.lat,
                    "lng": incident.lng,
                    "count": 0,
                    "severities": []
                }
            clusters[key]["count"] += 1
            if hasattr(incident, 'severity'):
                clusters[key]["severities"].append(incident.severity)

        # Filter clusters with multiple incidents
        hotspots = [
            {
                "location": {"lat": v["lat"], "lng": v["lng"]},
                "incident_count": v["count"],
                "avg_severity": max(set(v["severities"]), key=v["severities"].count) if v["severities"] else "unknown"
            }
            for v in clusters.values()
            if v["count"] >= 2  # Minimum incidents to be considered a hotspot
        ]

    return {"hotspots": hotspots}