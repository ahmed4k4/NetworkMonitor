from database.connection import get_connection
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
            connection.close()
            logger.info(f"Loaded {len(self.devices)} existing devices from database")
        except Exception as e:
            logger.warning(f"Could not load existing devices: {e}")

    def normalize_mac(self, mac: str) -> str:
        """Normalize MAC address to uppercase with colons"""
        return mac.upper().replace("-", ":")

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
                    connection.close()
                    return device_id
            connection.close()
        except Exception as e:
            logger.warning(f"Error looking up device in database: {e}")

        # Create new device_id
        self.counter += 1
        device_id = f"dev_{self.counter:03d}"
        self.devices[mac_normalized] = device_id

        logger.info(
            f"Created new device_id: {device_id} for MAC: {mac_normalized}"
        )

        return device_id

    def get_all(self):
        """Return all MAC → device_id mappings"""
        return self.devices.copy()
