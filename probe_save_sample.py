import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "network-engine")
import logging
logging.basicConfig(level=logging.DEBUG)
from database.repository import TrafficRepository
r = TrafficRepository()
try:
    r.save_delta_sample(
        device_id="dev_002",
        download_delta=100,
        upload_delta=50,
        packets_delta=3,
        connections=2,
        download_speed_bps=800,
        upload_speed_bps=400,
        mac_address=None,
        ip_address="192.168.137.75",
        hostname=None,
    )
    print("SAVE OK")
except Exception as e:
    print("SAVE FAILED:", type(e).__name__, e)