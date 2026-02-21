import requests
import json
import time

url = "http://127.0.0.1:8000/research"
payload = {"query": "What are the latest advancements in AI?"}
headers = {"Content-Type": "application/json"}

try:
    print(f"Sending POST request to {url}...")
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 202:
        task_id = response.json().get("task_id")
        print(f"Task ID: {task_id}")
        
        # Poll for status
        for _ in range(5):
            time.sleep(2)
            status_url = f"http://127.0.0.1:8000/research/{task_id}"
            resp = requests.get(status_url)
            print(f"Task Status Response: {json.dumps(resp.json(), indent=2)}")
            status = resp.json().get("status")
            if status in ["completed", "failed"]:
                if status == "failed":
                    error_msg = resp.json().get('error')
                    print(f"Task FAILED. Error: {error_msg}")
                    with open("last_error.txt", "w") as f:
                        f.write(str(error_msg))
                break
except Exception as e:
    print(f"An error occurred: {e}")
