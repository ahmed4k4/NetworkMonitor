from database.connection import get_connection, return_connection
from logger import logger
import uuid


class DeviceIdentityManager:
    """
    Manages persistent device identity mapping.
    MAC address → device_id (persistent across restarts)
    """

    def __init__(self):
        self.devices = {}
        self.counter = 0
        self._load_existing_devices()

    def _load_existing_devices(self):
        """Load existing device mappings from database"""
        connection = None
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT device_id, mac_address FROM devices"
                )
                for row in cursor.fetchall():
                    device_id, mac = row
                    mac_normalized = self.normalize_mac(mac)
                    self.devices[mac_normalized] = device_id
                    # Extract counter to continue from highest
                    try:
                        num = int(device_id.split('_')[1])
                        self.counter = max(self.counter, num)
                    except (ValueError, IndexError):
                        pass
            logger.info(f"Loaded {len(self.devices)} existing devices from database")
        except Exception as e:
            logger.warning(f"Could not load existing devices: {e}")
        finally:
            if connection is not None:
                return_connection(connection)

    def normalize_mac(self, mac: str) -> str:
        """Normalize MAC address to uppercase with colons"""
        mac = mac.upper().replace("-", ":")
        # Handle format without separators (e.g., "AABBCCDDEEFF")
        if ":" not in mac and len(mac) == 12:
            mac = ":".join(mac[i:i+2] for i in range(0, 12, 2))
        return mac

    def get_device_id(self, mac: str) -> str:
        """
        Get or create a device_id for the given MAC address.
        Returns the same device_id for the same MAC (persistent).
        """
        mac_normalized = self.normalize_mac(mac)

        # Check if already in memory
        if mac_normalized in self.devices:
            return self.devices[mac_normalized]

        # Check if in database
        connection = None
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT device_id FROM devices WHERE mac_address = %s",
                    (mac_normalized,)
                )
                result = cursor.fetchone()
                if result:
                    device_id = result[0]
                    self.devices[mac_normalized] = device_id
                    return device_id
        except Exception as e:
            logger.warning(f"Error looking up device in database: {e}")
        finally:
            if connection is not None:
                return_connection(connection)

        # Create new device_id
        self.counter += 1
        device_id = f"dev_{self.counter:03d}"
        self.devices[mac_normalized] = device_id

        # GUARANTEE a devices row exists immediately. Without this, a device
        # whose MAC emitted traffic but that the periodic ARP scan missed would
        # have no devices row, causing traffic_samples/usage_* writes to fail
        # with a FK violation and the whole sample to be rolled back (traffic
        # lost, device invisible to GET /api/devices).
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO devices (
                        device_id, mac_address, state, first_seen, last_seen
                    )
                    VALUES (%s, %s, 'ONLINE', NOW(), NOW())
                    ON CONFLICT (device_id) DO NOTHING
                    """,
                    (device_id, mac_normalized)
                )
            connection.commit()
        except Exception as e:
            logger.warning(f"Could not pre-create devices row for {device_id}: {e}")
        finally:
            if connection is not None:
                return_connection(connection)

        logger.info(
            f"Created new device_id: {device_id} for MAC: {mac_normalized}"
        )

        return device_id

    def get_all(self):
        """Return all MAC → device_id mappings"""
        return self.devices.copy()