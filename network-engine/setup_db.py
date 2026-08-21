import psycopg

try:
    # Connect as postgres with autocommit
    conn = psycopg.connect(
        host='127.0.0.1',
        port=5432,
        dbname='postgres',
        user='postgres',
        password='12345678',
        autocommit=True
    )
    
    with conn.cursor() as cursor:
        # Create database if not exists
        try:
            cursor.execute('CREATE DATABASE network_control')
            print('Created database: network_control')
        except psycopg.errors.DuplicateDatabase:
            print('Database already exists: network_control')
        
        # Create user if not exists
        try:
            cursor.execute("CREATE USER network_admin WITH PASSWORD '12345678'")
            print('Created user: network_admin')
        except psycopg.errors.DuplicateObject:
            print('User already exists: network_admin')
            # Update password just to be sure
            cursor.execute("ALTER USER network_admin WITH PASSWORD '12345678'")
            print('Updated password for: network_admin')
        
        # Grant privileges on database
        try:
            cursor.execute("GRANT ALL PRIVILEGES ON DATABASE network_control TO network_admin")
            print('Granted privileges on database network_control')
        except Exception as e:
            print(f'Could not grant database privileges: {e}')
        
        # Connect to network_control to grant schema/table privileges
        conn.close()
    
    # Now connect to network_control and grant schema permissions
    conn2 = psycopg.connect(
        host='127.0.0.1',
        port=5432,
        dbname='network_control',
        user='postgres',
        password='12345678',
        autocommit=True
    )
    
    with conn2.cursor() as cursor:
        # Grant usage on public schema
        try:
            cursor.execute("GRANT USAGE ON SCHEMA public TO network_admin")
            print('Granted USAGE on schema public')
        except Exception as e:
            print(f'Could not grant USAGE on schema: {e}')
        
        # Grant create on public schema
        try:
            cursor.execute("GRANT CREATE ON SCHEMA public TO network_admin")
            print('Granted CREATE on schema public')
        except Exception as e:
            print(f'Could not grant CREATE on schema: {e}')
    
    conn2.close()
    print('PostgreSQL setup complete')
    
except Exception as e:
    print(f'Error: {e}')
