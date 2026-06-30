import http.client
import json
import time

def test_phase4_endpoints():
    print("==================================================")
    print("   SENTINELNET AI PHASE 4 API VERIFICATION TEST   ")
    print("==================================================")
    
    conn = http.client.HTTPConnection("127.0.0.1", 8000)
    headers = {'Content-type': 'application/json'}

    # Helper helper to make HTTP requests
    def get_route(url):
        conn.request("GET", url)
        res = conn.getresponse()
        data = res.read().decode()
        return res.status, json.loads(data)

    def post_route(url, body):
        conn.request("POST", url, json.dumps(body), headers)
        res = conn.getresponse()
        data = res.read().decode()
        return res.status, json.loads(data)

    # Injecting Anomaly to trigger Decision logic
    print("\nInjecting failure scenario (TUNNEL_BR1_DOWN)...")
    post_route("/inject-fault", {"scenario": "TUNNEL_BR1_DOWN"})
    time.sleep(2) # Allow simulation tick to update DB and run engine pass

    print("\n1. Testing GET /correlation...")
    status, res = get_route("/correlation")
    print(f"Status: {status}")
    print(f"Result count: {len(res)}")
    if res:
        print(f"Clustered Incident: {res[0]['title']} (Confidence: {res[0]['correlation_confidence']})")
        print(f"Cascading sequence chain: {res[0]['cascade_chain']}")

    print("\n2. Testing GET /incident...")
    status, res = get_route("/incident")
    print(f"Status: {status}")
    print(f"Incident Status: {res.get('status')}")
    if "root_cause" in res:
        print(f"RCA Primary Cause: {res['root_cause']['primary_root_cause']}")
        print(f"RCA Confidence Score: {res['root_cause']['confidence_score']}")
        print(f"Dependency Path Chain: {res['root_cause']['dependency_chain']}")

    print("\n3. Testing GET /timeline...")
    status, res = get_route("/timeline")
    print(f"Status: {status}")
    print(f"Chronological events count: {len(res)}")
    for ev in res[:3]:
        print(f"- [{ev['time']}] {ev['title']}: {ev['description']}")

    print("\n4. Testing GET /playbook...")
    status, res = get_route("/playbook")
    print(f"Status: {status}")
    print(f"Remediation Playbook: {res.get('playbook_name')} (Confidence: {res.get('confidence')})")
    print(f"Remediation Action steps: {res.get('remediation_steps')}")

    print("\n5. Testing GET /business-impact...")
    status, res = get_route("/business-impact")
    print(f"Status: {status}")
    print(f"SLA Breach Risk Level: {res.get('sla_impact')}%")
    print(f"Operational Severity: {res.get('operational_severity')}")
    print(f"Estimated Downtime: {res.get('estimated_downtime_minutes')} minutes")

    print("\n6. Testing GET /blast-radius...")
    status, res = get_route("/blast-radius")
    print(f"Status: {status}")
    print(f"Blast Radius Level: {res.get('blast_radius_percent')}%")
    print(f"Is Single Point of Failure (SPOF): {res.get('is_spof')}")

    print("\n7. Testing GET /decision-summary...")
    status, res = get_route("/decision-summary")
    print(f"Status: {status}")
    print(f"Total Decision Confidence Score: {res.get('decision_confidence')}")
    print(f"Breakdown values: {res.get('confidence_breakdown')}")

    print("\n8. Testing POST /simulate (What-If Outage Simulation on HUB-Mumbai)...")
    status, res = post_route("/simulate", {"device_id": "HUB-Mumbai"})
    print(f"Status: {status}")
    print(f"Simulated Node: {res.get('device_id')}")
    print(f"Simulated Blast Radius: {res.get('blast_radius_percent')}%")
    print(f"Simulated SLA Users Impacted: {res.get('estimated_users_impacted')} users")
    print(f"Simulated predicted downtime: {res.get('predicted_downtime_minutes')} minutes")
    print(f"Simulated rerouting recommendation: {res.get('recommended_rerouting')}")

    # Recovery
    print("\nRecovering network to healthy baseline...")
    post_route("/recover", {})
    conn.close()

if __name__ == "__main__":
    test_phase4_endpoints()
