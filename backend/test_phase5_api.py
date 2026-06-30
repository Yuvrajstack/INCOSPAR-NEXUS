import http.client
import json
import time

def test_phase5_endpoints():
    print("==================================================")
    print("   SENTINELNET AI PHASE 5 API VERIFICATION TEST   ")
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

    # 1. Test GET /copilot/knowledge (verify RAG index loader finds markdown files)
    print("\n1. Testing GET /copilot/knowledge...")
    status, res = get_route("/copilot/knowledge")
    print(f"Status: {status}")
    print("Runbooks indexed in local Vector DB:")
    for doc in res:
        print(f"- File: {doc['filename']}, Chars: {doc['character_count']}, Status: {doc['status']}")

    # 2. Test GET /copilot/context (verify live metrics collection)
    print("\n2. Testing GET /copilot/context...")
    status, res = get_route("/copilot/context")
    print(f"Status: {status}")
    print(f"Live active anomaly: {res.get('active_anomaly')}")
    print(f"Device counts: {res.get('device_count')}")

    # 3. Test POST /copilot/chat (with no anomalies active)
    print("\n3. Testing POST /copilot/chat (General health query)...")
    query = {"message": "Summarize the current network health", "session_id": "operator_1"}
    status, res = post_route("/copilot/chat", query)
    print(f"Status: {status}")
    print("Structured Copilot Output Keys:", list(res.keys()))
    print(f"Summary: {res.get('summary')}")
    print(f"Confidence score: {res.get('overall_confidence')}")
    print(f"Confidence breakdown: {res.get('confidence_breakdown')}")

    # Injecting Anomaly
    print("\nInjecting failure scenario (CONGESTION_BR3)...")
    post_route("/inject-fault", {"scenario": "CONGESTION_BR3"})
    time.sleep(2) # Allow simulation tick to update DB and run engine pass

    # 4. Test POST /copilot/chat (with active anomaly)
    print("\n4. Testing POST /copilot/chat (RCA / Troubleshooting query)...")
    query = {"message": "Why is the Chennai link experiencing high latency?", "session_id": "operator_1"}
    status, res = post_route("/copilot/chat", query)
    print(f"Status: {status}")
    print(f"Summary: {res.get('summary')}")
    print(f"Overall Confidence: {res.get('overall_confidence')}")
    print(f"Prediction Confidence: {res.get('prediction_confidence')}")
    print(f"Knowledge Match Confidence: {res.get('knowledge_confidence')}")
    print(f"Decision Confidence: {res.get('decision_confidence')}")
    print(f"RAG Score: {res.get('rag_score')}")
    print(f"Isolated Root Cause: {res.get('root_cause')}")
    print(f"Business Impact: {res.get('business_impact')}")
    print(f"Blast Radius: {res.get('blast_radius')}")
    print(f"Recommended Actions: {res.get('recommended_actions')}")
    print(f"References Cited: {res.get('references')}")

    # 5. Test GET /copilot/history (verify session memory contains conversation history)
    print("\n5. Testing GET /copilot/history...")
    status, res = get_route("/copilot/history?session_id=operator_1")
    print(f"Status: {status}")
    print("History Entries:")
    for h in res.get("history", []):
        print(f"- Question: {h['question']}")
        print(f"  Response summary: {h['response_summary'][:80]}...")

    # Recovery
    print("\nRecovering network to healthy baseline...")
    post_route("/recover", {})
    conn.close()

if __name__ == "__main__":
    test_phase5_endpoints()
