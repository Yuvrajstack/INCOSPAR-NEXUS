import http.client
import json
import time

def test_api():
    print("Connecting to local Incospar Nexus AI Backend...")
    conn = http.client.HTTPConnection("127.0.0.1", 8000)
    
    # Test 1: GET /devices
    print("\n--- Test 1: GET /devices ---")
    conn.request("GET", "/devices")
    res = conn.getresponse()
    print(f"Status: {res.status}")
    devices = json.loads(res.read().decode())
    for d in devices:
        print(f"- {d['name']} ({d['id']}): Status={d['status']}, CPU={d['cpu_usage']:.1f}%")
        
    # Test 2: Inject Congestion
    print("\n--- Test 2: POST /inject-fault (CONGESTION_BR3) ---")
    headers = {'Content-type': 'application/json'}
    body = json.dumps({"scenario": "CONGESTION_BR3"})
    conn.request("POST", "/inject-fault", body, headers)
    res = conn.getresponse()
    print(f"Status: {res.status}")
    print(res.read().decode())
    
    # Wait for telemetry updates
    print("\nWaiting 3 seconds for drift to occur...")
    time.sleep(3)
    
    # Test 3: GET /devices (Verify state changed)
    print("\n--- Test 3: GET /devices (After Injection) ---")
    conn.request("GET", "/devices")
    res = conn.getresponse()
    devices = json.loads(res.read().decode())
    for d in devices:
        if d['id'] == "BR-Chennai":
            print(f"- {d['name']} ({d['id']}): Status={d['status']}, CPU={d['cpu_usage']:.1f}% (Expected: warning/critical with higher CPU)")
            
    # Test 4: Recover network
    print("\n--- Test 4: POST /recover ---")
    conn.request("POST", "/recover")
    res = conn.getresponse()
    print(f"Status: {res.status}")
    print(res.read().decode())
    
    conn.close()

if __name__ == "__main__":
    try:
        test_api()
    except Exception as e:
        print(f"Error during API tests: {e}")
