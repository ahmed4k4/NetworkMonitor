from database.connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# Count active flows
cursor.execute("SELECT COUNT(*) FROM flows WHERE state = 'ACTIVE'")
active_flows = cursor.fetchone()[0]
print(f"Active flows: {active_flows}")

# Count active connections
cursor.execute("SELECT COUNT(*) FROM connections WHERE state = 'ACTIVE'")
active_connections = cursor.fetchone()[0]
print(f"Active connections: {active_connections}")

# Check what's in connections table
cursor.execute("SELECT COUNT(*) FROM connections")
total_connections = cursor.fetchone()[0]
print(f"Total connections: {total_connections}")

# Check flows with different states
cursor.execute("SELECT state, COUNT(*) FROM flows GROUP BY state")
flow_states = cursor.fetchall()
for r in flow_states:
    print(f"Flow state {r[0]}: {r[1]}")

# Check connections with different states
cursor.execute("SELECT state, COUNT(*) FROM connections GROUP BY state")
conn_states = cursor.fetchall()
for r in conn_states:
    print(f"Connection state {r[0]}: {r[1]}")

conn.close()