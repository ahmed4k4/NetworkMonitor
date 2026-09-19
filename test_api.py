import requests
import json

# Login
login_data = {"username": "admin", "password": "admin"}
response = requests.post("http://127.0.0.1:8000/api/auth/login", json=login_data)
print("Login:", response.status_code, response.json())

if response.status_code == 200:
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test DNS
    dns_resp = requests.get("http://127.0.0.1:8000/api/dns/recent", headers=headers)
    print("DNS:", dns_resp.status_code, dns_resp.json()[:2] if dns_resp.json() else [])
    
    # Test applications analytics
    apps_resp = requests.get("http://127.0.0.1:8000/api/analytics/applications", headers=headers)
    print("Apps:", apps_resp.status_code, apps_resp.json()[:2] if apps_resp.json() else [])
    
    # Test devices
    dev_resp = requests.get("http://127.0.0.1:8000/api/devices/", headers=headers)
    print("Devices:", dev_resp.status_code, dev_resp.json()[:2] if dev_resp.json() else [])
    
    # Test domains analytics
    dom_resp = requests.get("http://127.0.0.1:8000/api/analytics/domains", headers=headers)
    print("Domains:", dom_resp.status_code, dom_resp.json()[:2] if dom_resp.json() else [])