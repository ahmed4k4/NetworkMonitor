#!/usr/bin/env python
"""Test traffic split_part"""
from database.connection import get_connection

conn = get_connection()
with conn.cursor() as cur:
    cur.execute('''
        SELECT t.device_id::text AS device_id,
               COALESCE(split_part(d.ip_address::text, '/', 1), '') AS ip
        FROM traffic_samples t
        LEFT JOIN devices d ON d.device_id::text = t.device_id::text
        WHERE t.device_id::text = 'dev_002'
        ORDER BY t.sampled_at DESC
        LIMIT 3
    ''')
    for row in cur.fetchall():
        print(f'device_id={row[0]} ip="{row[1]}" type={type(row[1])}')
conn.close()