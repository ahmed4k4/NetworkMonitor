from database.connection import get_connection


connection = get_connection()

print("PostgreSQL connection successful")

connection.close()