from logger import logger
import time

from database.migrations import initialize_database
from database.connection import close_pool

from engine import NetworkEngine


def main():

    logger.info(
        "================================"
    )

    logger.info(
        "      NETWORK ENGINE START"
    )

    logger.info(
        "================================"
    )

    # Initialize database schema
    initialize_database()
    logger.info("Database initialized")

    # Create and configure engine
    engine = NetworkEngine()

    # Perform initial device discovery
    engine.discover_devices()

    # Start continuous discovery loop
    engine.start_discovery_loop()
    logger.info("Device discovery loop started")

    # Start packet capture (blocking)
    try:
        engine.start_capture()
        # Keep main thread alive while capture runs
        while engine.running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        logger.info("Stopping engine...")
        engine.stop_discovery_loop()
        engine.stop_capture()
        close_pool()
        logger.info("Engine stopped")


if __name__ == "__main__":
    main()
