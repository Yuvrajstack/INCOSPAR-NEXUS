# Standard Runbook: Dynamic OSPF Routing Loop Remediation

## Symptom Signatures
- Hub transit aggregator routers CPU spikes to high levels (>80%).
- Average transit path latency rises from normal baselines to >250ms.
- Packets bounce between parallel transit paths (route loop behavior).

## Diagnosis Workflow
1. Check OSPF route cost matrix tables on aggregator and DC core routers.
2. Search route costs: identify equal-cost paths mapped to asymmetric links.
3. Validate routing table entries for target subnets.

## Resolution Remediation Steps
1. Log in to the loop transit aggregator router.
2. Edit OSPF cost metrics under interface: `router ospf 100; interface gig0/1; ip ospf cost 40`.
3. Flush dynamic routing tables to trigger SPF algorithm recalculations.
4. Verify routing paths converge, CPU load drops, and latencies normalize.
