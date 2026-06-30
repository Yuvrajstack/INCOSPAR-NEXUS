import asyncio
import random
import uuid
from datetime import datetime
from typing import Dict, List, Set, Optional
from sqlalchemy.orm import Session
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.database_models import Device, TelemetryHistory, NetflowRecord, Alert, SyslogEvent
from app.services.predictive_engine import predictive_engine
from app.services.event_correlation_engine import event_correlation_engine
from app.services.root_cause_engine import root_cause_engine
from app.services.decision_engine import decision_engine
from app.services.incident_timeline_engine import incident_timeline_engine


# Devices definition matching topological requirements
DEVICE_DEFS = [
    {"id": "DC-Bangalore", "name": "Bangalore DC (Core)", "type": "DC", "ip": "10.10.0.1"},
    {"id": "HUB-Mumbai", "name": "Mumbai Hub (Transit)", "type": "Hub", "ip": "10.20.0.1"},
    {"id": "BR-Delhi", "name": "New Delhi Branch (BR-1)", "type": "Branch", "ip": "10.30.1.1"},
    {"id": "BR-Kolkata", "name": "Kolkata Branch (BR-2)", "type": "Branch", "ip": "10.30.2.1"},
    {"id": "BR-Chennai", "name": "Chennai Branch (BR-3)", "type": "Branch", "ip": "10.30.3.1"},
    {"id": "BR-Hyderabad", "name": "Hyderabad Branch (BR-4)", "type": "Branch", "ip": "10.30.4.1"}
]

