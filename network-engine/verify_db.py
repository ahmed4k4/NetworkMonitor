import sys

def main():
    from database.connection import get_pool, return_connection, close_pool
    conn = get_pool().getconn()
    cur = conn.cursor()

    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
    rows = cur.fetchall()
    print("TABLE_COUNT", len(rows))
    for r in rows:
        print("TABLE:", r[0])

    conn.rollback()
    return_connection(conn)
    close_pool()

if __name__ == "__main__":
    main()