from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # 'DC', 'Hub', 'Branch'
    ip_address = Column(String, nullable=False)
    status = Column(String, nullable=False, default="healthy") # 'healthy', 'warning', 'critical'
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    bgp_state = Column(String, nullable=True) # 'ESTABLISHED', 'ACTIVE', 'IDLE', 'DOWN'
    ospf_state = Column(String, nullable=True) # 'FULL', '2-WAY', 'INIT', 'DOWN'
    mpls_label_status = Column(String, nullable=True) # 'ACTIVE', 'SWAPPED', 'DOWN'
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

class TelemetryHistory(Base):
    __tablename__ = "telemetry_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False)
    cpu_usage = Column(Float, nullable=False)
    memory_usage = Column(Float, nullable=False)
    rx_bandwidth = Column(Float, nullable=False) # In Mbps
    tx_bandwidth = Column(Float, nullable=False) # In Mbps
    latency = Column(Float, nullable=False) # In ms
    jitter = Column(Float, nullable=False) # In ms
    packet_loss = Column(Float, nullable=False) # In %
    tunnel_health = Column(Float, nullable=False) # In % (0 - 100)
    interface_errors = Column(Integer, default=0)
    link_availability = Column(Float, default=1.0) # 0.0 or 1.0

class NetflowRecord(Base):
    __tablename__ = "netflow_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    src_ip = Column(String, nullable=False)
    dst_ip = Column(String, nullable=False)
    src_port = Column(Integer, nullable=True)
    dst_port = Column(Integer, nullable=True)
    protocol = Column(String, nullable=False) # 'TCP', 'UDP', 'ICMP'
    bytes = Column(Integer, nullable=False)
    packets = Column(Integer, nullable=False)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False)
    severity = Column(String, nullable=False) # 'info', 'warning', 'critical', 'emergency'
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    likely_cause = Column(String, nullable=False)
    affected_services = Column(String, nullable=False) # Comma-separated list
    status = Column(String, nullable=False, default="active") # 'active', 'resolved'

class SyslogEvent(Base):
    __tablename__ = "syslog_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    device_id = Column(String, ForeignKey("devices.id"), nullable=False)
    severity = Column(String, nullable=False) # 'INFO', 'WARNING', 'CRITICAL', 'EMERGENCY'
    protocol = Column(String, nullable=True) # 'BGP', 'OSPF', 'IPSec', 'MPLS', 'SYS'
    message = Column(String, nullable=False)

class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    device_id = Column(String, ForeignKey("devices.id"), nullable=False, index=True)
    model_version = Column(String, nullable=False)
    failure_probability = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    confidence_history_json = Column(String, nullable=False)
    prediction_trend = Column(String, nullable=False) # 'UP', 'DOWN', 'STABLE'
    prediction_status = Column(String, nullable=False) # 'NORMAL', 'WATCH', 'WARNING', 'CRITICAL'
    predicted_failure_type = Column(String, nullable=False)
    root_cause_signals_json = Column(String, nullable=False)
    contributing_metrics_json = Column(String, nullable=False)
    recommended_action = Column(String, nullable=False)
    business_impact_json = Column(String, nullable=False)
    blast_radius = Column(Float, nullable=False)
    mission_criticality = Column(Float, nullable=False)
