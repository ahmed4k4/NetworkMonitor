import psycopg

try:
    # Connect as postgres to network_control to drop existing tables
    conn = psycopg.connect(
        host='127.0.0.1',
        port=5432,
        dbname='network_control',
        user='postgres',
        password='12345678',
        autocommit=True
    )
    
    with conn.cursor() as cursor:
        # Drop all tables
        try:
            cursor.execute("""
                DO $$ 
                DECLARE 
                    r RECORD; 
                BEGIN 
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') 
                    LOOP 
                        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE'; 
                    END LOOP; 
                END $$;
            """)
            print('Dropped all existing tables')
        except Exception as e:
            print(f'Could not drop tables: {e}')
    
    conn.close()
    print('Cleanup complete - ready for fresh schema creation')
    
except Exception as e:
    print(f'Error: {e}')
