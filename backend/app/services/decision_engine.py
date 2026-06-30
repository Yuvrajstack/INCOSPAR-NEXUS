from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.services.graph_analysis_engine import graph_analysis_engine
from app.services.incident_knowledge_engine import incident_knowledge_engine
from app.services.remediation_playbook_engine import remediation_playbook_engine

class DecisionEngine:
    """
    Decision Engine for SentinelNet AI.
    Integrates risk calculations, blast radius, business impacts, playbooks,
    and historical matches to yield operator recommendations.
    """

    def generate_decision(self, device_id: str, failure_type: str, db: Session) -> Dict[str, Any]:
        """
        Synthesizes active event metadata into a structured AIOps Decision.
        """
        # Fetch matching historical incident details
        kb_match = incident_knowledge_engine.match_incident(failure_type, device_id)
        
        # Fetch recommended playbook
        playbook = remediation_playbook_engine.get_playbook(failure_type, device_id)

        # Dynamic Graph Analysis failure impact
        graph_impact = graph_analysis_engine.analyze_node_failure(device_id)

        # 1. Estimate Business Impact Metrics
        affected_users = graph_impact["affected_users"]
        is_spof = graph_impact["is_spof"]
        mission_criticality = graph_impact["criticality_score"]
        blast_radius = graph_impact["blast_radius"]

        # Calculate SLA impact probability
        sla_impact = 0.0
        if failure_type == "Congestion":
            sla_impact = 45.0
        elif failure_type == "IPSec Tunnel Failure":
            sla_impact = 80.0
        elif failure_type == "Routing Loop":
            sla_impact = 99.0
        elif failure_type == "Configuration Drift":
            sla_impact = 30.0
        elif failure_type == "Interface Failure":
            sla_impact = 60.0

        # Operational Severity
        severity = "LOW"
        if is_spof or blast_radius > 50.0:
            severity = "CRITICAL"
        elif blast_radius > 20.0 or failure_type in ["IPSec Tunnel Failure", "Interface Failure"]:
            severity = "HIGH"
        elif failure_type != "None":
            severity = "MEDIUM"

        # 2. Recommended rerouting / alternative paths
        alternative_path = "All primary paths active. No rerouting needed."
        if failure_type in ["IPSec Tunnel Failure", "Interface Failure", "Congestion"]:
            alternative_path = "Egress route shifted from Primary Tunnel (IKE/OSPF) to Backup Overlay Link via HUB-Mumbai."
        elif failure_type == "Routing Loop":
            alternative_path = "OSPF metrics reprioritized; OSPF Cost incremented on failed interface to enforce alternative path convergence."

        # 3. Decision Confidence Breakdown calculation
        # Baseline confidence factors
        telemetry_quality = 0.95 if failure_type != "None" else 0.99
        prediction_confidence = playbook.get("confidence", 0.90)
        graph_confidence = 0.92
        historical_match_score = kb_match["similarity_score"] if kb_match else 0.0

        # Weighted calculation of the Decision Confidence
        if failure_type == "None":
            decision_confidence = 1.0
        else:
            # 30% Telemetry, 30% Prediction, 20% Graph Topology, 20% History
            decision_confidence = (
                (telemetry_quality * 0.3) + 
                (prediction_confidence * 0.3) + 
                (graph_confidence * 0.2) + 
                (max(0.65, historical_match_score) * 0.2) # default to standard score baseline if no historical match
            )
        
        # Risk assessment text
        risk_assessment = "Minimal network risk. Main primary links operating normally."
        if failure_type != "None":
            risk_assessment = f"Elevated network risk on {device_id}. Potential degradation of routing OSPF paths across branches."

        # Estimated recovery time
        est_recovery_time = "N/A"
        if failure_type != "None":
            est_recovery_time = f"{playbook.get('estimated_execution_time_seconds', 30)}s"

        return {
            "incident_summary": f"Active {failure_type} anomaly detected on device {device_id} affecting topological dependencies.",
            "recommended_action": playbook.get("playbook_name", "Monitor standard baseline"),
            "recovery_priority": "P1 (Immediate Remediation)" if severity in ["HIGH", "CRITICAL"] else ("P2 (Standard Attention)" if severity == "MEDIUM" else "P3 (Standard Monitor)"),
            "estimated_recovery_time": est_recovery_time,
            "risk_assessment": risk_assessment,
            "preventive_recommendation": f"Verify automated key SA rotations parameters and MTU configuration blueprints on {device_id}.",
            "alternative_network_path": alternative_path,
            
            # Decision Confidence Score Breakdown
            "decision_confidence": round(decision_confidence, 3),
            "confidence_breakdown": {
                "telemetry_quality": telemetry_quality,
                "prediction_confidence": prediction_confidence,
                "graph_confidence": graph_confidence,
                "historical_match": historical_match_score
            },

            # Business Impact Engine Outputs
            "business_impact": {
                "affected_branches": graph_impact["affected_branches"],
                "affected_devices": [device_id] if failure_type != "None" else [],
                "affected_services": graph_impact["affected_services"],
                "estimated_users_impacted": affected_users,
                "mission_criticality": mission_criticality,
                "sla_impact": sla_impact,
                "estimated_downtime_minutes": 15 if severity == "MEDIUM" else (45 if severity == "HIGH" else (120 if severity == "CRITICAL" else 0)),
                "operational_severity": severity
            },

            # Blast Radius Engine Outputs
            "blast_radius_analysis": {
                "blast_radius_percent": blast_radius,
                "immediate_impact": f"{device_id} status degraded.",
                "upstream_impact": "DC-Bangalore core sync loops." if device_id != "DC-Bangalore" else "None (Core Root Node).",
                "downstream_impact": "Downstream branches cannot resolve central database queries." if is_spof else "No branches disconnected.",
                "critical_dependencies": ["HUB-Mumbai"] if device_id != "HUB-Mumbai" else ["DC-Bangalore"],
                "is_spof": is_spof,
                "service_propagation_path": f"{device_id} -> HUB-Mumbai -> DC-Bangalore"
            },

            # Playbook Integration
            "playbook": playbook,
            
            # Knowledge Repository Integration
            "historical_match": kb_match
        }

# Singleton Instance
decision_engine = DecisionEngine()
