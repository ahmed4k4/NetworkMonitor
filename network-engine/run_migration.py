import sys
sys.path.insert(0, ".")
from database.migrations import initialize_database

initialize_database()
print("MIGRATION COMPLETE")