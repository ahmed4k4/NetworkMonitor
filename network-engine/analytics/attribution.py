"""
Evidence-based Application Attribution Engine

This module implements attribution of network traffic to applications/services
based on multiple evidence sources with confidence levels.

Evidence sources (in order of reliability):
1. DNS queries - direct domain observations
2. SNI (TLS Server Name Indication) - from TLS handshakes
3. Known IP ranges (ASN/Org) - for CDNs, cloud providers
4. Protocol signatures - port-based heuristics
5. Destination metadata - reverse DNS, WHOIS
6. Application signatures - behavioral patterns

Confidence levels:
- High: Direct evidence (DNS match, SNI match)
- Medium: Strong indirect evidence (known IP range + protocol)
- Low: Weak evidence (port heuristic only)
"""

from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import ipaddress
import re
import json


@dataclass
class Evidence:
    """Single piece of evidence for attribution"""
    source: str  # 'dns', 'sni', 'ip_range', 'protocol', 'metadata', 'behavioral'
    value: str   # domain, IP, port, etc.
    weight: float  # 0.0 to 1.0
    confidence: str  # 'HIGH', 'MEDIUM', 'LOW'
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttributionResult:
    """Result of attribution analysis"""
    application: str
    category: str
    confidence: str  # 'HIGH', 'MEDIUM', 'LOW'
    evidence: List[Evidence]
    total_weight: float
    matched_rules: List[str] = field(default_factory=list)


