import sys
sys.path.insert(0, '.')
from database.connection import get_connection, return_connection

conn = get_connection()
cur = conn.cursor()

print('=== DB totals dev_002 (traffic_samples) ===')
cur.execute(
    "SELECT date_trunc('day', sampled_at) d, SUM(download_bytes), SUM(upload_bytes), SUM(packets), COUNT(*) "
    "FROM traffic_samples WHERE device_id=%s GROUP BY d ORDER BY d DESC LIMIT 7",
    ('dev_002',)
)
for r in cur.fetchall():
    print('  ', r)

print()
print('=== RAW last 5 samples dev_002 ===')
cur.execute(
    "SELECT device_id, sampled_at, download_bytes, upload_bytes, packets, connections, "
    "download_speed_bps, upload_speed_bps "
    "FROM traffic_samples WHERE device_id=%s ORDER BY sampled_at DESC LIMIT 5",
    ('dev_002',)
)
for r in cur.fetchall():
    print('  ', r)

print()
print('=== TODAY total (all time today, UTC) dev_002 ===')
cur.execute(
    "SELECT SUM(download_bytes), SUM(upload_bytes) FROM traffic_samples "
    "WHERE device_id=%s AND sampled_at >= date_trunc('day', now())",
    ('dev_002',)
)
print('  today sum dl/ul =', cur.fetchone())

print()
print('=== devices row dev_002 ===')
cur.execute(
    "SELECT device_id, mac_address, ip_address, state, last_seen, first_seen "
    "FROM devices WHERE device_id=%s",
    ('dev_002',)
)
print('  ', cur.fetchone())

print()
print('=== daily_usage / analytics tables referencing dev_002 ===')
cur.execute(
    "SELECT table_name FROM information_schema.tables WHERE table_schema='public' "
    "AND table_name LIKE '%usage%' OR table_name LIKE '%analytics%' OR table_name LIKE '%daily%'"
)
for r in cur.fetchall():
    t = r[0]
    try:
        cur2 = conn.cursor()
        cur2.execute("SELECT * FROM %s WHERE device_id=%%s LIMIT 3" % t, ('dev_002',))
        cols = [d[0] for d in cur2.description]
        print('  ', t, 'cols=', cols)
        for row in cur2.fetchall():
            print('     ', row)
    except Exception as e:
        print('  ', t, 'table query failed:', e)

return_connection(conn)