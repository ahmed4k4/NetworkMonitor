from config import network_config as config
from logger import logger

import threading
import time
import ipaddress
import requests
from datetime import datetime

from discovery.scanner import DeviceScanner
from discovery.identity import DeviceIdentityManager

from database.repository import DeviceRepository, FlowRepository, TrafficRepository
from database.connection import get_connection

from capture.sniffer import PacketSniffer

from flow.manager import FlowManager
from flow.bandwidth import BandwidthTracker
from flow.connections import ConnectionTracker
from flow.device_stats import DeviceTrafficStats

from analytics.engine import AnalyticsEngine


class NetworkEngine:
    """Main network monitoring engine"""

    def __init__(self):
        logger.info("Initializing NetworkEngine...")
        
        self.identity = DeviceIdentityManager()
        self.analytics = AnalyticsEngine()

        # Per-device byte tracking for real usage deltas
        self.device_bytes = {}
        self.last_sample_bytes = {}

        # Parse network CIDR
        self.lan_network = ipaddress.ip_network(
            f"{config.lan_ip}/24",
            strict=False
        )
        
        logger.info(f"LAN Network: {self.lan_network}")
        logger.info(f"LAN Interface: {config.lan_interface}")
        logger.info(f"Upstream Gateway: {config.upstream_gateway}")

        self.device_scanner = DeviceScanner(
            str(self.lan_network),
            config.lan_interface,
        )

        self.device_repository = DeviceRepository()
        self.flow_repository = FlowRepository()
        self.traffic_repository = TrafficRepository()

        self.flow_manager = FlowManager(
            str(self.lan_network),
            config.lan_interface,
            flow_timeout=config.flow_timeout,
        )

        self.bandwidth = BandwidthTracker(
            config.bandwidth_window
        )

        self.connections = ConnectionTracker()
        self.device_stats = DeviceTrafficStats()

        self.devices = {}
        self.last_discovery = 0
        self.discovery_interval = config.discovery_interval
        self.discovery_thread = None
        self.running = False

        self.sniffer = PacketSniffer(
            interface=config.lan_interface,
            callback=self.process_packet,
            capture_filter=config.capture_filter,
        )

        logger.info("NetworkEngine initialized successfully")

    def is_lan_device(self, ip: str) -> bool:
        """Check if IP is on the LAN (handles /32 suffix from INET type)"""
        if ip is None:
            return False
        # Strip /32 or /24 suffix from INET type
        clean_ip = ip.split('/')[0]
        try:
            return ipaddress.ip_address(clean_ip) in self.lan_network
        except ValueError:
            return False

    def discover_devices(self):
        """Perform device discovery"""
        try:
            logger.debug("Starting device discovery...")
            
            devices = self.device_scanner.scan()
            
            # Track which devices were found
            found_macs = set()
            discovered_devices = []
            
            for device in devices:
                device_id = self.identity.get_device_id(device["mac"])
                found_macs.add(device["mac"])

                device["device_id"] = device_id
                device["interface"] = config.lan_interface
                device["state"] = "ONLINE"
                device["vendor"] = device.get("vendor", "Unknown")

                self.devices[device_id] = device
                self.device_repository.upsert_device(device)

                logger.info(
                    f"DEVICE | {device_id} | {device['ip']} | {device['mac']}"
                )
                
                discovered_devices.append(device)

            # Check for devices that went offline
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT device_id, mac_address, state FROM devices WHERE state = 'ONLINE'"
                    )
                    for row in cursor.fetchall():
                        device_id, mac, state = row
                        # Normalize MAC for comparison
                        mac_normalized = mac.upper().replace("-", ":")
                        
                        # If device was online but not found in scan, mark offline
                        if mac_normalized not in found_macs:
                            self.device_repository.mark_offline(device_id)
                            if device_id in self.devices:
                                self.devices[device_id]["state"] = "OFFLINE"
                            
                            # Broadcast device offline event
                            asyncio_safe_broadcast({
                                "type": "device_offline",
                                "data": {
                                    "device_id": device_id,
                                }
                            })
                            
                            logger.info(f"Device marked OFFLINE: {device_id}")
            finally:
                connection.close()
            
            # Broadcast device discovery events
            for device in discovered_devices:
                asyncio_safe_broadcast({
                    "type": "device_discovered",
                    "data": {
                        "device_id": device["device_id"],
                        "ip_address": device.get("ip"),
                        "mac_address": device.get("mac"),
                        "hostname": device.get("hostname"),
                        "vendor": device.get("vendor"),
                    }
                })

        except Exception as e:
            logger.error(f"Error in device discovery: {e}", exc_info=True)

    def _continuous_discovery_loop(self):
        """Continuous device discovery loop that runs in background"""
        logger.info("Starting continuous discovery loop...")
        
        sample_counter = 0
        sample_interval = 5  # Save traffic sample every 5 cycles (50 seconds with 10s interval)
        status_counter = 0
        status_interval = 2  # Broadcast system status every 2 cycles (20 seconds with 10s interval)
        
        while self.running:
            try:
                self.discover_devices()
                
                # Periodically save traffic samples
                sample_counter += 1
                if sample_counter >= sample_interval:
                    self._save_traffic_samples()
                    sample_counter = 0
                
                # Periodically broadcast system status
                status_counter += 1
                if status_counter >= status_interval:
                    self._broadcast_system_status()
                    status_counter = 0
                    
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}", exc_info=True)
            
            # Sleep for the configured interval
            time.sleep(self.discovery_interval)

    def _broadcast_system_status(self):
        """Broadcast system status to WebSocket clients"""
        try:
            stats = self.get_statistics()
            asyncio_safe_broadcast({
                "type": "system_status",
                "data": {
                    "total_devices": stats["devices"],
                    "online_devices": stats["devices_online"],
                    "offline_devices": stats["devices"] - stats["devices_online"],
                    "active_connections": stats["active_connections"],
                    "active_flows": stats["flows"],
                    "current_speed_bps": int(stats["current_mbps"] * 1_000_000),
                    "current_download_speed_bps": int(stats["current_mbps"] * 1_000_000 / 2),
                    "current_upload_speed_bps": int(stats["current_mbps"] * 1_000_000 / 2),
                    "peak_bandwidth_bps": int(stats["peak_mbps"] * 1_000_000),
                }
            })
        except Exception as e:
            logger.error(f"Error broadcasting system status: {e}")

    def start_discovery_loop(self):
        """Start the continuous discovery background thread"""
        if self.discovery_thread is None or not self.discovery_thread.is_alive():
            self.running = True
            self.discovery_thread = threading.Thread(
                target=self._continuous_discovery_loop,
                daemon=True,
                name="DiscoveryThread"
            )
            self.discovery_thread.start()
            logger.info("Discovery loop thread started")

    def stop_discovery_loop(self):
        """Stop the continuous discovery thread"""
        self.running = False
        if self.discovery_thread and self.discovery_thread.is_alive():
            self.discovery_thread.join(timeout=5)
            logger.info("Discovery loop thread stopped")

    def process_packet(self, packet):
        """Process a captured packet"""
        try:
            # Parse packet with analytics
            packet = self.analytics.process_packet(packet)
            
            if packet is None:
                return
            
            # Determine device from source IP OR destination IP (for download traffic)
            device_id = None
            source_ip = packet.get("source_ip")
            destination_ip = packet.get("destination_ip")
            
            source_is_lan = self.is_lan_device(source_ip)
            dest_is_lan = self.is_lan_device(destination_ip)
            
            if source_is_lan:
                # Upload or local traffic - device is the source
                connection = get_connection()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT device_id FROM devices WHERE ip_address = %s",
                            (source_ip,)
                        )
                        result = cursor.fetchone()
                        device_id = result[0] if result else None
                finally:
                    connection.close()
            elif dest_is_lan:
                # Download traffic - device is the destination
                connection = get_connection()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT device_id FROM devices WHERE ip_address = %s",
                            (destination_ip,)
                        )
                        result = cursor.fetchone()
                        device_id = result[0] if result else None
                finally:
                    connection.close()
            
            # Determine direction for bandwidth tracking
            direction = "TOTAL"
            if source_is_lan and not dest_is_lan:
                direction = "UPLOAD"
            elif not source_is_lan and dest_is_lan:
                direction = "DOWNLOAD"
            elif source_is_lan and dest_is_lan:
                direction = "LOCAL"
            
            # Track bandwidth (global + per-device)
            self.bandwidth.add(packet["size"], device_id=device_id, direction=direction)

            # Track real per-device byte counters for usage deltas
            if device_id:
                if device_id not in self.device_bytes:
                    self.device_bytes[device_id] = {"upload": 0, "download": 0, "packets": 0}
                if direction == "UPLOAD":
                    self.device_bytes[device_id]["upload"] += packet["size"]
                elif direction == "DOWNLOAD":
                    self.device_bytes[device_id]["download"] += packet["size"]
                self.device_bytes[device_id]["packets"] += 1

            # Process flow
            flow = self.flow_manager.process_packet(packet)
            
            if flow:
                # Set device_id on flow
                if device_id:
                    flow.device_id = device_id

                # Update connection tracking
                self.connections.update(flow)
                
                # Update device stats
                self.device_stats.process(packet)
                
                # Save flow to database
                try:
                    self.flow_repository.save_flow(flow)
                except Exception as e:
                    logger.error(f"Error saving flow: {e}")

        except Exception as e:
            logger.error(f"Error processing packet: {e}", exc_info=True)

    def _save_traffic_samples(self):
        """Save current traffic samples for all devices using real per-device byte deltas"""
        try:
            for device_id, device in self.devices.items():
                if device.get("state") == "ONLINE":
                    # Get per-device bandwidth speeds
                    download_speed = self.bandwidth.device_download_bps(device_id)
                    upload_speed = self.bandwidth.device_upload_bps(device_id)
                    
                    # Get current cumulative byte counters for this device
                    current = self.device_bytes.get(device_id, {"upload": 0, "download": 0, "packets": 0})
                    previous = self.last_sample_bytes.get(device_id, {"upload": 0, "download": 0, "packets": 0})
                    
                    # Compute real deltas since last sample
                    download_delta = max(0, current["download"] - previous["download"])
                    upload_delta = max(0, current["upload"] - previous["upload"])
                    packets_delta = max(0, current["packets"] - previous["packets"])
                    
                    # Save this device's current counters as the baseline for next sample
                    self.last_sample_bytes[device_id] = dict(current)
                    
                    # Save real delta sample
                    self.traffic_repository.save_delta_sample(
                        device_id=device_id,
                        download_delta=download_delta,
                        upload_delta=upload_delta,
                        packets_delta=packets_delta,
                        connections=len(self.connections.active()),
                        download_speed_bps=int(download_speed),
                        upload_speed_bps=int(upload_speed),
                    )
                    
                    # Get current device usage from DB
                    usage_today = self.device_repository.get_device_usage_today(device_id)
                    
                    # Broadcast real-time traffic update
                    asyncio_safe_broadcast({
                        "type": "traffic_update",
                        "data": {
                            "device_id": device_id,
                            "ip": device.get("ip"),
                            "download_speed_bps": int(download_speed),
                            "upload_speed_bps": int(upload_speed),
                            "download_today": usage_today["download"],
                            "upload_today": usage_today["upload"],
                            "total_today": usage_today["total"],
                        }
                    })
            logger.debug(f"Saved traffic samples for {len(self.devices)} devices")
        except Exception as e:
            logger.error(f"Error saving traffic samples: {e}")

    def cleanup_flows(self):
        """Periodically clean up old flows"""
        try:
            closed_flows = self.flow_manager.cleanup()
            
            for flow in closed_flows:
                try:
                    self.flow_repository.save_flow(flow)
                    
                    # Broadcast flow update event
                    asyncio_safe_broadcast({
                        "type": "flow_update",
                        "data": {
                            "device_id": flow.device_id,
                            "source_ip": str(flow.source_ip),
                            "destination_ip": str(flow.destination_ip),
                            "protocol": flow.protocol,
                            "bytes": flow.bytes,
                            "packets": flow.packets,
                            "direction": flow.direction,
                        }
                    })
                except Exception as e:
                    logger.error(f"Error saving closed flow: {e}")
                    
        except Exception as e:
            logger.error(f"Error in flow cleanup: {e}")

    def start_capture(self):
        """Start packet capture"""
        logger.info(f"Starting packet capture on {config.lan_interface}")
        try:
            self.sniffer.start()
        except Exception as e:
            logger.error(f"Error starting packet capture: {e}", exc_info=True)
            raise

    def stop_capture(self):
        """Stop packet capture"""
        logger.info("Stopping packet capture...")
        try:
            self.sniffer.stop()
        except Exception as e:
            logger.error(f"Error stopping packet capture: {e}")

    def get_statistics(self):
        """Get current system statistics"""
        return {
            "devices": len(self.devices),
            "devices_online": len([d for d in self.devices.values() if d.get("state") == "ONLINE"]),
            "flows": len(self.flow_manager.flows),
            "active_connections": len(self.connections.active()),
            "current_mbps": self.bandwidth.current_mbps(),
            "peak_mbps": self.bandwidth.peak_mbps(),
        }


def asyncio_safe_broadcast(message: dict):
    """Safely broadcast WebSocket message via HTTP to API process"""
    try:
        # Call the API's broadcast endpoint
        response = requests.post(
            "http://127.0.0.1:8000/api/system/broadcast",
            json={"type": message.get("type", ""), "data": message.get("data", {})},
            timeout=2.0
        )
        if response.status_code != 200:
            logger.warning(f"Broadcast failed with status {response.status_code}: {response.text}")
    except Exception as e:
        logger.warning(f"Could not broadcast WebSocket message: {e}")
