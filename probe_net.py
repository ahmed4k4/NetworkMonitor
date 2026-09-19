import sys
sys.path.insert(0, r"e:\NetworkMonitor\network-engine")
print("=== Windows adapters (Get-NetIPAddress) ===")
import subprocess
out = subprocess.run(["powershell","-NoProfile","-Command",
  "Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike '127.*'} | Select-Object InterfaceAlias,InterfaceIndex,IPAddress,PrefixLength | Format-Table -AutoSize | Out-String"],
  capture_output=True, text=True)
print(out.stdout)
print("=== ARP/neighbor cache (netsh, non-admin) ===")
out2 = subprocess.run(["netsh","interface","ipv4","show","neighbors"], capture_output=True, text=True)
print(out2.stdout[:4000])
print("=== scapy Npcap interfaces ===")
try:
    from scapy.all import get_if_list, conf
    print("default conf.iface strips:", conf.iface)
    print(get_if_list())
except Exception as e:
    print("scapy get_if_list failed:", repr(e))