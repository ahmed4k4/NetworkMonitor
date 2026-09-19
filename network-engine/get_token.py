import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from api.auth import create_access_token

token = create_access_token('admin', 'ADMIN')
print('Token:', token)
