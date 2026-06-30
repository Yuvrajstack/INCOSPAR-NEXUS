import os
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List

from app.core.database import get_db
from app.services.agent_orchestrator import copilot_orchestrator
from app.services.rag_pipeline import rag_retrieval_engine
from app.services.network_simulator import simulator

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"

class SessionHistoryResponse(BaseModel):
    history: List[Dict[str, str]]

@router.post("/copilot/chat", response_model=Dict[str, Any])
def post_copilot_chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    POST endpoint to converse with the NOC Copilot.
    Processes queries with RAG and Multi-Agents, returning structured JSON response.
    """
    try:
        response_json = copilot_orchestrator.process_operator_query(req.message, req.session_id, db)
        return response_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/copilot/history", response_model=Dict[str, Any])
def get_copilot_history(session_id: str = "default_session"):
    """GET endpoint to fetch session memory context."""
    history = copilot_orchestrator.get_session_history(session_id)
    return {"session_id": session_id, "history": history}

@router.post("/copilot/clear")
def clear_copilot_history(session_id: str = "default_session"):
    """POST endpoint to clear chat memory."""
    copilot_orchestrator.clear_session_history(session_id)
    return {"status": "success", "message": f"Session memory '{session_id}' cleared."}

@router.get("/copilot/context", response_model=Dict[str, Any])
def get_copilot_context(db: Session = Depends(get_db)):
    """GET endpoint to fetch live telemetry and device summaries fed to the Copilot."""
    # Gather live nodes
    devices = simulator.device_states
    active_anomaly = simulator.active_anomaly
    
    return {
        "active_anomaly": active_anomaly,
        "device_count": len(devices),
        "devices_status": {dev_id: state["status"] for dev_id, state in devices.items()}
    }

@router.get("/copilot/knowledge", response_model=List[Dict[str, Any]])
def get_copilot_knowledge():
    """GET endpoint to query local vector DB indexed documents."""
    docs = rag_retrieval_engine.loader.load_documents()
    indexed_docs = []
    for d in docs:
        indexed_docs.append({
            "filename": d["source"],
            "character_count": len(d["content"]),
            "status": "indexed_local_vector_db"
        })
    return indexed_docs

@router.websocket("/ws/copilot")
async def websocket_copilot_endpoint(websocket: WebSocket, session_id: str = "default_session"):
    """
    WebSocket channel to stream Copilot responses, token-by-token,
    along with reasoning steps, decision models, and citations.
    """
    await websocket.accept()
    db = next(get_db())
    
    try:
        while True:
            # Wait for text query from operator client
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                query = msg.get("message", "")
                sess_id = msg.get("session_id", session_id)
            except json.JSONDecodeError:
                query = data
                sess_id = session_id
                
            if not query:
                continue
                
            # 1. Send reasoning state updates
            await websocket.send_json({"type": "status", "status": "agent_reasoning", "message": "Invoking Prediction & Correlation Agents..."})
            await asyncio.sleep(0.3)
            await websocket.send_json({"type": "status", "status": "agent_reasoning", "message": "Retrieving standard runbooks from local Vector DB..."})
            await asyncio.sleep(0.3)
            
            # 2. Process query using Agent Orchestrator
            response_json = copilot_orchestrator.process_operator_query(query, sess_id, db)
            summary_text = response_json.get("summary", "")
            
            # 3. Simulate real-time token streaming typewriter effect
            await websocket.send_json({"type": "status", "status": "streaming", "message": "Generating Response..."})
            
            # Stream summary chunk-by-chunk (5-6 characters per tick)
            chunk_size = 6
            for idx in range(0, len(summary_text), chunk_size):
                chunk = summary_text[idx : idx + chunk_size]
                await websocket.send_json({
                    "type": "chunk",
                    "chunk": chunk
                })
                # Simulate network speed latency
                await asyncio.sleep(0.015)
                
            # 4. Stream full final JSON structures for rendering Cards and breakdowns
            await websocket.send_json({
                "type": "final",
                "payload": response_json
            })
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket Copilot error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        db.close()