class AttributionEngine:
    """
    Evidence-based application attribution engine.
    
    Uses multiple evidence sources to attribute traffic to applications
    with confidence levels. Never guesses - only returns what evidence supports.
    """
    
    def __init__(self):
        # Application definitions with evidence patterns
        self.applications = self._load_application_definitions()
        
        # Known IP ranges for major services (ASN-based)
        self.ip_ranges = self._load_ip_ranges()
        
        # Protocol to application mappings (weak evidence)
        self.protocol_hints = self._load_protocol_hints()
        
        # Domain category mappings
        self.domain_categories = self._load_domain_categories()
        
        # Cache for performance
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    def _load_application_definitions(self) -> Dict[str, Dict]:
        """Load application definitions with evidence patterns."""
        return {
            "YouTube": {
                "category": "Streaming",
                "domains": [
                    "youtube.com", "googlevideo.com", "ytimg.com",
                    "youtube-nocookie.com", "yt3.ggpht.com", "i.ytimg.com"
                ],
                "ip_ranges": [],  # Populated from ASN data
                "ports": [443, 80],
                "protocols": ["QUIC", "HTTPS"],
                "sni_patterns": ["youtube.com", "googlevideo.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.3,
            },
            "Netflix": {
                "category": "Streaming",
                "domains": [
                    "netflix.com", "nflxvideo.net", "nflximg.net",
                    "nflxext.com", "netflix.net", "netflixdn.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80],
                "protocols": ["HTTPS"],
                "sni_patterns": ["netflix.com", "nflxvideo.net"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.3,
            },
            "Google": {
                "category": "Web Services",
                "domains": [
                    "google.com", "googleapis.com", "gstatic.com",
                    "googleusercontent.com", "ggpht.com", "googleadservices.com",
                    "doubleclick.net", "googlesyndication.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 5228],
                "protocols": ["HTTPS", "HTTP", "XMPP"],
                "sni_patterns": ["google.com", "googleapis.com"],
                "weight_dns": 0.9,
                "weight_sni": 0.9,
                "weight_ip": 0.6,
                "weight_protocol": 0.2,
            },
            "Facebook": {
                "category": "Social Media",
                "domains": [
                    "facebook.com", "fbcdn.net", "fb.com",
                    "instagram.com", "cdninstagram.com",
                    "whatsapp.net", "whatsapp.com",
                    "messenger.com", "m.me"
                ],
                "ip_ranges": [],
                "ports": [443, 80],
                "protocols": ["HTTPS", "MQTT"],
                "sni_patterns": ["facebook.com", "fbcdn.net", "instagram.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.3,
            },
            "TikTok": {
                "category": "Social Media",
                "domains": [
                    "tiktok.com", "tiktokcdn.com", "tiktokv.com",
                    "musical.ly", "ibyteimg.com", "tiktokcdn-us.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80],
                "protocols": ["HTTPS", "QUIC"],
                "sni_patterns": ["tiktok.com", "tiktokcdn.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.3,
            },
            "Discord": {
                "category": "Communication",
                "domains": [
                    "discord.com", "discordapp.com", "discord.gg",
                    "discord.media", "discordapp.net", "discordstatus.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 50000, 50001, 50002, 50003, 50004, 50005, 50006, 50007, 50008, 50009],
                "protocols": ["HTTPS", "WebSocket", "UDP"],
                "sni_patterns": ["discord.com", "discordapp.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.4,
            },
            "Telegram": {
                "category": "Communication",
                "domains": [
                    "telegram.org", "t.me", "tdesktop.com",
                    "telegram.me", "telegram.dog"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 4433, 4434, 4435, 4436, 4437, 4438, 4439, 4440, 4441, 4442, 4443, 4444, 4445, 4446, 4447, 4448, 4449, 4450],
                "protocols": ["HTTPS", "MTProto"],
                "sni_patterns": ["telegram.org", "t.me"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.4,
            },
            "Steam": {
                "category": "Gaming",
                "domains": [
                    "steampowered.com", "steamcommunity.com", "steamcontent.com",
                    "steamstatic.com", "steamuserdata.com", "akamaihd.net",
                    "steamdatagram.net"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 27015, 27016, 27017, 27018, 27019, 27020, 27021, 27022, 27023, 27024, 27025, 27026, 27027, 27028, 27029, 27030],
                "protocols": ["HTTPS", "Steam Protocol"],
                "sni_patterns": ["steampowered.com", "steamcommunity.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.6,
                "weight_protocol": 0.5,
            },
            "Twitch": {
                "category": "Streaming",
                "domains": [
                    "twitch.tv", "ttvnw.net", "twitchcdn.net",
                    "jtvnw.net", "twitch.tv"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 1935],
                "protocols": ["HTTPS", "RTMP"],
                "sni_patterns": ["twitch.tv", "ttvnw.net"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.4,
            },
            "Microsoft": {
                "category": "Cloud Services",
                "domains": [
                    "microsoft.com", "windows.com", "office.com",
                    "azure.com", "azureedge.net", "azurefd.net",
                    "microsoftonline.com", "live.com", "outlook.com",
                    "onedrive.com", "sharepoint.com", "teams.microsoft.com",
                    "skype.com", "lync.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 3478, 3479, 3480, 3481, 50000, 50001],
                "protocols": ["HTTPS", "HTTP", "STUN", "TURN"],
                "sni_patterns": ["microsoft.com", "windows.com", "office.com"],
                "weight_dns": 0.9,
                "weight_sni": 0.9,
                "weight_ip": 0.6,
                "weight_protocol": 0.2,
            },
            "Apple": {
                "category": "Cloud Services",
                "domains": [
                    "apple.com", "icloud.com", "apple.com.cn",
                    "mzstatic.com", "itunes.apple.com", "apps.apple.com",
                    "gs.apple.com", "albert.apple.com", "xp.apple.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 5223],
                "protocols": ["HTTPS", "APNS"],
                "sni_patterns": ["apple.com", "icloud.com"],
                "weight_dns": 0.9,
                "weight_sni": 0.9,
                "weight_ip": 0.6,
                "weight_protocol": 0.2,
            },
            "Amazon": {
                "category": "Cloud Services",
                "domains": [
                    "amazon.com", "amazonaws.com", "cloudfront.net",
                    "amazonvideo.com", "primevideo.com", "aiv-cdn.net",
                    "aws.amazon.com", "s3.amazonaws.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80],
                "protocols": ["HTTPS"],
                "sni_patterns": ["amazon.com", "amazonaws.com"],
                "weight_dns": 0.8,
                "weight_sni": 0.8,
                "weight_ip": 0.7,
                "weight_protocol": 0.2,
            },
            "Cloudflare": {
                "category": "CDN/Infrastructure",
                "domains": [
                    "cloudflare.com", "cloudflare.net", "cloudflare-dns.com",
                    "cfdynamics.net", "cloudflareinsights.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 53, 853],
                "protocols": ["HTTPS", "DNS-over-HTTPS", "DNS-over-TLS"],
                "sni_patterns": ["cloudflare.com"],
                "weight_dns": 0.7,
                "weight_sni": 0.7,
                "weight_ip": 0.8,
                "weight_protocol": 0.3,
                "is_cdn": True,
            },
            "Akamai": {
                "category": "CDN/Infrastructure",
                "domains": [
                    "akamai.net", "akamaihd.net", "akamaiedge.net",
                    "edgesuite.net", "edgekey.net"
                ],
                "ip_ranges": [],
                "ports": [443, 80],
                "protocols": ["HTTPS"],
                "sni_patterns": ["akamai.net"],
                "weight_dns": 0.7,
                "weight_sni": 0.7,
                "weight_ip": 0.8,
                "weight_protocol": 0.2,
                "is_cdn": True,
            },
            "Spotify": {
                "category": "Streaming",
                "domains": [
                    "spotify.com", "scdn.co", "spotifycdn.com",
                    "audio-fa.scdn.co", "heads-fa.scdn.co"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 4070],
                "protocols": ["HTTPS", "P2P"],
                "sni_patterns": ["spotify.com", "scdn.co"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.3,
            },
            "Zoom": {
                "category": "Communication",
                "domains": [
                    "zoom.us", "zoom.com", "zoomgov.com",
                    "zoomcdn.com", "zwc.zoom.us"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 8801, 8802, 3478, 3479],
                "protocols": ["HTTPS", "STUN", "TURN", "UDP"],
                "sni_patterns": ["zoom.us", "zoom.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.5,
            },
            "Slack": {
                "category": "Communication",
                "domains": [
                    "slack.com", "slack-edge.com", "slack-msgs.com",
                    "slack-files.com", "slack-imgs.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80],
                "protocols": ["HTTPS", "WebSocket"],
                "sni_patterns": ["slack.com", "slack-edge.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.6,
                "weight_protocol": 0.3,
            },
            "GitHub": {
                "category": "Development",
                "domains": [
                    "github.com", "githubassets.com", "githubusercontent.com",
                    "githubapp.com", "github.io"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 22, 9418],
                "protocols": ["HTTPS", "SSH", "Git"],
                "sni_patterns": ["github.com", "githubassets.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.4,
            },
            "NVIDIA": {
                "category": "Gaming",
                "domains": [
                    "nvidia.com", "nvidia.net", "geforcenow.com",
                    "gfe.nvidia.com", "nvidiagrid.net"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 47984, 48010, 49001],
                "protocols": ["HTTPS", "GameStream"],
                "sni_patterns": ["nvidia.com", "geforcenow.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.4,
            },
            "Epic Games": {
                "category": "Gaming",
                "domains": [
                    "epicgames.com", "epicgames.net", "unrealengine.com",
                    "epicgames.dev", "epicgames.store"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 7777, 7778, 7779, 7780, 7781],
                "protocols": ["HTTPS", "Unreal"],
                "sni_patterns": ["epicgames.com", "unrealengine.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.6,
                "weight_protocol": 0.4,
            },
            "Battle.net": {
                "category": "Gaming",
                "domains": [
                    "battle.net", "blizzard.com", "blizzard.net",
                    "bnetstatic.com", "battle.net"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 1119, 3724, 6112, 6113, 6114],
                "protocols": ["HTTPS", "Battle.net Protocol"],
                "sni_patterns": ["battle.net", "blizzard.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.5,
            },
            "Origin": {
                "category": "Gaming",
                "domains": [
                    "origin.com", "ea.com", "ea.net",
                    "origin-a.akamaihd.net", "origin-edge-cdn.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 3216],
                "protocols": ["HTTPS"],
                "sni_patterns": ["origin.com", "ea.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.6,
                "weight_protocol": 0.3,
            },
            "Uplay": {
                "category": "Gaming",
                "domains": [
                    "ubisoft.com", "uplay.com", "ubi.com",
                    "ubisoft.net", "ubisoftgame.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 3074],
                "protocols": ["HTTPS"],
                "sni_patterns": ["ubisoft.com", "uplay.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.6,
                "weight_protocol": 0.3,
            },
            "Roblox": {
                "category": "Gaming",
                "domains": [
                    "roblox.com", "rbxcdn.com", "robloxusercontent.com",
                    "robloxapis.com", "roblox.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 49152, 49153, 49154, 49155, 49156, 49157, 49158, 49159, 49160, 49161, 49162, 49163, 49164, 49165, 49166, 49167],
                "protocols": ["HTTPS", "UDP"],
                "sni_patterns": ["roblox.com", "rbxcdn.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.7,
                "weight_protocol": 0.4,
            },
            "Minecraft": {
                "category": "Gaming",
                "domains": [
                    "minecraft.net", "mojang.com", "minecraft.net",
                    "minecraftservices.net", "msftconnecttest.com"
                ],
                "ip_ranges": [],
                "ports": [443, 80, 25565, 19132, 19133],
                "protocols": ["HTTPS", "Minecraft Protocol"],
                "sni_patterns": ["minecraft.net", "mojang.com"],
                "weight_dns": 1.0,
                "weight_sni": 1.0,
                "weight_ip": 0.6,
                "weight_protocol": 0.5,
            },
        }
    
    def _load_ip_ranges(self) -> Dict[str, List[str]]:
        """Load known IP ranges for major services (ASN-based).
        
        These are major known ranges. In production, these would be
        loaded from ASN databases like MaxMind or ipinfo.io.
        """
        return {
            "Google": [
                "8.8.8.0/24", "8.8.4.0/24",  # Google DNS
                "142.250.0.0/15", "172.217.0.0/16", "216.58.0.0/15",
                "173.194.0.0/16", "74.125.0.0/16", "64.233.160.0/19",
            ],
            "Microsoft": [
                "40.74.0.0/16", "40.112.0.0/15", "52.0.0.0/10",
                "13.64.0.0/11", "20.0.0.0/10", "104.0.0.0/10",
            ],
            "Amazon": [
                "52.0.0.0/10", "54.0.0.0/9", "18.0.0.0/9",
                "3.0.0.0/10", "35.0.0.0/10", "50.0.0.0/10",
            ],
            "Cloudflare": [
                "1.1.1.0/24", "1.0.0.0/24",  # Cloudflare DNS
                "104.16.0.0/13", "104.24.0.0/14", "172.64.0.0/13",
            ],
            "Akamai": [
                "23.0.0.0/11", "104.64.0.0/10", "184.0.0.0/10",
            ],
            "Fastly": [
                "151.101.0.0/16", "199.27.72.0/21", "199.232.0.0/16",
            ],
            "Facebook": [
                "31.13.24.0/21", "66.220.144.0/20", "69.63.176.0/20",
                "173.252.64.0/18", "179.60.192.0/22",
            ],
            "Netflix": [
                "198.45.48.0/20", "198.38.96.0/19", "192.254.68.0/22",
            ],
            "Apple": [
                "17.0.0.0/8",
            ],
        }
    
    def _load_protocol_hints(self) -> Dict[str, List[str]]:
        """Load protocol-to-application hints (weak evidence)."""
        return {
            53: ["DNS"],
            67: ["DHCP"],
            68: ["DHCP"],
            123: ["NTP"],
            161: ["SNMP"],
            162: ["SNMP"],
            389: ["LDAP"],
            443: ["HTTPS"],
            445: ["SMB"],
            465: ["SMTPS"],
            587: ["SMTP"],
            993: ["IMAPS"],
            995: ["POP3S"],
            1194: ["OpenVPN"],
            1723: ["PPTP"],
            3306: ["MySQL"],
            3389: ["RDP"],
            5432: ["PostgreSQL"],
            5900: ["VNC"],
            6379: ["Redis"],
            8080: ["HTTP-Proxy"],
            8443: ["HTTPS-Alt"],
        }
    
    def _load_domain_categories(self) -> Dict[str, str]:
        """Load domain to category mappings."""
        categories = {}
        for app_name, app_def in self.applications.items():
            for domain in app_def.get("domains", []):
                categories[domain] = app_def["category"]
        return categories
    
    def attribute_by_domain(self, domain: str) -> Tuple[Optional[str], Optional[str], List[Evidence]]:
        """Attribute traffic based on DNS domain."""
        if not domain:
            return None, None, []
        
        domain = domain.lower().rstrip('.')
        evidence = []
        
        # Exact match or subdomain match
        for app_name, app_def in self.applications.items():
            for pattern in app_def.get("domains", []):
                if domain == pattern or domain.endswith("." + pattern):
                    evidence.append(Evidence(
                        source="dns",
                        value=domain,
                        weight=app_def.get("weight_dns", 0.9),
                        confidence="HIGH",
                        details={"matched_pattern": pattern, "application": app_name}
                    ))
                    return app_name, app_def["category"], evidence
        
        # Check category from domain mappings
        for pattern, category in self.domain_categories.items():
            if domain == pattern or domain.endswith("." + pattern):
                return "Unknown", category, [Evidence(
                    source="dns",
                    value=domain,
                    weight=0.5,
                    confidence="MEDIUM",
                    details={"matched_pattern": pattern, "category": category}
                )]
        
        return None, None, []
    
    def attribute_by_sni(self, sni: str) -> Tuple[Optional[str], Optional[str], List[Evidence]]:
        """Attribute traffic based on TLS SNI."""
        if not sni:
            return None, None, []
        
        sni = sni.lower().rstrip('.')
        evidence = []
        
        for app_name, app_def in self.applications.items():
            for pattern in app_def.get("sni_patterns", []):
                if sni == pattern or sni.endswith("." + pattern):
                    evidence.append(Evidence(
                        source="sni",
                        value=sni,
                        weight=app_def.get("weight_sni", 0.9),
                        confidence="HIGH",
                        details={"matched_pattern": pattern, "application": app_name}
                    ))
                    return app_name, app_def["category"], evidence
        
        return None, None, []
    
    def attribute_by_ip(self, ip: str) -> Tuple[Optional[str], Optional[str], List[Evidence]]:
        """Attribute traffic based on destination IP (ASN/Org).

        Confidence is evidence-based only. An application is returned ONLY when
        there is an explicit, exact mapping between the holding organization and
        a known application (e.g. a Netflix-range IP -> Netflix). We NEVER
        fabricate an application from a generic "Cloud Services" or CDN range,
        because those ranges host many unrelated services. When the only
        evidence is a shared CDN / cloud range, we return (Unknown, Unknown)
        together with the range evidence so callers can display "Unknown"
        instead of inventing a name.
        """
        if not ip:
            return None, None, []
        
        try:
            ip_obj = ipaddress.ip_address(ip)
        except ValueError:
            return None, None, []
        
        evidence = []
        
        for org, ranges in self.ip_ranges.items():
            for cidr in ranges:
                try:
                    network = ipaddress.ip_network(cidr)
                except ValueError:
                    continue
                if ip_obj not in network:
                    continue
                # IP is inside a known organization range. Attribute to that
                # organization's application ONLY when an exact app exists with
                # that same name. No fuzzy category match => no fabricated apps.
                app_name = org
                if app_name in self.applications:
                    app_def = self.applications[app_name]
                    evidence.append(Evidence(
                        source="ip_range",
                        value=str(ip_obj),
                        weight=app_def.get("weight_ip", 0.5),
                        confidence="MEDIUM",
                        details={"cidr": cidr, "organization": org, "application": app_name}
                    ))
                    return app_name, app_def["category"], evidence
                # No explicit app for this org: shared range, do NOT invent one.
                evidence.append(Evidence(
                    source="ip_range",
                    value=str(ip_obj),
                    weight=0.5,
                    confidence="LOW",
                    details={"cidr": cidr, "organization": org, "application": None}
                ))
                return None, None, evidence
        return None, None, []
    
    def attribute_by_protocol_port(self, protocol: str, port: Optional[int]) -> Tuple[Optional[str], Optional[str], List[Evidence]]:
        """Attribute traffic based on protocol and port (weak evidence)."""
        evidence = []
        
        if port and port in self.protocol_hints:
            services = self.protocol_hints[port]
            if services:
                evidence.append(Evidence(
                    source="protocol",
                    value=f"{protocol}:{port}",
                    weight=0.3,
                    confidence="LOW",
                    details={"protocol": protocol, "port": port, "possible_services": services}
                ))
                return services[0], "Network Service", evidence
        
        return None, None, []
    
    def analyze(
        self,
        device_id: str,
        destination_ip: str = None,
        domain: str = None,
        sni: str = None,
        protocol: str = None,
        port: int = None,
        bytes_transferred: int = 0
    ) -> AttributionResult:
        """
        Analyze all evidence and return attribution with confidence.
        
        This is the main entry point for attribution.
        """
        all_evidence = []
        app_scores = defaultdict(float)
        app_evidence = defaultdict(list)
        categories = defaultdict(float)
        
        # 1. DNS Evidence (Highest confidence)
        if domain:
            app, cat, ev = self.attribute_by_domain(domain)
            if app:
                all_evidence.extend(ev)
                app_scores[app] += ev[0].weight
                app_evidence[app].extend(ev)
                categories[cat] += ev[0].weight
        
        # 2. SNI Evidence (Highest confidence)
        if sni:
            app, cat, ev = self.attribute_by_sni(sni)
            if app:
                all_evidence.extend(ev)
                app_scores[app] += ev[0].weight
                app_evidence[app].extend(ev)
                categories[cat] += ev[0].weight
        
        # 3. IP Range Evidence (Medium confidence)
        if destination_ip:
            app, cat, ev = self.attribute_by_ip(destination_ip)
            if app:
                all_evidence.extend(ev)
                app_scores[app] += ev[0].weight
                app_evidence[app].extend(ev)
                categories[cat] += ev[0].weight
        
        # 4. Protocol/Port Evidence (Lowest confidence)
        if protocol and port:
            app, cat, ev = self.attribute_by_protocol_port(protocol, port)
            if app:
                all_evidence.extend(ev)
                app_scores[app] += ev[0].weight
                app_evidence[app].extend(ev)
                categories[cat] += ev[0].weight
        
        # Determine best match
        if not app_scores:
            return AttributionResult(
                application="Unknown",
                category="Unknown",
                confidence="LOW",
                evidence=all_evidence,
                total_weight=0.0
            )
        
        # Get highest scoring application
        best_app = max(app_scores, key=app_scores.get)
        best_score = app_scores[best_app]
        best_category = self.applications.get(best_app, {}).get("category", categories.get(best_app, "Unknown"))
        
        # Determine confidence based on evidence quality
        has_high = any(e.confidence == "HIGH" for e in app_evidence[best_app])
        has_medium = any(e.confidence == "MEDIUM" for e in app_evidence[best_app])
        
        if has_high and best_score >= 1.0:
            confidence = "HIGH"
        elif has_medium and best_score >= 0.5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        
        # Get matched rules for transparency
        matched_rules = []
        for e in app_evidence[best_app]:
            if "matched_pattern" in e.details:
                matched_rules.append(f"{e.source}:{e.details['matched_pattern']}")
        
        return AttributionResult(
            application=best_app,
            category=best_category,
            confidence=confidence,
            evidence=app_evidence[best_app],
            total_weight=best_score,
            matched_rules=matched_rules
        )
    
    def get_category_for_application(self, application: str) -> str:
        """Get category for a known application."""
        return self.applications.get(application, {}).get("category", "Unknown")
    
    def get_category_for_domain(self, domain: str) -> Optional[str]:
        """Get category for a domain."""
        domain = domain.lower().rstrip('.')
        for pattern, category in self.domain_categories.items():
            if domain == pattern or domain.endswith("." + pattern):
                return category
        return None


class DeviceAttributionAggregator:
    """
    Aggregates attribution results per device over time periods.
    
    Stores and computes:
    - Per-application traffic with confidence breakdown
    - Per-domain traffic
    - Per-category traffic
    - Per-protocol traffic
    - Peak usage times
    """
    
    def __init__(self, db_pool=None):
        self.engine = AttributionEngine()
        self.db_pool = db_pool
    
    def process_flow(
        self,
        device_id: str,
        flow: Any,
        domain: str = None,
        sni: str = None
    ) -> AttributionResult:
        """Process a flow and return attribution."""
        return self.engine.analyze(
            device_id=device_id,
            destination_ip=getattr(flow, 'destination_ip', None),
            domain=domain,
            sni=sni,
            protocol=getattr(flow, 'protocol', None),
            port=getattr(flow, 'destination_port', None),
            bytes_transferred=getattr(flow, 'bytes', 0)
        )
    
    def aggregate_device_traffic(
        self,
        device_id: str,
        start_time: str,
        end_time: str,
        granularity: str = "daily"
    ) -> Dict[str, Any]:
        """
        Aggregate attributed traffic for a device over a time range.
        
        Returns comprehensive breakdown by application, domain, category, protocol.
        """
        # This would query the database for flows in the time range
        # and apply attribution to each, then aggregate
        # Implementation depends on database schema additions
        pass


# Global instance
attribution_engine = AttributionEngine()


def attribute_traffic(device_id: str, **kwargs) -> AttributionResult:
    """Convenience function for attribution."""
    return attribution_engine.analyze(device_id=device_id, **kwargs)