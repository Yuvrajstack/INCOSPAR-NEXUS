# Standard Runbook: Adaptive QoS Bandwidth Congestion Remediation

## Symptom Signatures
- Egress queue load utilization exceeds 85% bandwidth capacity.
- Real-time applications experience packet loss (>1.0%) and high latency (>100ms).
- SNMP statistics flags high TCP retransmission rates on physical WAN interfaces.

## Diagnosis Workflow
1. Check the egress interface bandwidth statistics on the branch router.
2. Verify QoS class allocation queues: check if default/bulk traffic is consuming priority queues.
3. Inspect whether central data synchronization tasks (e.g. backup replications) are active.

## Resolution Remediation Steps
1. Establish secure console/SSH session to the affected branch router.
2. Adjust policy-map default traffic parameters to limit bulk bandwidth to 80-85% capacity.
3. Configure Priority Queue Class 1 scheduler specifically for real-time VoIP packets.
4. Apply the configured policy-map to the WAN interface in the outbound direction.
