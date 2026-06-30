# Standard Runbook: IPSec Tunnel Rekeying & Routing Convergence

## Symptom Signatures
- IPSec overlay VPN tunnel health reports DOWN (availability: 0%).
- Link availability is 0 on WAN interfaces.
- Dynamic routing neighbors (OSPF Hello state) transition to DOWN/INIT.

## Diagnosis Workflow
1. Run local diagnostic `show crypto ipsec sa` to identify active security associations.
2. Confirm if ISAKMP Phase 1 exchange handshake times out.
3. Validate keepalive peer reachability.

## Resolution Remediation Steps
1. Log in to the branch router CLI.
2. Flush dynamic cryptographic associations: `clear crypto ipsec sa`.
3. Flush and restart the internet key exchange daemon: `clear crypto isakmp`.
4. Trigger manual ISAKMP Phase 1 negotiations.
5. Monitor logs to verify OSPF neighbour state transitions back to FULL.
