import psycopg
from psycopg_pool import ConnectionPool
from config import database_config
from logger import logger

# Connection pool for high-frequency database operations
# This prevents connection overhead during packet processing
_pool = None

def get_pool() -> ConnectionPool:
    """Get or create the global connection pool"""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=f"host={database_config.host} port={database_config.port} dbname={database_config.database} user={database_config.user} password={database_config.password}",
            min_size=5,
            max_size=20,
            max_waiting=50,
            max_lifetime=3600,
            max_idle=300,
            open=True,
        )
        logger.info("Database connection pool created")
    return _pool

def get_connection():
    """
    Get a connection from the pool.
    Returns a pooled connection that should be returned to pool when done.
    """
    return get_pool().getconn()

def return_connection(conn):
    """Return a connection to the pool"""
    if conn is not None:
        get_pool().putconn(conn)

def close_pool():
    """Close the connection pool on shutdown"""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
        logger.info("Database connection pool closed")
