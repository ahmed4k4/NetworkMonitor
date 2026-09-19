import sys
sys.path.insert(0, r'e:\NetworkMonitor\network-engine')
from scapy.layers.inet import IP, UDP
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import Ether
from scapy.layers.dns import DNS, DNSQR, DNSRR
from capture.parser import parse_packet, extract_dns

# 1) DNS QUERY packet
q_pkt = Ether(src="aa:bb:cc:dd:ee:01", dst="11:22:33:44:55:66")/IP(src="192.168.137.10", dst="8.8.8.8")/UDP(sport=53000, dport=53)/DNS(
    id=1, qr=0, qd=DNSQR(qname="www.youtube.com.", qtype=1)
)
parsed = parse_packet(q_pkt)
print("QUERY parsed dns:", parsed.get("dns"))
assert parsed["dns"]["domain"] == "www.youtube.com"
assert parsed["dns"]["response_ip"] is None

# 2) DNS RESPONSE packet with an A record
rr = DNSRR(rrname="www.youtube.com.", type=1, rdata="142.250.185.196")
r_pkt = Ether(src="11:22:33:44:55:66", dst="aa:bb:cc:dd:ee:01")/IP(src="8.8.8.8", dst="192.168.137.1")/UDP(sport=53, dport=53000)/DNS(
    id=1, qr=1, qd=DNSQR(qname="www.youtube.com.", qtype=1), an=rr,
)
parsed_r = parse_packet(r_pkt)
print("RESPONSE parsed:", parsed_r.get("dns"))
assert parsed_r["dns"]["domain"] == "www.youtube.com"
assert parsed_r["dns"]["response_ip"] == "142.250.185.196"

# 3) IPv6 AAAA response
rr6 = DNSRR(rrname="www.youtube.com.", type=28, rdata="2607:f8b0:4004:800::200e")
r6 = Ether(src="11:22:33:44:55:66", dst="aa:bb:cc:dd:ee:01")/IPv6(src="2001:4860:4860::8888", dst="2001:db8::1")/UDP(sport=53, dport=53000)/DNS(
    id=2, qr=1, qd=DNSQR(qname="www.youtube.com.", qtype=28), an=rr6,
)
parsed6 = parse_packet(r6)
print("AAAA RESPONSE parsed:", parsed6.get("dns"))
assert parsed6["dns"]["response_ip"] is not None

print("\nPARSER TESTS PASSED")

# 4) Repository: save query then correlate
from database.repository import DeviceIntelligenceRepository
repo = DeviceIntelligenceRepository()
# Use an existing device (FK constraint) and a marker domain for isolation
test_domain = "testdomain.example.com"
repo.save_dns_query("dev_001", test_domain, "A")
repo.save_dns_query("dev_001", test_domain, "A", response_ip="203.0.113.50")
print("save_dns_query with response_ip ok")

from database.connection import get_connection
conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT device_id, domain, query_type, response_ip::text
            FROM dns_queries
            WHERE device_id = 'dev_001' AND domain = %s
            ORDER BY queried_at DESC LIMIT 3
        """, (test_domain,))
        rows = cur.fetchall()
        for row in rows:
            print("DNS row:", row)
        assert any(row[3].split("/")[0] == "203.0.113.50" for row in rows), "response_ip was not stored!"

        # Verify the engine's correlation query finds the domain for that IP
        cur.execute("""
            SELECT domain FROM dns_queries
            WHERE device_id = 'dev_001'
              AND response_ip = '203.0.113.50'
            ORDER BY queried_at DESC
            LIMIT 1
        """)
        found = cur.fetchone()
        print("Correlated domain:", found)
        assert found and found[0] == test_domain

    # Cleanup the test rows (do not pollute real data)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM dns_queries WHERE domain = %s", (test_domain,))
    conn.commit()
    print("\nREPOSITORY + CORRELATION TESTS PASSED")
finally:
    from database.connection import return_connection
    return_connection(conn)