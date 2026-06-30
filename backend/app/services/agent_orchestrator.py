import json
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.services.predictive_engine import predictive_engine
from app.services.event_correlation_engine import event_correlation_engine
from app.services.decision_engine import decision_engine
from app.services.incident_knowledge_engine import incident_knowledge_engine
from app.services.remediation_playbook_engine import remediation_playbook_engine
from app.services.rag_pipeline import rag_retrieval_engine
from app.services.local_llm import local_llm_client

class PredictionAgent:
    """Specialized agent to assess model forecasts and future telemetry anomalies."""
    def gather_data(self, db: Session) -> Dict[str, Any]:
        predictions = predictive_engine.run_predictions_pass(db)
        active_predictions = [p for p in predictions if p.get("failure_probability", 0.0) > 0.50]
        return {
            "predictions_analyzed_count": len(predictions),
            "critical_forecasts": active_predictions,
            "confidence_rating": 0.95
        }

class CorrelationAgent:
    """Specialized agent to cluster duplicate alarms and evaluate cascades."""
    def gather_data(self, db: Session) -> Dict[str, Any]:
        incidents = event_correlation_engine.correlate_incidents(db)
        return {
            "active_incidents": incidents,
            "correlation_confidence": 0.94 if incidents else 1.0
        }

class DecisionAgent:
    """Specialized agent to calculate blast radius, rerouting, and business SLA impact."""
    def gather_data(self, db: Session, active_device_id: Optional[str], active_failure_type: Optional[str]) -> Dict[str, Any]:
        if active_device_id and active_failure_type:
            decision = decision_engine.generate_decision(active_device_id, active_failure_type, db)
            return {
                "decision_model": decision,
                "confidence_rating": 0.92
            }
        return {
            "decision_model": None,
            "confidence_rating": 1.0
        }

class KnowledgeAgent:
    """Specialized agent to match active incidents to historical resolved templates."""
    def gather_data(self, failure_type: str, device_id: str) -> Dict[str, Any]:
        kb_match = incident_knowledge_engine.match_incident(failure_type, device_id)
        return {
            "kb_match": kb_match,
            "confidence_rating": 0.91 if kb_match else 0.0
        }

class PlaybookAgent:
    """Specialized agent to provide dynamic CLI step commands and risk indices."""
    def gather_data(self, failure_type: str, device_id: str) -> Dict[str, Any]:
        playbook = remediation_playbook_engine.get_playbook(failure_type, device_id)
        return {
            "playbook": playbook,
            "confidence_rating": 0.94
        }

class CopilotOrchestrator:
    """
    Core orchestrator coordination agent.
    Maintains conversational memory context and coordinates specialized agent datasets.
    """
    
    def __init__(self):
        self.prediction_agent = PredictionAgent()
        self.correlation_agent = CorrelationAgent()
        self.decision_agent = DecisionAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.playbook_agent = PlaybookAgent()
        
        # In-memory chat memory session (keys map to session IDs)
        self.sessions_memory: Dict[str, List[Dict[str, str]]] = {}

    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        return self.sessions_memory.setdefault(session_id, [])

    def clear_session_history(self, session_id: str):
        if session_id in self.sessions_memory:
            self.sessions_memory[session_id] = []

    def process_operator_query(self, query: str, session_id: str, db: Session) -> Dict[str, Any]:
        """
        Coordinates the RAG search, specialized agent parameters, prompt context building,
        and LLM inference. Returns structured JSON schema payload.
        """
        # 1. Retrieve RAG troubleshooting contexts
        retrieved_docs = rag_retrieval_engine.retrieve_context(query, top_k=2)
        rag_context_text = "\n\n".join([
            f"Source: {doc['source']}\n{doc['content']}"
            for doc in retrieved_docs
        ])
        
        # 2. Gather Multi-Agent telemetry structures
        prediction_info = self.prediction_agent.gather_data(db)
        correlation_info = self.correlation_agent.gather_data(db)
        
        # Identify active anomaly details if correlation found
        active_incidents = correlation_info.get("active_incidents", [])
        active_dev = None
        fail_type = "None"
        
        if active_incidents:
            primary = active_incidents[0]
            active_dev = primary["device_id"]
            
            # Match failure keyword
            title = primary["title"]
            if "Congestion" in title:
                fail_type = "Congestion"
            elif "Tunnel" in title:
                fail_type = "IPSec Tunnel Failure"
            elif "Loop" in title:
                fail_type = "Routing Loop"
            elif "Drift" in title:
                fail_type = "Configuration Drift"
            elif "Failure" in title:
                fail_type = "Interface Failure"
            elif "BGP" in title:
                fail_type = "BGP Route Flap"

        decision_info = self.decision_agent.gather_data(db, active_dev, fail_type)
        knowledge_info = self.knowledge_agent.gather_data(fail_type, active_dev or "None")
        playbook_info = self.playbook_agent.gather_data(fail_type, active_dev or "None")

        # 3. Read previous conversation context (Memory)
        history = self.get_session_history(session_id)
        history_summary = ""
        if history:
            history_summary = "Previous Conversation Exchanges:\n" + "\n".join([
                f"- Operator: {item['question']}\n- Copilot: {item['response_summary']}"
                for item in history[-4:] # limit to last 4 exchanges
            ])

        # 4. Construct Structured Prompt instructions
        system_prompt = f"""
You are the fully offline SentinelNet AI AIOps NOC Copilot.
Your response MUST be valid JSON matching the following schema:
{{
  "summary": "Short operator-friendly markdown summary answering the user's question.",
  "overall_confidence": 0.95,
  "prediction_confidence": 0.94,
  "knowledge_confidence": 0.91,
  "decision_confidence": 0.96,
  "rag_score": 0.93,
  "root_cause": "Isolate the root cause if failure active.",
  "business_impact": "Specify branch, users, and SLA impact metrics.",
  "blast_radius": "Specify downstream nodes affected.",
  "recommended_actions": ["CLI step 1", "CLI step 2"],
  "references": ["runbook.md", "Incident #101"]
}}

Live Agent NOC Telemetry:
- Active Predictions: {json.dumps(prediction_info)}
- Correlated Incidents: {json.dumps(correlation_info)}
- Decisions: {json.dumps(decision_info)}
- Knowledge Repository Matches: {json.dumps(knowledge_info)}
- Remediation Playbook: {json.dumps(playbook_info)}

Retrieved Local Runbooks (RAG Context):
{rag_context_text}

{history_summary}
"""

        # 5. Query LLM / Fallback Engine
        response_json = local_llm_client.query_llm(query, system_prompt, session_id)
        
        # Fallback RAG Score assignment from retrieval engine scores
        if retrieved_docs and "rag_score" not in response_json:
            response_json["rag_score"] = retrieved_docs[0]["score"]

        # Append references used from retrieved RAG sources
        if retrieved_docs:
            existing_refs = response_json.setdefault("references", [])
            for doc in retrieved_docs:
                if doc["source"] not in existing_refs:
                    existing_refs.append(doc["source"])

        # 6. Save query and summary to memory
        history.append({
            "question": query,
            "response_summary": response_json.get("summary", "")
        })

        return response_json

# Global Singleton Instance
copilot_orchestrator = CopilotOrchestrator()
