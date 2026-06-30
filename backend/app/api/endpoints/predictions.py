from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.services.predictive_engine import predictive_engine

router = APIRouter()

@router.get("/predictions", response_model=List[Dict[str, Any]])
def get_predictions(db: Session = Depends(get_db)):
    """
    Retrieve active failure predictions, forecasts, and explainability records
    for all topological network devices.
    """
    return predictive_engine.get_predictions(db)

@router.get("/prediction-history", response_model=List[Dict[str, Any]])
def get_prediction_history(
    limit: int = Query(default=100, lte=1000),
    db: Session = Depends(get_db)
):
    """
    Retrieve persisted prediction logs from the SQLite database.
    """
    return predictive_engine.get_prediction_history(db, limit)

@router.get("/risk", response_model=Dict[str, Any])
def get_risk_profile(db: Session = Depends(get_db)):
    """
    Retrieve dynamic risk classification groups and health indices.
    """
    return predictive_engine.get_risk_profile(db)

@router.get("/root-cause", response_model=List[Dict[str, Any]])
def get_root_cause_analysis(db: Session = Depends(get_db)):
    """
    Retrieve details of active anomaly predictions including root cause signals.
    """
    return predictive_engine.get_root_cause_analysis(db)

@router.get("/network-health", response_model=Dict[str, Any])
def get_network_health(db: Session = Depends(get_db)):
    """
    Retrieve the network health score percentage and current operational status.
    """
    return predictive_engine.get_network_health(db)

@router.get("/device/{device_id}/prediction", response_model=Dict[str, Any])
def get_device_prediction(device_id: str, db: Session = Depends(get_db)):
    """
    Retrieve predictions specifically for a single device.
    """
    res = predictive_engine.get_device_prediction(device_id, db)
    if "status" in res and res["status"] == "error":
        raise HTTPException(status_code=404, detail=res["message"])
    return res

@router.get("/summary", response_model=Dict[str, Any])
def get_network_summary(db: Session = Depends(get_db)):
    """
    Retrieve high-level overview summary indicators (devices count, predicted failures,
    network health, and average prediction confidence).
    """
    profile = predictive_engine.get_risk_profile(db)
    preds = predictive_engine.get_predictions(db)
    
    # Calculate predicted failure nodes count
    predicted_failures = sum(1 for p in preds if p["predicted_failure_type"] != "None")
    
    # Calculate average confidence
    avg_conf = sum(p["confidence"] for p in preds) / len(preds) if preds else 0.0
    
    return {
        "healthy_devices": profile["summary"]["healthy_devices"],
        "warning_devices": profile["summary"]["warning_devices"],
        "critical_devices": profile["summary"]["critical_devices"],
        "predicted_failures": predicted_failures,
        "average_confidence": round(avg_conf * 100.0, 1),
        "network_health": profile["network_health_score"]
    }
