import requests

for port in (8000, 8080):
    for path in ('/api/auth/login', '/login', '/api/login'):
        try:
            r = requests.post(f'http://localhost:{port}{path}',
                              json={'username': 'admin', 'password': 'admin_change_me'},
                              timeout=5)
            body = r.text[:300]
            print(f'PORT {port} POST {path} -> {r.status_code} {body}')
        except Exception as e:
            print(f'PORT {port} POST {path} -> EXC {e}')