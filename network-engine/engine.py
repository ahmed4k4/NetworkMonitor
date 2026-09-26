from config import network_config as config
from logger import logger

import threading
import time
import ipaddress
import requests
from datetime import datetime, timezone

from discovery.scanner import DeviceScanner
from discovery.identity import DeviceIdentityManager

from database.repository import DeviceRepository, FlowRepository, TrafficRepository, DeviceIntelligenceRepository
from database.connection import get_connection, return_connection

from capture.sniffer import PacketSniffer

from flow.manager import FlowManager
from flow.bandwidth import BandwidthTracker
from flow.connections import ConnectionTracker
from flow.device_stats import DeviceTrafficStats

from analytics.engine import AnalyticsEngine
from analytics.attribution import AttributionEngine, attribute_traffic

from control.quotas import QuotaEngine


class NetworkEngine:
    """Main network monitoring engine"""

    def __init__(self):
        logger.info("Initializing NetworkEngine...")
        
        self.identity = DeviceIdentityManager()
        self.analytics = AnalyticsEngine()

        # Per-device byte tracking for real usage deltas
        self.device_bytes = {}
        self.last_sample_bytes = {}

        # Timestamp of the previous traffic-sample save, used to derive
        # bytes-per-second from byte deltas over the real elapsed interval.
        import time as _time
        self._last_sample_time = _time.time()

        # Cached network-wide real-time speeds (bps) derived from byte deltas,
        # broadcast to the dashboard between sample saves.
        self._live_speed = {"download_bps": 0, "upload_bps": 0}

        # Highest network-wide delta-derived total speed observed (bps), used
        # for peak_bandwidth in the live system-status broadcast.
        self._peak_live_bps = 0

        # Parse network CIDR. Prefer the explicit lan_subnet when configured,
        # otherwise derive a /24 from the host's lan_ip. In ICS topology the
        # host (192.168.137.1) is the LAN gateway and the phone (192.168.137.2)
        # is an ordinary LAN device, so the subnet MUST cover the client range
        # (e.g. 192.168.137.0/24), not exclude it.
        if config.lan_subnet:
            self.lan_network = ipaddress.ip_network(
                config.lan_subnet,
                strict=False
            )
        else:
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
            upstream_gateway=config.upstream_gateway,
        )
        
        # Pass LAN network to flow manager for direction detection
        self.flow_manager.lan_network = self.lan_network

        self.bandwidth = BandwidthTracker(
            config.bandwidth_window
        )

        self.connections = ConnectionTracker()
        self.device_stats = DeviceTrafficStats(
            lan_network=self.lan_network,
            upstream_gateway=config.upstream_gateway,
        )

        # Initialize Device Intelligence Repository
        self.intel_repo = DeviceIntelligenceRepository()

        # Attribution engine
        self.attribution = AttributionEngine()

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

        # Initialize QuotaEngine for quota enforcement
        self.quota_engine = QuotaEngine()

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

    def _is_boundary_ip(self, ip) -> bool:
        """True if this IP is the monitor host's own NAT-boundary IP.

        In the ICS topology the host (config.lan_ip == 192.168.137.1) is the
        gateway, NOT a client device. Any captured frame whose source or
        destination is this IP is the host's own traffic and must never be
        attributed to a "device". This prevents the host's own frames (seen via
        promiscuous capture on the bridge) from re-creating a phantom device.
        """
        if ip is None:
            return False
        if not config.lan_ip:
            return False
        clean = str(ip).split('/')[0]
        return clean == config.lan_ip.split('/')[0]

    def discover_devices(self):
        """Perform device discovery"""
        try:
            logger.debug("Starting device discovery...")
            
            devices = self.device_scanner.scan()
            
            # Track which devices were found
            found_macs = set()
            discovered_devices = []
            
            for device in devices:
                ip = device.get("ip")
                mac = device.get("mac")

                # SKIP the monitor host's own boundary IP. In the ICS topology
                # the host (config.lan_ip == 192.168.137.1) is the NAT gateway,
                # NOT a client device. Tracking it as a device makes the host's
                # own NAT-boundary traffic appear as a phantom "device" with
                # upload/download counters.
                if ip is not None:
                    clean_ip = str(ip).split('/')[0]
                    if config.lan_ip and clean_ip == config.lan_ip.split('/')[0]:
                        logger.debug(f"Skipping boundary host IP {ip} (not a client device)")
                        continue

                # SKIP broadcast/multicast/zero MACs. These are not devices.
                if mac is not None:
                    mac_norm = self.identity.normalize_mac(mac)
                    if mac_norm in ("FF:FF:FF:FF:FF:FF", "00:00:00:00:00:00"):
                        logger.debug(f"Skipping broadcast/zero MAC {mac}")
                        continue
                    # Multicast bit (least significant bit of first octet) set.
                    first = mac_norm.split(':')[0]
                    if int(first, 16) & 1:
                        logger.debug(f"Skipping multicast MAC {mac}")
                        continue

                # IP-first identity: prefer reusing an existing device_id that
                # already owns this IP, so a device whose MAC randomizes is NOT
                # forked into duplicate records (dev_003 vs dev_006). Only fall
                # back to MAC-based identity when no IP is known.
                device_id = None
                if ip is not None:
                    clean_ip = str(ip).split('/')[0]
                    device_id = self._get_device_id_by_ip(clean_ip)
                if device_id is None:
                    device_id = self.identity.get_device_id(mac)

                found_macs.add(mac)

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

            # Check for devices that went offline.
            # ONLINE/OFFLINE is based on RECENT REAL TRAFFIC (last_seen within
            # ONLINE_THRESHOLD), NOT on a single missed ARP scan. A phone that
            # is actively sending traffic but that the periodic ARP broadcast
            # probe missed (AP isolation / phone sleep / ARP no-reply) must NOT
            # be flipped to OFFLINE. Only devices with no traffic for longer
            # than the threshold are marked offline.
            ONLINE_THRESHOLD_SECONDS = 60
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT device_id, mac_address, state, last_seen
                        FROM devices
                        WHERE state = 'ONLINE'
                        """
                    )
                    for row in cursor.fetchall():
                        device_id, mac, state, last_seen = row
                        # Normalize MAC for comparison
                        mac_normalized = mac.upper().replace("-", ":")
                        
                        # If device was online but not found in scan, check if it
                        # has had recent traffic. If last_seen is recent, keep it
                        # ONLINE (traffic recency is the authoritative signal).
                        if mac_normalized not in found_macs:
                            # If last_seen is NULL or older than threshold, mark offline
                            if last_seen is None or \
                               (datetime.now(timezone.utc) - last_seen).total_seconds() > ONLINE_THRESHOLD_SECONDS:
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
                                
                                logger.info(f"Device marked OFFLINE (no traffic for >{ONLINE_THRESHOLD_SECONDS}s): {device_id}")
            finally:
                # The SELECT above leaves the connection INTRANS; roll back so
                # the pooled connection is returned clean (avoids the
                # "rolling back returned connection" warning on every cycle).
                connection.rollback()
                return_connection(connection)
            
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
        cleanup_counter = 0
        cleanup_interval = 6  # Clean up flows every 6 cycles (60 seconds with 10s interval)
        active_attribution_counter = 0
        active_attribution_interval = 2  # Attribute active flows every 2 cycles (~20s)
        domain_agg_counter = 0
        domain_agg_interval = 6  # Re-sync DNS->domain usage every 6 cycles (60s)
        quota_reset_counter = 0
        quota_reset_interval = 180  # Check quota reset every 180 cycles (30 minutes with 10s interval)
        retention_counter = 0
        retention_interval = 8640  # Run retention cleanup every 8640 cycles (24 hours with 10s interval)
        
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
                
                # Periodically clean up old flows
                cleanup_counter += 1
                if cleanup_counter >= cleanup_interval:
                    self.cleanup_flows()
                    cleanup_counter = 0
                
                # Attribute still-ACTIVE long-lived flows incrementally so the
                # Applications/Domains/Categories/Protocols tabs never go stale
                # or empty during an ongoing traffic session.
                active_attribution_counter += 1
                if active_attribution_counter >= active_attribution_interval:
                    self.attribute_active_flows()
                    active_attribution_counter = 0
                
                # Periodically sync observed DNS queries into domain usage
                domain_agg_counter += 1
                if domain_agg_counter >= domain_agg_interval:
                    try:
                        self.intel_repo.aggregate_dns_domains(hours=24)
                    except Exception as e:
                        logger.error(f"Error aggregating DNS domains: {e}")
                    domain_agg_counter = 0
                
                # Periodically check and reset quotas
                quota_reset_counter += 1
                if quota_reset_counter >= quota_reset_interval:
                    self.quota_engine.check_and_reset_quotas()
                    quota_reset_counter = 0
                
                # Periodically run data retention cleanup
                retention_counter += 1
                if retention_counter >= retention_interval:
                    from database.retention import cleanup_old_data, get_table_sizes
                    cleanup_old_data()
                    get_table_sizes()
                    retention_counter = 0
                    
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}", exc_info=True)
            
            # Sleep for the configured interval
            time.sleep(self.discovery_interval)

    def _broadcast_system_status(self):
        """Broadcast system status to WebSocket clients.

        CURRENT SPEED is a RATE derived from real byte deltas over the real
        elapsed sample interval (stored in self._live_speed by
        _save_traffic_samples). It decays to 0 when the last sample is older
        than the sampling cadence, so it never shows a fabricated value or a
        50/50 fake download/upload split.
        """
        try:
            stats = self.get_statistics()

            # Derive real, delta-based speeds. If the sample loop has not run
            # recently (e.g. no ONLINE devices or a long stall), fall back to 0
            # rather than reporting a stale or fabricated number.
            cadence = max(1.0, self.discovery_interval * 5)
            stale = (time.time() - self._last_sample_time) > cadence

            download_bps = int(self._live_speed.get("download_bps", 0)) if not stale else 0
            upload_bps = int(self._live_speed.get("upload_bps", 0)) if not stale else 0
            total_bps = download_bps + upload_bps

            asyncio_safe_broadcast({
                "type": "system_status",
                "data": {
                    "total_devices": stats["devices"],
                    "online_devices": stats["devices_online"],
                    "offline_devices": stats["devices"] - stats["devices_online"],
                    "active_connections": stats["active_connections"],
                    "active_flows": stats["flows"],
                    "current_speed_bps": total_bps,
                    "current_download_speed_bps": download_bps,
                    "current_upload_speed_bps": upload_bps,
                    # Real peak observed by the delta sampler (network-wide bps).
                    "peak_bandwidth_bps": int(self._peak_live_bps),
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

    def _get_device_id_by_mac(self, mac):
        """Get device_id from MAC address using identity manager"""
        if not mac:
            return None
        return self.identity.get_device_id(mac)

    def _get_device_id_by_ip(self, ip):
        """Get device_id from IP address (fallback).

        The devices.ip_address column is INET and may store the value either as
        a bare address ("192.168.137.75") or with a suffix ("192.168.137.75/32"),
        so match both forms. Prefer the most recently seen device so a device
        whose MAC randomized (and was forked) resolves to the latest record.

        Refuses to resolve the monitor host's own boundary IP: the host is not
        a client device, and must never be attributed device traffic.
        """
        if not ip:
            return None
        if self._is_boundary_ip(ip):
            return None
        clean = str(ip).split('/')[0]
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT device_id FROM devices
                    WHERE ip_address = %s OR ip_address = %s
                    ORDER BY last_seen DESC NULLS LAST
                    LIMIT 1
                    """,
                    (clean, f"{clean}/32")
                )
                result = cursor.fetchone()
                return result[0] if result else None
        finally:
            return_connection(connection)

    def process_packet(self, packet):
        """Process a captured packet"""
        try:
            # Parse packet with analytics
            packet = self.analytics.process_packet(packet)
            
            if packet is None:
                return
            
            # Determine device from MAC address (most reliable)
            source_mac = packet.get("source_mac")
            destination_mac = packet.get("destination_mac")
            source_ip = packet.get("source_ip")
            destination_ip = packet.get("destination_ip")
            
            # Use flow manager's direction logic for consistency
            source_is_lan = self.flow_manager._is_local(source_ip)
            dest_is_lan = self.flow_manager._is_local(destination_ip)
            
            device_id = None
            
            # IP-first identity: resolve the LAN client endpoint's device_id by
            # its IP so a device whose MAC randomizes (phone privacy MAC) is NOT
            # forked into duplicate records.
            #
            # The monitor host's own boundary IP (the ICS gateway, 192.168.137.1)
            # is NEVER a client device and must never be attributed traffic.
            # _get_device_id_by_ip already refuses to resolve the boundary IP,
            # and _is_local treats the gateway as non-local, so the host can
            # never become the attributed device. Crucially, we must NOT drop
            # attribution just because the OTHER endpoint is the boundary host:
            # every real internet packet has the host as one endpoint
            #   phone(.75) -> host(.1)   == UPLOAD
            #   host(.1)  -> phone(.75)  == DOWNLOAD
            # and was previously (bug) set device_id=None, which made ALL
            # internet traffic unattributed and every speed/byte counter zero.
            device_id = None
            if source_is_lan and source_ip and not self._is_boundary_ip(source_ip):
                device_id = self._get_device_id_by_ip(source_ip)
            elif dest_is_lan and destination_ip and not self._is_boundary_ip(destination_ip):
                device_id = self._get_device_id_by_ip(destination_ip)

            if device_id is None:
                if source_is_lan and source_mac:
                    device_id = self._get_device_id_by_mac(source_mac)
                elif dest_is_lan and destination_mac:
                    device_id = self._get_device_id_by_mac(destination_mac)
            
            # Determine direction for bandwidth tracking (use flow manager's logic)
            direction = "LOCAL"
            if source_is_lan and not dest_is_lan:
                direction = "UPLOAD"
            elif not source_is_lan and dest_is_lan:
                direction = "DOWNLOAD"
            # else: LOCAL (LAN-to-LAN, broadcast, multicast, etc.)
            
            # Track bandwidth (global + per-device) - only for Internet traffic
            if direction != "LOCAL":
                self.bandwidth.add(packet["size"], device_id=device_id, direction=direction)

            # Track real per-device byte counters for usage deltas - only Internet traffic
            if device_id and direction != "LOCAL":
                if device_id not in self.device_bytes:
                    self.device_bytes[device_id] = {"upload": 0, "download": 0, "packets": 0}
                if direction == "UPLOAD":
                    self.device_bytes[device_id]["upload"] += packet["size"]
                elif direction == "DOWNLOAD":
                    self.device_bytes[device_id]["download"] += packet["size"]
                self.device_bytes[device_id]["packets"] += 1

            # Process DNS query/response if present
            dns = packet.get("dns")
            if dns and device_id:
                domain = dns.get("domain")
                query_type = dns.get("query_type", "A")
                response_ip = dns.get("response_ip")
                if domain:
                    # Save DNS query (with response IP when available) to database
                    try:
                        self.intel_repo.save_dns_query(device_id, domain, query_type, response_ip=response_ip)
                    except Exception as e:
                        logger.error(f"Error saving DNS query: {e}")
                    
                    # Also process through analytics for domain tracking
                    try:
                        self.analytics.process_dns(device_id, domain, query_type)
                    except Exception as e:
                        logger.error(f"Error processing DNS in analytics: {e}")
            
            # Process flow (will use same direction logic internally)
            flow = self.flow_manager.process_packet(packet, device_id=device_id)
            
            if flow and flow.device_id:
                # Only track/save flows with a valid device_id

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
        """Save current traffic samples for all devices using real per-device byte deltas.

        Speed is derived from the byte delta over the real elapsed interval
        (speed_bps = bytes_delta * 8 / elapsed_seconds). This avoids the
        jumpy/static speeds produced by the short bandwidth window."""
        try:
            now = time.time()
            # Actual seconds since the previous sample save (guarded to avoid
            # division by zero / implausibly high speeds after long stalls).
            elapsed = max(1.0, now - self._last_sample_time)
            self._last_sample_time = now

            # Reset the network-wide live speed cache each cycle.
            net_download_bps = 0
            net_upload_bps = 0

            # Iterate over every device that we have either discovered OR that
            # has recorded byte counters (device_bytes is the authoritative
            # "this traffic belongs to device X" ledger, independent of the ARP
            # scanner). This guarantees a device that sends traffic is never
            # skipped just because the periodic ARP scan missed it, so its
            # counters always update.
            device_ids = set(self.devices.keys()) | set(self.device_bytes.keys()) | set(self.last_sample_bytes.keys())

            for device_id in device_ids:
                device = self.devices.get(device_id, {})

                # A device is actively online if it has fresh byte deltas since
                # the last sample. Prefer the recorded-traffic signal over the
                # scanner's state so a quiet-but-active device still updates.
                current = self.device_bytes.get(device_id, {"upload": 0, "download": 0, "packets": 0})
                previous = self.last_sample_bytes.get(device_id, {"upload": 0, "download": 0, "packets": 0})
                download_delta = max(0, current["download"] - previous["download"])
                upload_delta = max(0, current["upload"] - previous["upload"])
                packets_delta = max(0, current["packets"] - previous["packets"])

                # Skip only if the device produced NO new traffic in this cycle
                # AND is not currently marked ONLINE (so idle-but-online devices
                # still emit a 0-speed sample to keep their speed decaying).
                if (download_delta + upload_delta + packets_delta) <= 0 \
                        and device.get("state") != "ONLINE":
                    continue

                # Save this device's current counters as the baseline for next sample
                self.last_sample_bytes[device_id] = dict(current)

                # Current speed = byte_delta / elapsed interval, in bits/sec.
                download_speed = (download_delta * 8) / elapsed
                upload_speed = (upload_delta * 8) / elapsed

                # Per-device active connections = distinct active flows for
                # THIS device (flow_manager is pruned by flow_timeout).
                device_conns = sum(
                    1 for f in self.flow_manager.flows.values()
                    if f.device_id == device_id and f.state == "ACTIVE"
                )

                # Save real delta sample. Pass the device's MAC/IP/hostname so
                # the repository can create/refresh the devices row (mac_address
                # is NOT NULL in the schema). These come from the ARP scanner
                # (self.devices) or from the packet capture (device_bytes).
                self.traffic_repository.save_delta_sample(
                    device_id=device_id,
                    download_delta=download_delta,
                    upload_delta=upload_delta,
                    packets_delta=packets_delta,
                    connections=device_conns,
                    download_speed_bps=int(download_speed),
                    upload_speed_bps=int(upload_speed),
                    mac_address=device.get("mac"),
                    ip_address=device.get("ip"),
                    hostname=device.get("hostname"),
                )

                # Accumulate real, delta-derived network-wide speed for the
                # dashboard / system-status broadcast.
                net_download_bps += download_speed
                net_upload_bps += upload_speed

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

                # Update quota usage and enforce if exceeded
                total_delta = download_delta + upload_delta
                if total_delta > 0:
                    self.quota_engine.update_usage(device_id, total_delta)

                    # Get updated quota info and broadcast
                    quota = self.quota_engine.get_quota(device_id)
                    if quota:
                        asyncio_safe_broadcast({
                            "type": "quota_update",
                            "data": {
                                "device_id": device_id,
                                "quota_bytes": quota.limit_bytes,
                                "quota_used_bytes": quota.used_bytes,
                                "quota_remaining_bytes": quota.remaining_bytes,
                                "usage_percentage": quota.usage_percentage,
                                "quota_enabled": quota.enabled,
                                "quota_exceeded": quota.exceeded,
                            }
                        })

            # After processing every online device, publish the network-wide
            # delta-derived speeds and log once per cycle.
            self._live_speed["download_bps"] = int(net_download_bps)
            self._live_speed["upload_bps"] = int(net_upload_bps)
            total_net_bps = int(net_download_bps) + int(net_upload_bps)
            if total_net_bps > self._peak_live_bps:
                self._peak_live_bps = total_net_bps
            logger.debug(f"Saved traffic samples for {len(self.devices)} devices")
        except Exception as e:
            logger.error(f"Error saving traffic samples: {e}")

    def _attribute_and_save_flow(self, flow):
        """Attribute a flow and save intelligence data using incremental deltas.

        Uses delta accounting so long-lived ACTIVE flows can be attributed
        repeatedly without double-counting. Each call attributes ONLY the bytes
        that have not already been attributed in a previous call.
        """
        try:
            device_id = getattr(flow, 'device_id', None)
            if not device_id:
                return

            # Only attribute traffic we have not already accounted for.
            download_delta = max(0, flow.download_bytes - flow.attributed_download_bytes)
            upload_delta = max(0, flow.upload_bytes - flow.attributed_upload_bytes)
            total_delta = download_delta + upload_delta
            packets_delta = max(0, flow.packets - getattr(flow, 'attributed_packets', 0))

            if total_delta <= 0:
                return

            # Get destination IP and port for attribution
            dest_ip = str(flow.destination_ip)
            dest_port = flow.destination_port
            protocol = flow.protocol

            # Get hour bucket for when this traffic actually flowed.
            now = datetime.now(timezone.utc)
            hour_start = now.replace(minute=0, second=0, microsecond=0)

            # Get SNI from flow (stored during packet processing)
            sni = getattr(flow, 'sni', None)

            # Try to get domain from DNS queries for this destination IP.
            # Correlate by device_id + destination_ip + time window (not just IP).
            # A/AAAA DNS answers stay valid evidence for 60 minutes after the query.
            domain = None
            connection = get_connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT domain FROM dns_queries
                        WHERE device_id = %s
                          AND response_ip = %s
                          AND queried_at >= %s - INTERVAL '60 minutes'
                          AND queried_at <= %s + INTERVAL '5 minutes'
                        ORDER BY queried_at DESC
                        LIMIT 1
                        """,
                        (device_id, dest_ip, flow.started_at, flow.started_at)
                    )
                    row = cursor.fetchone()
                    if row:
                        domain = row[0]
            finally:
                return_connection(connection)

            # Attribute the traffic
            attribution_result = self.attribution.analyze(
                device_id=device_id,
                destination_ip=dest_ip,
                domain=domain,
                sni=sni,
                protocol=protocol,
                port=dest_port,
                bytes_transferred=total_delta
            )

            # Store the resolved domain on flow for reference.
            # Note: Python operator precedence would make the old expression
            # "(domain or matched_rules[0]) if matched_rules else None", which
            # silently DISCARDS a valid DNS-derived domain whenever
            # matched_rules is empty. Resolve explicitly instead.
            flow.domain = domain
            if not flow.domain and attribution_result.matched_rules:
                flow.domain = attribution_result.matched_rules[0]

            # Increment "connections"/"queries" only on the first attribution so
            # long-lived flows do not inflate those counters each cycle.
            conn_inc = 1 if not flow.attributed_once else 0
            queries_inc = 1 if (not flow.attributed_once and domain) else 0

            evidence_list = [
                {
                    "source": e.source,
                    "value": e.value,
                    "weight": e.weight,
                    "confidence": e.confidence,
                    "details": e.details
                }
                for e in attribution_result.evidence
            ]

            # Save attributed application usage with confidence and evidence.
            self.intel_repo.save_app_usage(
                device_id=device_id,
                application=attribution_result.application,
                category=attribution_result.category,
                confidence=attribution_result.confidence,
                hour_start=hour_start,
                download_bytes=download_delta,
                upload_bytes=upload_delta,
                connections=conn_inc,
                evidence=evidence_list
            )
            
            # Save domain usage if we have a domain
            if domain:
                category = self.attribution.get_category_for_domain(domain) or attribution_result.category
                # Use attribution confidence for domain (same as application)
                self.intel_repo.save_domain_usage(
                    device_id=device_id,
                    domain=domain,
                    category=category,
                    hour_start=hour_start,
                    download_bytes=download_delta,
                    upload_bytes=upload_delta,
                    queries=queries_inc,
                    connections=conn_inc,
                    confidence=attribution_result.confidence,
                    evidence=evidence_list
                )

            # Save SNI observation if available (separate from domain)
            if sni:
                self.intel_repo.save_sni_observation(
                    device_id=device_id,
                    sni=sni,
                    destination_ip=dest_ip,
                    destination_port=dest_port,
                    observed_at=now,
                    bytes_transferred=total_delta
                )

            # Save category usage (with confidence from attribution)
            self.intel_repo.save_category_usage(
                device_id=device_id,
                category=attribution_result.category,
                hour_start=hour_start,
                download_bytes=download_delta,
                upload_bytes=upload_delta,
                connections=conn_inc
            )

            # Save protocol usage
            self.intel_repo.save_protocol_usage(
                device_id=device_id,
                protocol=protocol,
                hour_start=hour_start,
                download_bytes=download_delta,
                upload_bytes=upload_delta,
                packets=packets_delta,
                connections=conn_inc
            )

            # Track peak speeds - use attribution_elapsed() for correct instantaneous speed
            # speed_bps = delta_bytes * 8 / elapsed_seconds (elapsed since last attribution)
            elapsed = flow.attribution_elapsed()
            download_speed = int((download_delta * 8) / elapsed) if download_delta > 0 else 0
            upload_speed = int((upload_delta * 8) / elapsed) if upload_delta > 0 else 0
            total_speed = download_speed + upload_speed

            self.intel_repo.save_peak(device_id, 'download_speed', download_speed, now)
            self.intel_repo.save_peak(device_id, 'upload_speed', upload_speed, now)
            self.intel_repo.save_peak(device_id, 'total_speed', total_speed, now)
            # Also track connections peak (using connections count for this delta)
            if conn_inc > 0:
                self.intel_repo.save_peak(device_id, 'connections', conn_inc, now)

            # Save activity timeline (mark hour as active)
            self.intel_repo.save_activity_timeline(
                device_id=device_id,
                hour_start=hour_start,
                is_active=True,
                total_bytes=total_delta,
                connections=conn_inc
            )

            # Mark this delta + flow as attributed so we never double count.
            flow.attributed_download_bytes += download_delta
            flow.attributed_upload_bytes += upload_delta
            flow.attributed_packets = getattr(flow, 'attributed_packets', 0) + packets_delta
            flow.attributed_once = True
            # Update last_attributed_at for next cycle's speed calculation
            flow.last_attributed_at = now
            
            # Broadcast intelligence updates for real-time UI
            asyncio_safe_broadcast({
                "type": "intelligence_update",
                "data": {
                    "device_id": device_id,
                    "application": attribution_result.application,
                    "category": attribution_result.category,
                    "confidence": attribution_result.confidence,
                    "domain": domain,
                    "sni": sni,
                    "protocol": protocol,
                    "download_bytes": download_delta,
                    "upload_bytes": upload_delta,
                    "total_bytes": total_delta,
                    "connections": conn_inc,
                }
            })
        
        except Exception as e:
            import traceback
            logger.error(f"Error attributing flow: {e}\n{traceback.format_exc()}")
    
    def cleanup_flows(self):
        """Periodically clean up old flows"""
        try:
            closed_flows = self.flow_manager.cleanup()
            
            for flow in closed_flows:
                try:
                    self.flow_repository.save_flow(flow)
                    
                    # Attribute and save intelligence data
                    self._attribute_and_save_flow(flow)
                    
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

    def attribute_active_flows(self):
        """Attribute long-lived ACTIVE flows using incremental delta accounting.

        Long-lived flows (e.g. an active YouTube/Google session) may never close
        during the observation window, so waiting for them to close keeps the
        Applications/Domains/Categories/Protocols tabs stale or empty. This
        periodically attributes only the bytes accumulated since the last pass,
        so the intelligence tables stay fresh without double counting.
        """
        try:
            for flow in self.flow_manager.flows.values():
                if not getattr(flow, 'device_id', None):
                    continue
                if getattr(flow, 'state', 'ACTIVE') != 'ACTIVE':
                    continue
                download_delta = max(0, flow.download_bytes - flow.attributed_download_bytes)
                upload_delta = max(0, flow.upload_bytes - flow.attributed_upload_bytes)
                if download_delta + upload_delta <= 0:
                    continue
                try:
                    self._attribute_and_save_flow(flow)
                except Exception as e:
                    logger.error(f"Error attributing active flow: {e}")
        except Exception as e:
            logger.error(f"Error attributing active flows: {e}")

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