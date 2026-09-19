import psycopg

conn = psycopg.connect('postgresql://postgres:12345678@localhost:5432/network_control')
cur = conn.cursor()

# Add missing columns to device_domain_usage
print("Adding confidence column...")
try:
    cur.execute('ALTER TABLE device_domain_usage ADD COLUMN confidence VARCHAR(20) DEFAULT \'MEDIUM\'')
    conn.commit()
    print("  Added confidence column")
except Exception as e:
    conn.rollback()
    print(f"  Error: {e}")

print("Adding evidence column...")
try:
    cur.execute('ALTER TABLE device_domain_usage ADD COLUMN evidence JSONB')
    conn.commit()
    print("  Added evidence column")
except Exception as e:
    conn.rollback()
    print(f"  Error: {e}")

# Verify
cur.execute('SELECT column_name FROM information_schema.columns WHERE table_name = \'device_domain_usage\'')
print('\ndevice_domain_usage columns after fix:')
for row in cur.fetchall():
    print(f'  {row[0]}')

conn.close()