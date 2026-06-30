import random
from typing import Dict, List, Any, Optional

class IncidentKnowledgeEngine:
    """
    Incident Knowledge Repository for SentinelNet AI.
    Stores and matches resolved incidents and their successful remediation steps.
    """

    def __init__(self):
        # Seed historical resolved incidents for matching
        self.historical_records: List[Dict[str, Any]] = [
            {
                "id": "KB-INC-001",
                "failure_type": "Congestion",
                "device_id": "BR-Chennai",
                "description": "Bandwidth saturation on Chennai branch link.",
                "remediation": "PB_QOS_ADJUST",
                "resolution": "Applied dynamic rate limiting and prioritized VoIP default queues.",
                "date_resolved": "2026-06-25 14:22:10",
                "metrics_signature": {"packet_loss": 8.0, "latency": 110.0}
            },
            {
                "id": "KB-INC-002",
                "failure_type": "IPSec Tunnel Failure",
                "device_id": "BR-Delhi",
                "description": "Tunnel down on Delhi branch router due to Main Mode SA negotiation timeout.",
                "remediation": "PB_IPSEC_RESTART",
                "resolution": "Flushed crypto SAs and forced Phase 1 dynamic rekeying.",
                "date_resolved": "2026-06-28 09:15:43",
                "metrics_signature": {"packet_loss": 100.0, "latency": 999.0}
            },
            {
                "id": "KB-INC-003",
                "failure_type": "Routing Loop",
                "device_id": "HUB-Mumbai",
                "description": "Transit routing loop bouncing frames and spiking core aggregator CPU.",
                "remediation": "PB_RESET_METRICS",
                "resolution": "Mismatched interface costs corrected on redundant routing tables.",
                "date_resolved": "2026-06-29 18:33:04",
                "metrics_signature": {"cpu_usage": 94.0, "latency": 280.0}
            },
            {
                "id": "KB-INC-004",
                "failure_type": "BGP Route Flap",
                "device_id": "HUB-Mumbai",
                "description": "BGP peering session flap instability on aggregate WAN port.",
                "remediation": "PB_RESET_METRICS",
                "resolution": "Reset BGP daemon and synchronized neighbor hold-timers.",
                "date_resolved": "2026-06-30 11:05:00",
                "metrics_signature": {"bgp_state": "ACTIVE"}
            },
            {
                "id": "KB-INC-005",
                "failure_type": "Configuration Drift",
                "device_id": "BR-Kolkata",
                "description": "MTU config drift causing packet fragmentation drops.",
                "remediation": "PB_REKEY_HARDEN",
                "resolution": "Synchronized router configuration blueprint and corrected interface MTU.",
                "date_resolved": "2026-06-30 22:40:15",
                "metrics_signature": {"interface_errors": 120}
            },
            {
                "id": "KB-INC-006",
                "failure_type": "Interface Failure",
                "device_id": "BR-Hyderabad",
                "description": "Physical GigabitEthernet port link state reported DOWN.",
                "remediation": "PB_RESET_METRICS",
                "resolution": "Aggregated alternate Hub overlay path to avoid physical failure path.",
                "date_resolved": "2026-06-30 23:12:44",
                "metrics_signature": {"link_availability": 0.0}
            }
        ]

    def add_resolved_incident(self, failure_type: str, device_id: str, description: str, remediation: str, resolution: str):
        """Adds a new resolved incident to the repository."""
        self.historical_records.append({
            "id": f"KB-INC-{len(self.historical_records) + 1:03d}",
            "failure_type": failure_type,
            "device_id": device_id,
            "description": description,
            "remediation": remediation,
            "resolution": resolution,
            "date_resolved": "Just now",
            "metrics_signature": {}
        })

    def match_incident(self, current_failure_type: str, current_device_id: str) -> Optional[Dict[str, Any]]:
        """
        Matches a current active incident against historical resolved incidents.
        Returns details of the match and a similarity confidence score.
        """
        if current_failure_type == "None":
            return None

        best_match = None
        highest_score = 0.0

        for record in self.historical_records:
            score = 0.0
            
            # Match rules
            if record["failure_type"].lower() == current_failure_type.lower():
                score += 0.60
            if record["device_id"] == current_device_id:
                score += 0.30
                
            # Random jitter for realistic matching variance
            if score > 0:
                score += random.uniform(0.01, 0.09)
                score = min(1.0, score)

            if score > highest_score:
                highest_score = score
                best_match = record

        if best_match and highest_score >= 0.50:
            return {
                "kb_id": best_match["id"],
                "similarity_score": round(highest_score, 3),
                "remediation": best_match["remediation"],
                "resolution_summary": best_match["resolution"],
                "resolved_at": best_match["date_resolved"]
            }
            
        return None

# Singleton Instance
incident_knowledge_engine = IncidentKnowledgeEngine()
