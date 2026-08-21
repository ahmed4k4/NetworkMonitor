import psycopg

from config import database_config


def get_connection():

    return psycopg.connect(
        host=database_config.host,
        port=database_config.port,
        dbname=database_config.database,
        user=database_config.user,
        password=database_config.password,
    )