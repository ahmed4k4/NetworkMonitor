import os
import re

route_dir = os.path.join(os.path.dirname(__file__), 'api', 'routes')
for filename in os.listdir(route_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(route_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace connection.close() with return_connection(connection)
        # But only if the file imports get_connection or uses it
        if 'get_connection' in content or 'from database.connection import' in content:
            new_content = content.replace('connection.close()', 'return_connection(connection)')
            if new_content != content:
                # Also need to ensure return_connection is imported
                if 'return_connection' not in content:
                    # Add import if not present
                    if 'from database.connection import' in new_content:
                        new_content = new_content.replace(
                            'from database.connection import get_connection',
                            'from database.connection import get_connection, return_connection'
                        )
                    elif 'import get_connection' in new_content:
                        new_content = new_content.replace(
                            'from database.connection import get_connection',
                            'from database.connection import get_connection, return_connection'
                        )
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Fixed: {filename}')
            else:
                print(f'No changes: {filename}')
        else:
            print(f'Skipped (no DB): {filename}')

# Fix auth.py init_default_users
auth_path = os.path.join(os.path.dirname(__file__), 'api', 'auth.py')
with open(auth_path, 'r', encoding='utf-8') as f:
    content = f.read()
if 'connection.close()' in content:
    content = content.replace('connection.close()', 'return_connection(connection)')
    if 'return_connection' not in content:
        content = content.replace(
            'from database.connection import get_connection',
            'from database.connection import get_connection, return_connection'
        )
    with open(auth_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Fixed: api/auth.py')
else:
    print('auth.py already fixed')
