from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class DeviceBase(BaseModel):
    id: str
    name: str
    type: str
    ip_address: str
    status: str
    cpu_usage: float
    memory_usage: float
    bgp_state: Optional[str] = None
    ospf_state: Optional[str] = None
    mpls_label_status: Optional[str] = None

class DeviceCreate(DeviceBase):
    pass

class DeviceSchema(DeviceBase):
    last_updated: datetime

    class Config:
        from_attributes = True

class TelemetryHistoryBase(BaseModel):
    timestamp: datetime
    device_id: str
    cpu_usage: float
    memory_usage: float
    rx_bandwidth: float
    tx_bandwidth: float
    latency: float
    jitter: float
    packet_loss: float
    tunnel_health: float
    interface_errors: int
    link_availability: float

class TelemetryHistorySchema(TelemetryHistoryBase):
    id: int

    class Config:
        from_attributes = True

class NetflowRecordBase(BaseModel):
    timestamp: datetime
    src_ip: str
    dst_ip: str
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    protocol: str
    bytes: int
    packets: int

class NetflowRecordSchema(NetflowRecordBase):
    id: int

    class Config:
        from_attributes = True

class AlertBase(BaseModel):
    id: str
    timestamp: datetime
    device_id: str
    severity: str
    title: str
    description: str
    confidence: float
    likely_cause: str
    affected_services: str
    status: str

class AlertSchema(AlertBase):
    class Config:
        from_attributes = True

class SyslogEventBase(BaseModel):
    timestamp: datetime
    device_id: str
    severity: str
    protocol: Optional[str] = None
    message: str

class SyslogEventSchema(SyslogEventBase):
    id: int

    class Config:
        from_attributes = True

class FaultInjectionRequest(BaseModel):
    scenario: str # 'CONGESTION_BR3', 'BGP_FLAP', 'OSPF_FAIL', 'MPLS_FAIL', 'IPSEC_DEGRADED', 'CONFIG_DRIFT', 'INTERFACE_FAIL'

class LiveTelemetryStreamFrame(BaseModel):
    devices: List[DeviceSchema]
    alerts: List[AlertSchema]
    syslog: List[SyslogEventSchema]
