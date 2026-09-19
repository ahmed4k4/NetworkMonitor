import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJBRE1JTiIsImV4cCI6MTc4NzUyNTQ0NSwidHlwZSI6ImFjY2VzcyJ9.Px897Lm2VSbSdXZOBf7FW6b0BJTMF1rb-_AdBZkq8-0"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get("http://127.0.0.1:8000/api/analytics/domains", headers=headers)
print("Status:", response.status_code)
print("Response:")
import json
print(json.dumps(response.json(), indent=2))