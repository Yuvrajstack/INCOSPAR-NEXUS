from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.database_models import Alert, SyslogEvent
from app.schemas.telemetry_schemas import AlertSchema, SyslogEventSchema, FaultInjectionRequest
from app.services.network_simulator import simulator

router = APIRouter()

@router.get("/alerts", response_model=List[AlertSchema])
def get_alerts(
    status: str = Query(default="active"),
    db: Session = Depends(get_db)
):
    """Retrieve active or resolved network alerts."""
    return db.query(Alert).filter(Alert.status == status).order_by(Alert.timestamp.desc()).all()

@router.get("/syslog", response_model=List[SyslogEventSchema])
def get_syslogs(
    limit: int = Query(default=50, lte=200),
    db: Session = Depends(get_db)
):
    """Retrieve recent syslog log streams."""
    return db.query(SyslogEvent).order_by(SyslogEvent.timestamp.desc()).limit(limit).all()

@router.post("/inject-fault")
def inject_fault(
    req: FaultInjectionRequest,
    db: Session = Depends(get_db)
):
    """Manually inject a fault scenario into the simulation engine."""
    valid_scenarios = [
        "CONGESTION_BR3", "BGP_FLAP", "OSPF_FAIL", 
        "MPLS_FAIL", "IPSEC_DEGRADED", "CONFIG_DRIFT", "INTERFACE_FAIL",
        "TUNNEL_BR1_DOWN", "ROUTING_LOOP_HUB"
    ]
    if req.scenario not in valid_scenarios:
        raise HTTPException(status_code=400, detail=f"Invalid fault scenario. Must be one of {valid_scenarios}")
    
    simulator.inject_fault(req.scenario, db)
    return {"status": "success", "message": f"Injected fault scenario: {req.scenario}"}

@router.post("/recover")
def recover_network(db: Session = Depends(get_db)):
    """Clear all fault injections and restore all devices to normal operation."""
    simulator.recover_network(db)
    return {"status": "success", "message": "Triggered network recovery."}
