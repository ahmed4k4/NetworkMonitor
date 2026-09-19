import sys, io
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'network-engine'))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from api.app import app

def collect(routes, prefix, out):
    for r in routes:
        kind = type(r).__name__
        if kind == '_IncludedRouter':
            # new prefix from include_context
            ctx = getattr(r, 'include_context', None)
            pfx = prefix
            if ctx is not None:
                p = getattr(ctx, 'prefix', None)
                if p:
                    pfx = prefix.rstrip('/') + '/' + p.lstrip('/')
            sub = getattr(r, '_effective_candidates', None)
            if sub:
                collect(sub, pfx, out)
                continue
            orig = getattr(r, 'original_router', None)
            if orig is not None and hasattr(orig, 'routes'):
                collect(orig.routes, pfx, out)
                continue
        if kind == 'APIRoute':
            methods = ','.join(sorted(getattr(r, 'methods', []) or []))
            path = prefix.rstrip('/') + '/' + r.path.lstrip('/')
            out.append(f'{methods:20s} {path}')

out = []
collect(app.routes, '', out)
for line in sorted(set(out)):
    print(line)