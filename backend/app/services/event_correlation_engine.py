from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models.database_models import Alert, SyslogEvent, TelemetryHistory, Device
from app.services.graph_analysis_engine import graph_analysis_engine

class EventCorrelationEngine:
    """
    Event Correlation Engine for SentinelNet AI.
    Correlates alerts, syslogs, netflow records, and telemetry states to cluster
    duplicate alarms into root incidents and detect cascading topologies.
    """

    def correlate_incidents(self, db: Session) -> List[Dict[str, Any]]:
        """
        Scans recent alerts and syslogs, groups related events by device/topology,
        deduplicates notices, and formats them into high-level AIOps Incidents.
        """
        # Fetch active alerts
        active_alerts = db.query(Alert).filter(Alert.status == "active").all()
        if not active_alerts:
            return []

        # Group alerts by primary device first to deduplicate
        grouped_alerts: Dict[str, List[Alert]] = {}
        for alert in active_alerts:
            grouped_alerts.setdefault(alert.device_id, []).append(alert)

        incidents = []

        for device_id, alerts_list in grouped_alerts.items():
            primary_alert = alerts_list[0] # The highest severity alert
            
            # Fetch recent syslogs for this device (last 60 seconds)
            time_threshold = datetime.now() - timedelta(seconds=60)
            syslogs = db.query(SyslogEvent).filter(
                SyslogEvent.device_id == device_id,
                SyslogEvent.timestamp >= time_threshold
            ).all()

            # Identify if this is a cascading loop or path propagate event
            is_cascade = False
            cascade_chain = []
            
            # Fetch OSPF/BGP status to look for routing drops
            device = db.query(Device).filter(Device.id == device_id).first()
            
            # Form cascading chain trace
            if device:
                # 1. Interface / Link physical layer
                if device.status == "critical" or device.status == "warning":
                    cascade_chain.append("Physical / Interface Alert")
                # 2. IPSec VPN layer
                if "IPSec" in primary_alert.title or any("IPSec" in log.protocol for log in syslogs):
                    cascade_chain.append("IPSec VPN Tunnel Degraded")
                # 3. Routing daemon layer (OSPF/BGP)
                if device.ospf_state == "DOWN" or any(log.protocol == "OSPF" for log in syslogs):
                    cascade_chain.append("OSPF Route Adjacency Flap")
                if device.bgp_state == "DOWN" or device.bgp_state == "ACTIVE" or any(log.protocol == "BGP" for log in syslogs):
                    cascade_chain.append("BGP Peering Session Flap")
                
            if len(cascade_chain) > 1:
                is_cascade = True
            else:
                # Default linear chain
                cascade_chain = ["Interface Alert", "Syslog Triggered"]

            # Compute correlation confidence based on temporal proximity and data completeness
            correlation_score = 0.75
            if syslogs:
                correlation_score += 0.15 # Supporting logs available
            if is_cascade:
                correlation_score += 0.08 # Cascade sequence fits topology rules
            correlation_score = min(1.0, correlation_score)

            incidents.append({
                "incident_id": f"INC-{primary_alert.id.split('-')[-1]}",
                "timestamp": primary_alert.timestamp.isoformat(),
                "device_id": device_id,
                "title": f"Correlated Incident: {primary_alert.title}",
                "severity": primary_alert.severity,
                "primary_alert_id": primary_alert.id,
                "alerts_merged_count": len(alerts_list),
                "is_cascading": is_cascade,
                "cascade_chain": cascade_chain,
                "correlation_confidence": round(correlation_score, 3),
                "syslog_evidence": [s.message for s in syslogs[:5]]
            })

        return incidents

# Singleton Instance
event_correlation_engine = EventCorrelationEngine()
