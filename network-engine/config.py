import os
import yaml
from dataclasses import dataclass
from pathlib import Path


def load_yaml_config():
    """Load configuration from config/system.yaml"""
    config_path = Path(__file__).parent.parent / "config" / "system.yaml"
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


yaml_config = load_yaml_config()


@dataclass
class NetworkConfig:

    lan_interface: str = None
    lan_ip: str = None
    lan_subnet: str = None
    upstream_gateway: str = None
    wan_interface: str = None
    wan_ip: str = None
    wan_gateway: str = None
    
    scan_interval: int = None
    discovery_interval: int = None
    capture_filter: str = ""
    flow_timeout: int = None
    bandwidth_window: int = None
    tz: str = "Africa/Cairo"

    def __post_init__(self):
        """Apply YAML config and environment overrides"""
        net_config = yaml_config.get("network", {})
        
        if self.lan_interface is None:
            self.lan_interface = os.getenv(
                "LAN_INTERFACE",
                net_config.get("lan_interface", "Ethernet")
            )
        
        if self.lan_ip is None:
            self.lan_ip = os.getenv(
                "LAN_IP",
                net_config.get("lan_ip", "192.168.137.1")
            )
        
        if self.lan_subnet is None:
            self.lan_subnet = os.getenv(
                "LAN_SUBNET",
                net_config.get("lan_subnet", "192.168.137.0/24")
            )
        
        if self.upstream_gateway is None:
            self.upstream_gateway = os.getenv(
                "UPSTREAM_GATEWAY",
                net_config.get("upstream_gateway", "")
            )
        
        if self.wan_interface is None:
            self.wan_interface = os.getenv(
                "WAN_INTERFACE",
                net_config.get("wan_interface", "Wi-Fi")
            )
        
        # capture_filter: optional BPF filter for the packet sniffer.
        if self.capture_filter == "":
            self.capture_filter = os.getenv(
                "CAPTURE_FILTER",
                net_config.get("capture_filter", "")
            )
        
        if self.scan_interval is None:
            self.scan_interval = int(os.getenv(
                "SCAN_INTERVAL",
                net_config.get("scan_interval", 10)
            ))
        
        if self.discovery_interval is None:
            self.discovery_interval = int(os.getenv(
                "DISCOVERY_INTERVAL",
                net_config.get("discovery_interval", 10)
            ))
        
        if self.flow_timeout is None:
            self.flow_timeout = int(os.getenv(
                "FLOW_TIMEOUT",
                net_config.get("flow_timeout", 60)
            ))
        
        if self.bandwidth_window is None:
            self.bandwidth_window = int(os.getenv(
                "BANDWIDTH_WINDOW",
                net_config.get("bandwidth_window", 1)
            ))


@dataclass
class DatabaseConfig:

    host: str = None
    port: int = None
    database: str = None
    user: str = None
    password: str = None

    def __post_init__(self):
        """Apply YAML config and environment overrides"""
        db_config = yaml_config.get("database", {})
        
        if self.host is None:
            self.host = os.getenv(
                "POSTGRES_HOST",
                db_config.get("host", "127.0.0.1")
            )
        
        if self.port is None:
            self.port = int(os.getenv(
                "POSTGRES_PORT",
                db_config.get("port", 5432)
            ))
        
        if self.database is None:
            self.database = os.getenv(
                "POSTGRES_DB",
                db_config.get("name", "network_control")
            )
        
        if self.user is None:
            self.user = os.getenv(
                "POSTGRES_USER",
                db_config.get("user", "postgres")
            )
        
        if self.password is None:
            self.password = os.getenv(
                "POSTGRES_PASSWORD",
                db_config.get("password", "12345678")
            )


network_config = NetworkConfig()
database_config = DatabaseConfig()


@dataclass
class AuthConfig:
    jwt_secret: str = None
    jwt_algorithm: str = "HS256"
    token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    def __post_init__(self):
        """Apply YAML config and environment overrides"""
        if self.jwt_secret is None:
            self.jwt_secret = os.getenv(
                "NETWORK_CONTROL_JWT_SECRET",
                yaml_config.get("jwt_secret", "your-secure-random-secret-change-in-production")
            )


auth_config = AuthConfig()
