from database.connection import get_connection
conn = get_connection()
cursor = conn.cursor()
try:
    cursor.execute("""
        ALTER TABLE flows 
        ADD CONSTRAINT flows_unique_flow 
        UNIQUE(device_id, source_ip, destination_ip, source_port, destination_port, protocol, interface_name)
    """)
    conn.commit()
    print("Unique constraint added successfully")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()