#!/usr/bin/env python

"""
Simple test to verify engine initialization and discovery loop
"""

from engine import NetworkEngine
from database.migrations import initialize_database
from logger import logger
import time
import signal
import sys

def signal_handler(sig, frame):
    print("\n\n✓ Test interrupted, cleaning up...")
    if engine:
        engine.stop_discovery_loop()
    sys.exit(0)

# Set up signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

try:
    logger.info("=" * 50)
    logger.info("PHASE D TEST: Engine Initialization & Discovery")
    logger.info("=" * 50)
    
    # Step 1: Initialize database
    logger.info("Step 1: Initializing database schema...")
    initialize_database()
    logger.info("✓ Database initialized")
    
    # Step 2: Create and initialize engine
    logger.info("\nStep 2: Initializing NetworkEngine...")
    engine = NetworkEngine()
    logger.info("✓ NetworkEngine initialized")
    
    # Step 3: Perform initial discovery
    logger.info("\nStep 3: Performing initial device discovery...")
    engine.discover_devices()
    logger.info(f"✓ Discovery complete. Found {len(engine.devices)} devices")
    
    # Step 4: Start discovery loop
    logger.info("\nStep 4: Starting continuous discovery loop...")
    engine.start_discovery_loop()
    logger.info("✓ Discovery loop started (daemon thread)")
    
    # Step 5: Wait and observe
    logger.info("\nStep 5: Monitoring discovery loop for 30 seconds...")
    logger.info("(Press Ctrl+C to stop)")
    
    for i in range(30):
        time.sleep(1)
        stats = engine.get_statistics()
        logger.info(f"[{i+1}s] Devices: {stats['devices']}, Online: {stats['devices_online']}")
    
    logger.info("\n" + "=" * 50)
    logger.info("✓ TEST PASSED: Engine running normally")
    logger.info("=" * 50)
    
    # Cleanup
    engine.stop_discovery_loop()
    
except Exception as e:
    logger.error(f"✗ TEST FAILED: {e}", exc_info=True)
    sys.exit(1)
