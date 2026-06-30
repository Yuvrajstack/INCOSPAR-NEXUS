from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db, SessionLocal
from app.models.database_models import TelemetryHistory, NetflowRecord
from app.schemas.telemetry_schemas import TelemetryHistorySchema, NetflowRecordSchema
from app.services.network_simulator import simulator

router = APIRouter()

@router.get("/telemetry")
def get_realtime_telemetry():
    """Retrieve the latest real-time telemetry frame for all devices."""
    return list(simulator.device_states.values())

@router.get("/history", response_model=List[TelemetryHistorySchema])
def get_telemetry_history(
    device_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(default=100, lte=1000),
    db: Session = Depends(get_db)
):
    """Retrieve historical time-series telemetry metrics for charting."""
    query = db.query(TelemetryHistory)
    if device_id:
        query = query.filter(TelemetryHistory.device_id == device_id)
    if start_time:
        query = query.filter(TelemetryHistory.timestamp >= start_time)
    if end_time:
        query = query.filter(TelemetryHistory.timestamp <= end_time)
        
    return query.order_by(TelemetryHistory.timestamp.desc()).limit(limit).all()

@router.get("/netflow", response_model=List[NetflowRecordSchema])
def get_netflow(
    limit: int = Query(default=50, lte=200),
    db: Session = Depends(get_db)
):
    """Fetch NetFlow session aggregates."""
    return db.query(NetflowRecord).order_by(NetflowRecord.timestamp.desc()).limit(limit).all()

@router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """WebSocket tunnel to stream real-time JSON frames of devices, alerts, and syslogs."""
    await websocket.accept()
    simulator.active_websockets.add(websocket)
    try:
        while True:
            # Handle incoming control commands from client
            data = await websocket.receive_json()
            action = data.get("action")
            if action == "pause":
                simulator.is_running = False
            elif action == "resume":
                simulator.is_running = True
            elif action == "reset":
                # Clear active anomalies via websocket command
                db = SessionLocal()
                try:
                    simulator.recover_network(db)
                finally:
                    db.close()
    except (WebSocketDisconnect, ConnectionClosedOK, ConnectionClosedError):
        pass
    finally:
        simulator.active_websockets.discard(websocket)
