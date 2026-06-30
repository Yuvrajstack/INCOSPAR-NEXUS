from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.database_models import Device
from app.schemas.telemetry_schemas import DeviceSchema

router = APIRouter()

@router.get("", response_model=List[DeviceSchema])
def list_devices(db: Session = Depends(get_db)):
    """List all topological router devices and their current status."""
    devices = db.query(Device).all()
    return devices

@router.get("/{device_id}", response_model=DeviceSchema)
def get_device(device_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a single device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device
