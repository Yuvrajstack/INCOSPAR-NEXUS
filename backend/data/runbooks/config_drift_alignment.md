# Standard Runbook: Configuration Drift & MTU Parameter Alignment

## Symptom Signatures
- Interfaces log incrementing CRC errors and alignment packet drops.
- Network throughput drops with high fragmentation requests.
- System logs report MTU configuration mismatch warnings.

## Diagnosis Workflow
1. Retrieve router config status parameters: inspect configuration logs.
2. Compare running configuration parameters with golden master files.
3. Check the maximum transmission unit (MTU) size parameters across peer interfaces.

## Resolution Remediation Steps
1. Log in to the branch router CLI.
2. Align MTU configurations: `interface gig0/2; ip mtu 1500; mtu 1500`.
3. Check the interface errors counter and confirm drops stabilize to 0.
4. Verify config compliance audit scores return to normal boundaries.
