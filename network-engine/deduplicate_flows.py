from database.connection import get_connection
conn = get_connection()
cursor = conn.cursor()
try:
    # First, check duplicates
    cursor.execute("""
        SELECT device_id, source_ip, destination_ip, source_port, destination_port, protocol, interface_name, COUNT(*) as cnt
        FROM flows
        GROUP BY device_id, source_ip, destination_ip, source_port, destination_port, protocol, interface_name
        HAVING COUNT(*) > 1
    """)
    duplicates = cursor.fetchall()
    print(f"Found {len(duplicates)} duplicate groups")
    
    for dup in duplicates:
        print(f"  Duplicate: {dup}")
    
    # Delete duplicates, keeping only the most recent (highest id) for each group
    cursor.execute("""
        DELETE FROM flows
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM flows
            GROUP BY device_id, source_ip, destination_ip, source_port, destination_port, protocol, interface_name
        )
    """)
    deleted_count = cursor.rowcount
    conn.commit()
    print(f"Deleted {deleted_count} duplicate rows")
    
    # Now add the unique constraint
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