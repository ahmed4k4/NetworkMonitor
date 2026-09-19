import psycopg

conn = psycopg.connect(
    host="127.0.0.1",
    port=5432,
    dbname="network_control",
    user="postgres",
    password="12345678",
)

with conn.cursor() as cur:
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' ORDER BY table_name"
    )
    tables = [r[0] for r in cur.fetchall()]
    print("TABLES:", len(tables))
    for t in tables:
        print(" ", t)

    print("\n--- devices columns ---")
    cur.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='devices' ORDER BY ordinal_position"
    )
    for r in cur.fetchall():
        print(" ", r[0], r[1])

    print("\n--- devices row count ---")
    cur.execute("SELECT count(*) FROM devices")
    print(" ", cur.fetchone()[0])

conn.close()