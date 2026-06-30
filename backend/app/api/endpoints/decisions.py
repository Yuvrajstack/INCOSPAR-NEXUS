from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from app.core.database import get_db
from app.services.event_correlation_engine import event_correlation_engine
from app.services.root_cause_engine import root_cause_engine
from app.services.decision_engine import decision_engine
from app.services.incident_timeline_engine import incident_timeline_engine
from app.services.graph_analysis_engine import graph_analysis_engine
from app.models.database_models import Alert

router = APIRouter()

class SimulationRequest(BaseModel):
    device_id: str # e.g. "HUB-Mumbai", "BR-Delhi"

@router.get("/correlation", response_model=List[Dict[str, Any]])
def get_correlation(db: Session = Depends(get_db)):
    """Retrieve correlated incident alert groups."""
    return event_correlation_engine.correlate_incidents(db)

@router.get("/incident", response_model=Dict[str, Any])
def get_active_incident(db: Session = Depends(get_db)):
    """Retrieve active correlated incident metadata."""
    correlations = event_correlation_engine.correlate_incidents(db)
    if not correlations:
        return {"status": "healthy", "message": "No active incidents detected."}
    
    primary = correlations[0]
    device_id = primary["device_id"]
    
    # Extract failure type from alert
    alert = db.query(Alert).filter(Alert.id == primary["primary_alert_id"]).first()
    failure_type = "None"
    if alert:
        if "Congestion" in alert.title:
            failure_type = "Congestion"
        elif "Tunnel" in alert.title:
            failure_type = "IPSec Tunnel Failure"
        elif "Loop" in alert.title:
            failure_type = "Routing Loop"
        elif "Drift" in alert.title:
            failure_type = "Configuration Drift"
        elif "Link" in alert.title or "Failure" in alert.title:
            failure_type = "Interface Failure"
        elif "BGP" in alert.title or "Flap" in alert.title:
            failure_type = "BGP Route Flap"

    rca = root_cause_engine.analyze_root_cause(device_id, failure_type, db)
    decision = decision_engine.generate_decision(device_id, failure_type, db)

    return {
        "status": "active",
        "correlation": primary,
        "root_cause": rca,
        "decision": decision
    }

@router.get("/timeline", response_model=List[Dict[str, Any]])
def get_timeline(db: Session = Depends(get_db)):
    """Retrieve chronological event timelines for active incidents."""
    correlations = event_correlation_engine.correlate_incidents(db)
    if not correlations:
        return incident_timeline_engine.generate_timeline("None", "None", db)
        
    primary = correlations[0]
    device_id = primary["device_id"]
    alert = db.query(Alert).filter(Alert.id == primary["primary_alert_id"]).first()
    failure_type = "None"
    if alert:
        if "Congestion" in alert.title:
            failure_type = "Congestion"
        elif "Tunnel" in alert.title:
            failure_type = "IPSec Tunnel Failure"
        elif "Loop" in alert.title:
            failure_type = "Routing Loop"
        elif "Drift" in alert.title:
            failure_type = "Configuration Drift"
        elif "Link" in alert.title:
            failure_type = "Interface Failure"
        elif "BGP" in alert.title:
            failure_type = "BGP Route Flap"

    return incident_timeline_engine.generate_timeline(device_id, failure_type, db)

@router.get("/playbook", response_model=Dict[str, Any])
def get_playbook(db: Session = Depends(get_db)):
    """Retrieve recommended playbooks for active incidents."""
    incident = get_active_incident(db)
    if "decision" in incident:
        return incident["decision"]["playbook"]
    return {
        "playbook_id": "PB_NONE",
        "playbook_name": "Standard Monitoring Policy",
        "remediation_steps": ["Maintain baseline monitoring."],
        "confidence": 1.0,
        "estimated_execution_time_seconds": 0,
        "expected_improvement": "Normal baseline operations maintained.",
        "risk_if_ignored": "None"
    }

@router.get("/business-impact", response_model=Dict[str, Any])
def get_business_impact(db: Session = Depends(get_db)):
    """Retrieve business impact assessments for active incidents."""
    incident = get_active_incident(db)
    if "decision" in incident:
        return incident["decision"]["business_impact"]
    return {
        "affected_branches": [],
        "affected_devices": [],
        "affected_services": [],
        "estimated_users_impacted": 0,
        "mission_criticality": 0.0,
        "sla_impact": 0.0,
        "estimated_downtime_minutes": 0,
        "operational_severity": "LOW"
    }

@router.get("/blast-radius", response_model=Dict[str, Any])
def get_blast_radius(db: Session = Depends(get_db)):
    """Retrieve dynamic blast radius calculations for active incidents."""
    incident = get_active_incident(db)
    if "decision" in incident:
        return incident["decision"]["blast_radius_analysis"]
    return {
        "blast_radius_percent": 0.0,
        "immediate_impact": "None. Network operating normally.",
        "upstream_impact": "None.",
        "downstream_impact": "None.",
        "critical_dependencies": [],
        "is_spof": False,
        "service_propagation_path": "N/A"
    }

@router.get("/decision-summary", response_model=Dict[str, Any])
def get_decision_summary(db: Session = Depends(get_db)):
    """Retrieve integrated AIOps decision-making summaries."""
    incident = get_active_incident(db)
    if "decision" in incident:
        return incident["decision"]
    return {
        "incident_summary": "All network interfaces healthy.",
        "recommended_action": "Maintain monitoring protocol.",
        "recovery_priority": "P3 (Standard Monitor)",
        "estimated_recovery_time": "N/A",
        "risk_assessment": "Nominal risks.",
        "preventive_recommendation": "Configure standard audit checks.",
        "alternative_network_path": "All primary paths active.",
        "decision_confidence": 1.0,
        "confidence_breakdown": {
            "telemetry_quality": 0.99,
            "prediction_confidence": 1.0,
            "graph_confidence": 0.95,
            "historical_match": 0.0
        }
    }

@router.post("/simulate", response_model=Dict[str, Any])
def simulate_outage(req: SimulationRequest):
    """
    Simulate a node outage to predict upstream/downstream impacts, affected branches,
    users, services, expected downtime, and recommended rerouting path.
    """
    dev_id = req.device_id
    graph_impact = graph_analysis_engine.analyze_node_failure(dev_id)
    
    # Estimate downtime and routing recovery
    downtime = 30
    if dev_id == "HUB-Mumbai":
        downtime = 120
    elif dev_id == "DC-Bangalore":
        downtime = 240

    rerouting = "No path change. Path remains redundant."
    if dev_id in ["BR-Delhi", "BR-Kolkata", "BR-Chennai", "BR-Hyderabad"]:
        rerouting = "Rerouting traffic through secondary link via alternate overlay paths."
    elif dev_id == "HUB-Mumbai":
        rerouting = "Emergency traffic path rerouted directly to DC core backups if available."

    return {
        "device_id": dev_id,
        "blast_radius_percent": graph_impact["blast_radius"],
        "affected_branches": graph_impact["affected_branches"],
        "affected_services": graph_impact["affected_services"],
        "estimated_users_impacted": graph_impact["affected_users"],
        "is_single_point_of_failure": graph_impact["is_spof"],
        "predicted_downtime_minutes": downtime,
        "recommended_rerouting": rerouting
    }
