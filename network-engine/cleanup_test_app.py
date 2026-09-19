import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from database.connection import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM device_app_usage WHERE device_id='dev_001' AND application='HTTPS' "
            "AND download_bytes=45000 AND upload_bytes=5000 AND connections=1"
        )
        conn.commit()
        print("removed test app row")
finally:
    from database.connection import return_connection
    return_connection(conn)