class NetworkSimulator:
    def __init__(self):
        self.is_running: bool = True
        self.active_anomaly: Optional[str] = None
        self.active_websockets: Set = set()
        
        # In-memory current states
        self.device_states: Dict[str, dict] = {}
        self.bgp_flap_timer: int = 0
        self.bgp_flap_state: bool = True
        
        self.initialize_states()

    def initialize_states(self):
        """Setup initial healthy device states."""
        for d in DEVICE_DEFS:
            self.device_states[d["id"]] = {
                "id": d["id"],
                "name": d["name"],
                "type": d["type"],
                "ip_address": d["ip"],
                "status": "healthy",
                "cpu_usage": 12.0 + random.uniform(0, 5),
                "memory_usage": 35.0 + random.uniform(0, 10),
                "bgp_state": "ESTABLISHED" if d["type"] != "DC" else None,
                "ospf_state": "FULL" if d["type"] in ["DC", "Hub"] else None,
                "mpls_label_status": "ACTIVE" if d["type"] == "Hub" else None,
                
                # Telemetry stats
                "rx_bandwidth": 35.0 + random.uniform(0, 10),
                "tx_bandwidth": 30.0 + random.uniform(0, 10),
                "latency": 15.0 + random.uniform(0, 5) if d["id"] != "DC-Bangalore" else 1.0,
                "jitter": 1.5 + random.uniform(0, 1) if d["id"] != "DC-Bangalore" else 0.1,
                "packet_loss": 0.01 + random.uniform(0, 0.02) if d["id"] != "DC-Bangalore" else 0.0,
                "tunnel_health": 100.0,
                "interface_errors": 0,
                "link_availability": 1.0
            }

    def seed_database(self, db: Session):
        """Insert default devices into SQLite if empty."""
        for d in DEVICE_DEFS:
            existing = db.query(Device).filter(Device.id == d["id"]).first()
            if not existing:
                state = self.device_states[d["id"]]
                db_device = Device(
                    id=d["id"],
                    name=d["name"],
                    type=d["type"],
                    ip_address=d["ip"],
                    status="healthy",
                    cpu_usage=state["cpu_usage"],
                    memory_usage=state["memory_usage"],
                    bgp_state=state["bgp_state"],
                    ospf_state=state["ospf_state"],
                    mpls_label_status=state["mpls_label_status"]
                )
                db.add(db_device)
        db.commit()

    def stochastic_walk(self, val: float, min_val: float, max_val: float, mu: float = 0.0, sigma: float = 1.0) -> float:
        """Stochastic random walk helper."""
        change = random.normalvariate(mu, sigma)
        new_val = val + change
        return max(min_val, min(max_val, new_val))

    def update_simulation_states(self, db: Session):
        """Update metrics for one simulation tick (1 second)."""
        time_now = datetime.now()
        
        # Dynamic updates to BGP state machine if BGP FLAP anomaly is active
        if self.active_anomaly == "BGP_FLAP":
            self.bgp_flap_timer += 1
            if self.bgp_flap_timer >= 6:
                self.bgp_flap_timer = 0
                self.bgp_flap_state = not self.bgp_flap_state
                state_str = "ESTABLISHED" if self.bgp_flap_state else "ACTIVE"
                
                # Mumbai Hub flaps BGP session
                self.device_states["HUB-Mumbai"]["bgp_state"] = state_str
                
                # Insert Syslogs
                severity = "INFO" if self.bgp_flap_state else "WARNING"
                syslog = SyslogEvent(
                    timestamp=time_now,
                    device_id="HUB-Mumbai",
                    severity=severity,
                    protocol="BGP",
                    message=f"BGP Peering Session state transition to {state_str}"
                )
                db.add(syslog)
                
                # Add alert on route flap
                if not self.bgp_flap_state:
                    alert = Alert(
                        id=f"ALT-BGP-{uuid.uuid4().hex[:6]}",
                        timestamp=time_now,
                        device_id="HUB-Mumbai",
                        severity="warning",
                        title="BGP Session State Instability",
                        description="BGP session transitioning active to idle. Frequent route advertisements.",
                        confidence=0.92,
                        likely_cause="Peering session flapping or misconfigured hold-timers.",
                        affected_services="Mumbai aggregate transit links",
                        status="active"
                    )
                    db.add(alert)

        for dev_id, state in self.device_states.items():
            # Stochastic defaults
            mu_cpu = 0.0
            sigma_cpu = 1.0
            
            # Basic defaults
            if dev_id != "DC-Bangalore":
                target_lat_min, target_lat_max = 12.0, 35.0
                target_loss_min, target_loss_max = 0.0, 0.05
                target_thr_min, target_thr_max = 30.0, 75.0
                mu_lat, sigma_lat = 0.0, 1.0
                mu_loss, sigma_loss = 0.0, 0.01
                mu_thr, sigma_thr = 0.0, 2.0
            else:
                target_lat_min, target_lat_max = 0.5, 2.0
                target_loss_min, target_loss_max = 0.0, 0.0
                target_thr_min, target_thr_max = 100.0, 250.0
                mu_lat, sigma_lat = 0.0, 0.1
                mu_loss, sigma_loss = 0.0, 0.0
                mu_thr, sigma_thr = 0.0, 5.0

            # ----------------------------------------------------
            # Apply Fault Injection Anomaly Drifts
            # ----------------------------------------------------
            if self.active_anomaly == "CONGESTION_BR3" and dev_id == "BR-Chennai":
                # Spikes Chennai bandwidth, CPU, and packet loss
                mu_cpu = 4.0
                mu_thr = 15.0
                mu_lat = 10.0
                mu_loss = 0.5
                target_lat_max = 120.0
                target_loss_max = 8.5
                target_thr_max = 196.0 # Max capacity is 200 Mbps
                state["status"] = "critical"
                
            elif self.active_anomaly == "TUNNEL_BR1_DOWN" and dev_id == "BR-Delhi":
                # Sever Delhi tunnel
                state["tunnel_health"] = max(0.0, state["tunnel_health"] - 25.0)
                state["link_availability"] = 0.0
                state["packet_loss"] = 100.0
                state["latency"] = 999.0
                state["rx_bandwidth"] = 0.0
                state["tx_bandwidth"] = 0.0
                state["status"] = "critical"
                state["bgp_state"] = "DOWN"
                
            elif self.active_anomaly == "ROUTING_LOOP_HUB" and dev_id == "HUB-Mumbai":
                # Spikes CPU on Hub-Mumbai and routing latencies globally
                mu_cpu = 15.0
                mu_lat = 35.0
                target_lat_max = 285.0
                state["status"] = "critical"
                state["ospf_state"] = "DOWN"
                
            elif self.active_anomaly == "IPSEC_DEGRADED" and dev_id == "BR-Delhi":
                # High loss/jitter on Delhi
                mu_loss = 1.2
                target_loss_max = 15.4
                state["jitter"] = self.stochastic_walk(state["jitter"], 2.0, 45.0, mu=3.0, sigma=2.0)
                state["tunnel_health"] = max(20.0, state["tunnel_health"] - 10.0)
                state["status"] = "warning"
                
            elif self.active_anomaly == "CONFIG_DRIFT" and dev_id == "BR-Kolkata":
                # Increment interface errors
                state["interface_errors"] += random.randint(5, 20)
                state["status"] = "warning"
                
            elif self.active_anomaly == "INTERFACE_FAIL" and dev_id == "BR-Hyderabad":
                # Hyderbad link down
                state["link_availability"] = 0.0
                state["rx_bandwidth"] = 0.0
                state["tx_bandwidth"] = 0.0
                state["status"] = "critical"
                state["interface_errors"] += random.randint(1, 3)

            # ----------------------------------------------------
            # Apply Stochastic updates
            # ----------------------------------------------------
            state["cpu_usage"] = self.stochastic_walk(state["cpu_usage"], 5.0, 98.0, mu=mu_cpu, sigma=sigma_cpu)
            state["memory_usage"] = self.stochastic_walk(state["memory_usage"], 25.0, 95.0, mu=0.0, sigma=0.5)
            
            if state["link_availability"] > 0:
                state["rx_bandwidth"] = self.stochastic_walk(state["rx_bandwidth"], 5.0, target_thr_max, mu=mu_thr, sigma=sigma_thr)
                state["tx_bandwidth"] = self.stochastic_walk(state["tx_bandwidth"], 5.0, target_thr_max, mu=mu_thr, sigma=sigma_thr)
                state["latency"] = self.stochastic_walk(state["latency"], 1.0, target_lat_max, mu=mu_lat, sigma=sigma_lat)
                state["packet_loss"] = self.stochastic_walk(state["packet_loss"], 0.0, target_loss_max, mu=mu_loss, sigma=sigma_loss)

            # Auto-recovering attributes back to baseline if recovery triggered
            if not self.active_anomaly:
                state["status"] = "healthy"
                state["link_availability"] = 1.0
                state["tunnel_health"] = min(100.0, state["tunnel_health"] + 20.0)
                if state["bgp_state"] == "DOWN":
                    state["bgp_state"] = "ESTABLISHED"
                if state["ospf_state"] == "DOWN" and dev_id in ["DC-Bangalore", "HUB-Mumbai"]:
                    state["ospf_state"] = "FULL"

            # Sync active state values to SQLite Device objects
            db_device = db.query(Device).filter(Device.id == dev_id).first()
            if db_device:
                db_device.cpu_usage = state["cpu_usage"]
                db_device.memory_usage = state["memory_usage"]
                db_device.status = state["status"]
                db_device.bgp_state = state["bgp_state"]
                db_device.ospf_state = state["ospf_state"]
                db_device.mpls_label_status = state["mpls_label_status"]

            # Save historical timeseries metrics
            telemetry = TelemetryHistory(
                timestamp=time_now,
                device_id=dev_id,
                cpu_usage=state["cpu_usage"],
                memory_usage=state["memory_usage"],
                rx_bandwidth=state["rx_bandwidth"],
                tx_bandwidth=state["tx_bandwidth"],
                latency=state["latency"],
                jitter=state["jitter"],
                packet_loss=state["packet_loss"],
                tunnel_health=state["tunnel_health"],
                interface_errors=state["interface_errors"],
                link_availability=state["link_availability"]
            )
            db.add(telemetry)

        # Generate some synthetic NetFlow flow statistics
        self.generate_netflow_stats(db, time_now)

        db.commit()

    def generate_netflow_stats(self, db: Session, timestamp: datetime):
        """Simulate random active socket TCP/UDP NetFlow distributions."""
        for _ in range(random.randint(1, 3)):
            src = random.choice(DEVICE_DEFS)["ip"]
            dst = random.choice(DEVICE_DEFS)["ip"]
            if src == dst:
                continue
            
            bytes_val = random.randint(1500, 250000)
            if self.active_anomaly == "CONGESTION_BR3":
                # High traffic flows from Chennai
                src = "10.30.3.1"
                bytes_val = random.randint(850000, 1500000)

            flow = NetflowRecord(
                timestamp=timestamp,
                src_ip=src,
                dst_ip=dst,
                src_port=random.randint(1024, 65535),
                dst_port=random.choice([80, 443, 22, 4500, 500]),
                protocol=random.choice(["TCP", "UDP", "ICMP"]),
                bytes=bytes_val,
                packets=max(1, bytes_val // 1400)
            )
            db.add(flow)

    def inject_fault(self, scenario: str, db: Session):
        """Triggers specific anomaly injection parameters."""
        self.active_anomaly = scenario
        time_now = datetime.now()
        
        # Flush active alerts list and start new alerts
        alert_id = f"ALT-{scenario}-{uuid.uuid4().hex[:6]}"
        
        severity = "critical"
        title = "Diagnostic Alert"
        desc = "Anomaly condition"
        cause = "Trigger event"
        services = "Secondary tunnels"
        confidence = 0.95
        
        if scenario == "CONGESTION_BR3":
            title = "SD-WAN Overlay Bandwidth Congestion Warning"
            desc = "Throughput usage crossed 90% SLA limits on BR-Chennai tunnel to Hub-Mumbai."
            cause = "Volume threshold overrun. Suspected large sync replication task."
            services = "Chennai local subnet, VoIP services"
            confidence = 0.96
            
        elif scenario == "TUNNEL_BR1_DOWN":
            severity = "emergency"
            title = "IPSec Overlay Tunnel Negotiation Failure"
            desc = "Delhi Branch IPSec secure association failed. Neighbor OSPF adjacency down."
            cause = "Phase 1 Main Mode negotiation timeout. Link interface degradation."
            services = "Delhi domain controller replication, intra-site file transfer"
            confidence = 0.99
            
        elif scenario == "ROUTING_LOOP_HUB":
            severity = "emergency"
            title = "OSPF Routing Loop & Transit CPU Alert"
            desc = "Routing loop detected between DC-Bangalore and HUB-Mumbai. Aggressive traffic bounce."
            cause = "Mismatched dynamic OSPF path cost metrics."
            services = "All WAN branches transit packets"
            confidence = 0.91
            
        elif scenario == "IPSEC_DEGRADED":
            severity = "warning"
            title = "IPSec Overlay Performance Loss / Jitter Spike"
            desc = "Delhi tunnel experiencing 15.4% drop rates and 45ms latency jitter."
            cause = "High interface CRC error rates, network degradation."
            services = "Delhi real-time VoIP queues"
            confidence = 0.93
            
        elif scenario == "CONFIG_DRIFT":
            severity = "warning"
            title = "Kolkata Interface Configuration Drift"
            desc = "Kolkata Branch router interface MTU mismatch. Packet fragmentation drops rising."
            cause = "VLAN tag or MTU costing error drift."
            services = "Kolkata ERP application syncs"
            confidence = 0.88
            
        elif scenario == "INTERFACE_FAIL":
            severity = "critical"
            title = "Hyderabad Link Interface Failure"
            desc = "GigabitEthernet0/1 link is DOWN on Hyderabad branch."
            cause = "Port transceiver hardware error or cable disconnect."
            services = "Hyderabad Branch aggregate traffic"
            confidence = 0.98

        alert = Alert(
            id=alert_id,
            timestamp=time_now,
            device_id= "HUB-Mumbai" if scenario == "ROUTING_LOOP_HUB" else ("BR-Chennai" if "BR3" in scenario else ("BR-Delhi" if "BR1" in scenario or "DEGRADED" in scenario else "BR-Kolkata" if "CONFIG" in scenario else "BR-Hyderabad")),
            severity=severity,
            title=title,
            description=desc,
            confidence=confidence,
            likely_cause=cause,
            affected_services=services,
            status="active"
        )
        db.add(alert)
        
        # Log syslog
        syslog = SyslogEvent(
            timestamp=time_now,
            device_id=alert.device_id,
            severity=severity.upper(),
            protocol="SYS",
            message=f"CRITICAL ANOMALY INJECTED: {scenario}. {desc}"
        )
        db.add(syslog)
        db.commit()
        
    def recover_network(self, db: Session):
        """Clears anomalies and updates statuses back to baseline."""
        self.active_anomaly = None
        time_now = datetime.now()
        
        # Mark active alerts resolved
        db.query(Alert).filter(Alert.status == "active").update({"status": "resolved"})
        
        # Add success syslog log
        log = SyslogEvent(
            timestamp=time_now,
            device_id="HUB-Mumbai",
            severity="INFO",
            protocol="SYS",
            message="Autonomic self-healing actions finalized. All interfaces active."
        )
        db.add(log)
        db.commit()

    async def broadcast_loop(self):
        """Async daemon loop that publishes telemetry frames over WS every second."""
        while True:
            if self.is_running:
                db = SessionLocal()
                try:
                    self.update_simulation_states(db)
                    
                    # Package broadcast payload
                    devices_list = []
                    for dev_id, state in self.device_states.items():
                        devices_list.append({
                            "id": state["id"],
                            "name": state["name"],
                            "type": state["type"],
                            "ip_address": state["ip_address"],
                            "status": state["status"],
                            "cpu_usage": state["cpu_usage"],
                            "memory_usage": state["memory_usage"],
                            "bgp_state": state["bgp_state"],
                            "ospf_state": state["ospf_state"],
                            "mpls_label_status": state["mpls_label_status"],
                            "rx_bandwidth": state["rx_bandwidth"],
                            "tx_bandwidth": state["tx_bandwidth"],
                            "latency": state["latency"],
                            "packet_loss": state["packet_loss"],
                            "jitter": state["jitter"],
                            "tunnel_health": state["tunnel_health"],
                            "interface_errors": state["interface_errors"],
                            "link_availability": state["link_availability"],
                            "last_updated": datetime.now().isoformat()
                        })
                        
                    # Run predictive engine updates and save prediction logs
                    predictions_list = predictive_engine.run_predictions_pass(db)

                    active_alerts = db.query(Alert).filter(Alert.status == "active").all()
                    alerts_list = [{
                        "id": a.id,
                        "timestamp": a.timestamp.isoformat(),
                        "device_id": a.device_id,
                        "severity": a.severity,
                        "title": a.title,
                        "description": a.description,
                        "confidence": a.confidence,
                        "likely_cause": a.likely_cause,
                        "affected_services": a.affected_services,
                        "status": a.status
                    } for a in active_alerts]
                    
                    recent_logs = db.query(SyslogEvent).order_by(SyslogEvent.timestamp.desc()).limit(15).all()
                    logs_list = [{
                        "timestamp": lg.timestamp.isoformat(),
                        "device_id": lg.device_id,
                        "severity": lg.severity,
                        "protocol": lg.protocol,
                        "message": lg.message
                    } for lg in recent_logs]

                    # Phase 4 AIOps Integrations
                    correlation_results = event_correlation_engine.correlate_incidents(db)
                    if correlation_results:
                        primary_inc = correlation_results[0]
                        dev_id = primary_inc["device_id"]
                        
                        # Identify failure type from alert
                        primary_alt = db.query(Alert).filter(Alert.id == primary_inc["primary_alert_id"]).first()
                        fail_type = "None"
                        if primary_alt:
                            if "Congestion" in primary_alt.title:
                                fail_type = "Congestion"
                            elif "Tunnel" in primary_alt.title:
                                fail_type = "IPSec Tunnel Failure"
                            elif "Loop" in primary_alt.title:
                                fail_type = "Routing Loop"
                            elif "Drift" in primary_alt.title:
                                fail_type = "Configuration Drift"
                            elif "Link" in primary_alt.title or "Failure" in primary_alt.title:
                                fail_type = "Interface Failure"
                            elif "BGP" in primary_alt.title or "Flap" in primary_alt.title:
                                fail_type = "BGP Route Flap"

                        rca_res = root_cause_engine.analyze_root_cause(dev_id, fail_type, db)
                        decision_res = decision_engine.generate_decision(dev_id, fail_type, db)
                        timeline_res = incident_timeline_engine.generate_timeline(dev_id, fail_type, db)
                    else:
                        rca_res = {
                            "primary_root_cause": "No issues active.",
                            "supporting_evidence": [],
                            "confidence_score": 1.0,
                            "contributing_signals": [],
                            "dependency_chain": []
                        }
                        decision_res = {
                            "incident_summary": "All network interfaces healthy.",
                            "recommended_action": "Maintain monitoring protocol.",
                            "recovery_priority": "P3 (Standard Monitor)",
                            "estimated_recovery_time": "N/A",
                            "risk_assessment": "Nominal risks.",
                            "preventive_recommendation": "Configure standard audit checks.",
                            "alternative_network_path": "All primary paths active.",
                            "decision_confidence": 1.0,
                            "confidence_breakdown": {
                                "telemetry_quality": 0.99,
                                "prediction_confidence": 1.0,
                                "graph_confidence": 0.95,
                                "historical_match": 0.0
                            },
                            "business_impact": {
                                "affected_branches": [],
                                "affected_devices": [],
                                "affected_services": [],
                                "estimated_users_impacted": 0,
                                "mission_criticality": 0.0,
                                "sla_impact": 0.0,
                                "estimated_downtime_minutes": 0,
                                "operational_severity": "LOW"
                            },
                            "blast_radius_analysis": {
                                "blast_radius_percent": 0.0,
                                "immediate_impact": "None. Network operating normally.",
                                "upstream_impact": "None.",
                                "downstream_impact": "None.",
                                "critical_dependencies": [],
                                "is_spof": False,
                                "service_propagation_path": "N/A"
                            },
                            "playbook": {
                                "playbook_id": "PB_NONE",
                                "playbook_name": "Standard Monitoring Policy",
                                "remediation_steps": ["Maintain baseline monitoring."],
                                "confidence": 1.0,
                                "estimated_execution_time_seconds": 0,
                                "expected_improvement": "Normal baseline operations maintained.",
                                "risk_if_ignored": "None"
                            },
                            "historical_match": None
                        }
                        timeline_res = incident_timeline_engine.generate_timeline("None", "None", db)

                    payload = {
                        "timestamp": datetime.now().isoformat(),
                        "devices": devices_list,
                        "alerts": alerts_list,
                        "logs": logs_list,
                        "active_anomaly": self.active_anomaly,
                        "predictions": predictions_list,
                        # Phase 4 AIOps Data
                        "correlation_results": correlation_results,
                        "root_cause": rca_res,
                        "decision_summary": decision_res,
                        "incident_timeline": timeline_res,
                        "blast_radius": decision_res["blast_radius_analysis"],
                        "business_impact": decision_res["business_impact"],
                        "recommended_playbook": decision_res["playbook"]
                    }


                    # Broadcast payload to all open WebSockets
                    if self.active_websockets:
                        tasks = []
                        for ws in list(self.active_websockets):
                            try:
                                tasks.append(ws.send_json(payload))
                            except Exception:
                                self.active_websockets.discard(ws)
                        if tasks:
                            await asyncio.gather(*tasks, return_exceptions=True)
                except Exception as e:
                    print(f"Error in simulation loop: {e}")
                finally:
                    db.close()
                    
            await asyncio.sleep(settings.TELEMETRY_INTERVAL_SECONDS)

# Singleton Instance
simulator = NetworkSimulator()
