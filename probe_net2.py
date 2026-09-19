import sys, subprocess
sys.path.insert(0, r"e:\NetworkMonitor\network-engine")

# Map Windows adapter friendly names + MACs to ifindex
ps = ["powershell","-NoProfile","-Command",
  "Get-NetAdapter | Select-Object Name,InterfaceDescription,MacAddress,Status,ifIndex | Format-Table -AutoSize | Out-String"]
print( subprocess.run(ps, capture_output=True, text=True).stdout )

print("=== scapy iface resolution ===")
from scapy.all import conf, get_if_list, get_if_raw_hwaddr
confs = conf.ifaces
print("conf.ifaces type:", type(confs))
for name in ["Ethernet","Wi-Fi","Ethernet 2","Local Area Connection"]:
    try:
        ifc = conf.iface if False else None
    except Exception:
        pass
    try:
        # try resolve by name
        resolved = conf.ifaces.dev_from_name(name)
        print(f"dev_from_name({name}) -> ", resolved, "guid_hint=", getattr(resolved,'guid',None))
    except Exception as e:
        print(f"dev_from_name({name}) FAILED: {repr(e)[:120]}")

print("=== iterate all conf.ifaces (name -> guid) ===")
try:
    items = list(conf.ifaces.values()) if hasattr(conf.ifaces,'values') else list(conf.ifaces)
    for it in items[:25]:
        print(repr(getattr(it,'name',None)), "|", repr(getattr(it,'description',None)), "|", getattr(it,'guid',None))
except Exception as e:
    print("iterate failed:", repr(e)[:200])

print("=== get_if_raw_hwaddr on Ethernet guid (needs pcap; may fail without admin) ===")
try:
    from scapy.all import get_if_raw_hwaddr
    print(get_if_raw_hwaddr("Ethernet"))
except Exception as e:
    print("get_if_raw_hwaddr(Ethernet) failed:", repr(e)[:150])