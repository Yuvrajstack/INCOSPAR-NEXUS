from fastapi import APIRouter
from app.api.endpoints import devices, telemetry, alerts, predictions, decisions, copilot

api_router = APIRouter()

# Registering endpoints with prefixes
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
api_router.include_router(telemetry.router, tags=["Telemetry"])
api_router.include_router(alerts.router, tags=["Alerts"])
api_router.include_router(predictions.router, tags=["Predictions"])
api_router.include_router(decisions.router, tags=["Decisions"])
api_router.include_router(copilot.router, tags=["Copilot"])


