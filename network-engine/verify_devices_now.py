import sys
from database.connection import get_connection, return_connection

def main():
    c = get_connection()
    try:
        cur = c.cursor()
        cur.execute(
            """
            SELECT device_id,
                   split_part(ip_address::text, '/', 1) AS ip,
                   mac_address, hostname, vendor, state,
                   total_upload, total_download, last_seen
            FROM devices
            ORDER BY device_id
            """
        )
        rows = cur.fetchall()
        print("Devices:")
        for r in rows:
            print(r)
        print(f"\nTotal devices: {len(rows)}")
    finally:
        return_connection(c)
    return 0

if __name__ == "__main__":
    sys.exit(main())