"""Dump the live OpenAPI paths to compare with frontend api.ts call sites."""
import json, urllib.request

with urllib.request.urlopen("http://127.0.0.1:8000/openapi.json", timeout=15) as r:
    spec = json.load(r)

for path in sorted(spec["paths"].keys()):
    methods = ",".join(m.upper() for m in spec["paths"][path].keys())
    print(f"{methods:12s} {path}")