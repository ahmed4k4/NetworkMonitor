import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.repository import DeviceIntelligenceRepository

repo = DeviceIntelligenceRepository()
domains = repo.get_device_domain_usage("dev_001", hours=24, limit=50)
print("get_device_domain_usage dev_001 24h:", len(domains))
for d in domains[:5]:
    print(" ", d)

apps = repo.get_device_app_usage("dev_001", hours=24)
print("get_device_app_usage dev_001 24h:", len(apps))
for a in apps[:5]:
    print(" ", a)

summary = repo.get_device_intelligence_summary("dev_001", hours=24)
print("summary top_domains:", len(summary["top_domains"]))
print("summary top_applications:", summary["top_applications"][:3])