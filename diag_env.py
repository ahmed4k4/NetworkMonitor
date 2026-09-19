import sys
print("Python:", sys.version)

mods = ["scapy", "psycopg2", "fastapi", "uvicorn", "yaml", "pydantic"]
for m in mods:
    try:
        mod = __import__(m)
        ver = getattr(mod, "__version__", "?")
        print(f"OK   {m} = {ver}")
    except Exception as e:
        print(f"FAIL {m}: {type(e).__name__}: {e}")

# Scapy interface resolution
try:
    from scapy.all import conf, get_if_list
    print("\nScapy conf.iface:", conf.iface)
    print("Scapy interfaces:", get_if_list())
except Exception as e:
    print("\nScapy interface FAIL:", type(e).__name__, e)