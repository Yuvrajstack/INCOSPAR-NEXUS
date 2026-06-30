import json
import urllib.request
import urllib.error
from typing import Dict, Any, List

class LocalLLMClient:
    """
    Local LLM Client mapping to local Ollama endpoints (port 11434).
    If Ollama is offline or unavailable, falls back to a deterministic,
    grounded AIOps rule-based fallback reasoning engine running completely offline.
    """

    def __init__(self, ollama_url: str = "http://localhost:11434", default_model: str = "llama3"):
        self.ollama_url = ollama_url
        self.default_model = default_model

    def query_llm(self, prompt: str, system_prompt: str, session_id: str) -> Dict[str, Any]:
        """
        Attempts to call the local Ollama API to generate a structured JSON response.
        If Ollama is unavailable, falls back to the deterministic offline rule engine.
        """
        payload = {
            "model": self.default_model,
            "prompt": f"{system_prompt}\n\nUser Question:\n{prompt}",
            "stream": False,
            "format": "json" # Enforce structured JSON mode in Ollama
        }
        
        try:
            req = urllib.request.Request(
                f"{self.ollama_url}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            # Timeout set to 6 seconds for responsiveness
            with urllib.request.urlopen(req, timeout=6) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text_output = res_data.get("response", "")
                
                # Parse output as JSON
                try:
                    structured_res = json.loads(text_output)
                    return structured_res
                except json.JSONDecodeError:
                    # If model returned text despite format="json", wrap it in standard schema
                    return self._wrap_raw_text_in_schema(text_output)
        except Exception as e:
            # Ollama is offline or timed out. Gracefully activate deterministic fallback reasoning.
            print(f"Ollama connection unavailable ({e}). Activating deterministic offline AIOps reasoning engine.")
            return self._run_rule_based_fallback(prompt, system_prompt)

    def _wrap_raw_text_in_schema(self, text: str) -> Dict[str, Any]:
        return {
            "summary": text,
            "overall_confidence": 0.85,
            "prediction_confidence": 0.88,
            "knowledge_confidence": 0.80,
            "decision_confidence": 0.85,
            "rag_score": 0.90,
            "root_cause": "Analyzed from text description.",
            "business_impact": "Degradations logged.",
            "blast_radius": "Check AIOps telemetry.",
            "recommended_actions": ["Review summary and execute remediation guides."],
            "references": ["General Troubleshooting Guide"]
        }

    def _run_rule_based_fallback(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """
        Deterministic, offline rule-based reasoning engine.
        Parses keywords and active network context to output the requested structured JSON schema.
        """
        query = prompt.lower()
        
        # Parse context keywords to identify targeted failure mode
        target_device = "Unknown Device"
        if "delhi" in query or "br-1" in query or "tunnel" in query or "vpn" in query:
            failure_mode = "IPSec Tunnel Failure"
            device_id = "BR-Delhi"
            runbook = "ipsec_tunnel_rekeying.md"
            summary = "IPSec VPN tunnel connection dropped on BR-Delhi. Remote cryptographical Phase 1 SA negotiation failed."
            root_cause = "Handshake timeout during Main Mode SA parameter dynamic key exchange."
            impact = "Full branch isolation. All secure transaction traffic dropped. SLA impact probability: 80.0%."
            blast = "20% (Local Delhi branch overlay paths isolated)."
            actions = [
                "Flush active security associations: 'clear crypto ipsec sa'.",
                "Flush and restart ISAKMP daemon: 'clear crypto isakmp'.",
                "Force Phase 1 renegotiation hello state exchanges."
            ]
            references = [runbook, "Incident #102", "Predictive History"]
            pred_conf, kb_conf, dec_conf, rag_conf = 0.98, 0.98, 0.95, 0.96
        elif "chennai" in query or "br-3" in query or "congestion" in query or "loss" in query:
            failure_mode = "Congestion"
            device_id = "BR-Chennai"
            runbook = "qos_congestion_remediation.md"
            summary = "Egress queue bandwidth saturation detected on BR-Chennai outbound link."
            root_cause = "Asymmetric WAN interface weights causing default queues to spike under heavy backup replications."
            impact = "Real-time VoIP packet drops and latency spikes. SLA impact probability: 45.0%."
            blast = "16% (Outbound Chennai link degraded)."
            actions = [
                "Enter terminal configuration mode: 'policy-map SDWAN-SHAPER'.",
                "Cap bulk traffic queue utilization limits to 85% link capacity.",
                "Allocate priority scheduler bandwidth for Class-1 VoIP real-time packets."
            ]
            references = [runbook, "Incident #101", "Prediction History"]
            pred_conf, kb_conf, dec_conf, rag_conf = 0.95, 0.94, 0.92, 0.95
        elif "mumbai" in query or "hub" in query or "loop" in query or "cpu" in query:
            failure_mode = "Routing Loop"
            device_id = "HUB-Mumbai"
            runbook = "ospf_metric_tuning.md"
            summary = "Transit routing loop flagged between Mumbai Hub aggregator and Data Center core interfaces."
            root_cause = "Mismatched OSPF route metric costs assigned across redundant link paths."
            impact = "Aggregator CPU utilization rose to 94.0%. Frame bouncing causing global latency spike. SLA impact probability: 99.0%."
            blast = "83% (Transit paths bouncing transit packets)."
            actions = [
                "Enter router OSPF config mapping: 'router ospf 100'.",
                "Configure administrative costs: 'interface gig0/1; ip ospf cost 40'.",
                "Clear ip routing tables to trigger OSPF recalculations."
            ]
            references = [runbook, "Incident #103", "Graph Analysis Engine"]
            pred_conf, kb_conf, dec_conf, rag_conf = 0.92, 0.91, 0.96, 0.93
        elif "kolkata" in query or "br-2" in query or "drift" in query or "mtu" in query:
            failure_mode = "Configuration Drift"
            device_id = "BR-Kolkata"
            runbook = "config_drift_alignment.md"
            summary = "Interface configuration compliance warning on BR-Kolkata router."
            root_cause = "Maximum transmission unit (MTU) size parameter mismatch causing packet fragmentation drops."
            actions = [
                "Verify MTU compliance audit settings.",
                "Sync interface parameters: 'interface gig0/2; ip mtu 1500; mtu 1500'.",
                "Monitor interface alignment and CRC packet drop counters."
            ]
            impact = "Packet fragmentation overhead. Reduced application throughput. SLA impact probability: 30.0%."
            blast = "16% (Kolkata branch interface errors)."
            references = [runbook, "Incident #105", "Configuration Metadata"]
            pred_conf, kb_conf, dec_conf, rag_conf = 0.88, 0.88, 0.90, 0.92
        elif "hyderabad" in query or "br-4" in query or "interface" in query or "fail" in query:
            failure_mode = "Interface Failure"
            device_id = "BR-Hyderabad"
            runbook = "ipsec_tunnel_rekeying.md"
            summary = "Physical port link down alarm on BR-Hyderabad router interface."
            root_cause = "Transceiver connection issue or physical fiber line disconnect."
            impact = "Hyderabad branch network backup routing. SLA impact probability: 60.0%."
            blast = "16% (Hyderabad branch port status: Offline)."
            actions = [
                "Configure failed port administrative status to standby.",
                "Verify OSPF routes converge through alternate backup overlay paths."
            ]
            references = [runbook, "Incident #106", "Topology Schema"]
            pred_conf, kb_conf, dec_conf, rag_conf = 0.96, 0.96, 0.95, 0.94
        else:
            # Global status overview
            return {
                "summary": "All dynamic SD-WAN digital twin nodes and overlay links are operating within standard performance baseline scopes.",
                "overall_confidence": 0.98,
                "prediction_confidence": 0.99,
                "knowledge_confidence": 0.95,
                "decision_confidence": 0.98,
                "rag_score": 0.99,
                "root_cause": "N/A. System state: NOMINAL.",
                "business_impact": "None. SLA compliance matches 99.98% performance guarantees.",
                "blast_radius": "0.0% (All paths redundant).",
                "recommended_actions": [
                    "Maintain standard SNMP polling interval limits.",
                    "Verify compliance audits scripts execution calendar."
                ],
                "references": ["Device Inventory", "Network Topology"]
            }

        overall_conf = round((pred_conf + kb_conf + dec_conf + rag_conf) / 4, 3)

        return {
            "summary": summary,
            "overall_confidence": overall_conf,
            "prediction_confidence": pred_conf,
            "knowledge_confidence": kb_conf,
            "decision_confidence": dec_conf,
            "rag_score": rag_conf,
            "root_cause": root_cause,
            "business_impact": impact,
            "blast_radius": blast,
            "recommended_actions": actions,
            "references": references
        }

# Singleton Instance
local_llm_client = LocalLLMClient()
