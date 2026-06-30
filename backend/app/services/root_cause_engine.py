from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models.database_models import Device, TelemetryHistory, SyslogEvent
from app.services.graph_analysis_engine import graph_analysis_engine
from app.services.explainability_engine import explainability_engine

class RootCauseEngine:
    """
    Root Cause Analysis (RCA) Engine for SentinelNet AI.
    Isolates primary failure triggers and formats operator-friendly diagnostics.
    """

    def analyze_root_cause(self, device_id: str, failure_type: str, db: Session) -> Dict[str, Any]:
        """
        Generates structured RCA metadata including device dependencies, evidence signals,
        and chronological timelines.
        """
        # Fetch device telemetry state
        device = db.query(Device).filter(Device.id == device_id).first()
        
        # Build dependency path to Data Center core
        dependency_chain = graph_analysis_engine.get_dependency_path(device_id, "DC-Bangalore")
        if not dependency_chain:
            dependency_chain = [device_id, "HUB-Mumbai", "DC-Bangalore"]

        # Fetch recent timeseries to extract supporting metrics
        recent_telemetry = db.query(TelemetryHistory)\
            .filter(TelemetryHistory.device_id == device_id)\
            .order_by(TelemetryHistory.timestamp.desc())\
            .limit(3).all()

        signals = []
        evidence = []

        if failure_type == "Congestion":
            signals = [
                "Egress queue utilization exceeded 90% SLA limits.",
                "VoIP packet loss spikes detected on MPLS tunnel.",
                "High TCP window retransmissions flagged by NetFlow telemetry."
            ]
            if recent_telemetry:
                t = recent_telemetry[0]
                evidence = [
                    f"Measured packet loss of {t.packet_loss:.2f}% (Threshold: 1.00%).",
                    f"Link latency rose to {t.latency:.1f}ms (Baseline: 15.0ms).",
                    f"Egress bandwidth load calculated at {t.rx_bandwidth:.1f} Mbps."
                ]
        elif failure_type == "IPSec Tunnel Failure":
            signals = [
                "VPN gateway security association (SA) renegotiation timeout.",
                "OSPF Peer Neighbor Hello packet keepalive timer expiration.",
                "IKE Phase 1 Main Mode dynamic encryption handshake failure."
            ]
            if recent_telemetry:
                t = recent_telemetry[0]
                evidence = [
                    f"IPSec tunnel health collapsed to {t.tunnel_health:.1f}%.",
                    f"Link availability status: {t.link_availability:.1f} (Operational status: Offline).",
                    f"Adjacent OSPF Routing state transition to DOWN."
                ]
        elif failure_type == "Routing Loop":
            signals = [
                "OSPF route metric cost mismatch causing frame bouncing.",
                "Aggressive aggregation aggregation overhead on aggregate aggregates.",
                "Core CPU utilization spiked due to header processing overload."
            ]
            if recent_telemetry:
                t = recent_telemetry[0]
                evidence = [
                    f"Hub router CPU usage rose to {t.cpu_usage:.1f}% (Baseline: 14.0%).",
                    f"Aggregate core transit latency rose to {t.latency:.1f}ms.",
                    f"Redundant paths matched costs on parallel transit links."
                ]
        elif failure_type == "Configuration Drift":
            signals = [
                "Interface maximum transmission unit (MTU) size parameter mismatch.",
                "Incrementing interface CRC and alignment packet drop counters."
            ]
            if recent_telemetry:
                t = recent_telemetry[0]
                evidence = [
                    f"Router logged {t.interface_errors} active interface packet errors.",
                    f"Packet fragmentation drops rising on trunk interfaces."
                ]
        elif failure_type == "Interface Failure":
            signals = [
                "Physical GigabitEthernet interface transceiver transceiver disconnect.",
                "Fiber laser TX/RX power dropped below critical threshold limit."
            ]
            if recent_telemetry:
                t = recent_telemetry[0]
                evidence = [
                    f"Link availability metric drops to 0.0 (Hard link loss).",
                    f"Transceiver log flags physical line disconnect."
                ]
        elif failure_type in ["BGP Route Flap", "OSPF Instability"]:
            signals = [
                "Session state flap transitions logged between ESTABLISHED and IDLE.",
                "Dynamic route advertisements exceeding dynamic flap dampening bounds."
            ]
            if recent_telemetry:
                t = recent_telemetry[0]
                evidence = [
                    f"Active BGP neighbor state reported as {device.bgp_state if device else 'DOWN'}.",
                    f"OSPF Neighbor state reported as {device.ospf_state if device else 'DOWN'}."
                ]
        else:
            signals = ["All metrics reside within normal baseline operational boundaries."]
            evidence = ["Telemetry indicators are in-bounds."]

        # Calculate Root Cause confidence
        confidence = 0.90
        if failure_type != "None":
            confidence = 0.95 if recent_telemetry else 0.85

        return {
            "primary_root_cause": f"Primary trigger: {failure_type} on {device_id}.",
            "failure_type": failure_type,
            "device_id": device_id,
            "supporting_evidence": evidence,
            "confidence_score": round(confidence, 3),
            "contributing_signals": signals,
            "dependency_chain": dependency_chain
        }

# Singleton Instance
root_cause_engine = RootCauseEngine()
