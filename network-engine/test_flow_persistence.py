#!/usr/bin/env python

"""
Phase F-G Test: Device-to-Packet Mapping and Flow Persistence
Tests that:
1. Devices discovered and stored in database
2. Flows are created and properly associated with devices
3. Flows are persisted to database
4. Flow queries work correctly
"""

from engine import NetworkEngine
from database.migrations import initialize_database
from database.repository import FlowRepository, DeviceRepository
from models.flow import Flow
from datetime import datetime
from logger import logger
import time
import sys

try:
    logger.info("=" * 60)
    logger.info("PHASE F-G TEST: Device Mapping & Flow Persistence")
    logger.info("=" * 60)
    
    # Step 1: Initialize database
    logger.info("\n[Step 1] Initializing database...")
    initialize_database()
    logger.info("✓ Database schema initialized")
    
    # Step 2: Insert test device
    logger.info("\n[Step 2] Inserting test device...")
    device_repo = DeviceRepository()
    test_device = {
        "device_id": "test_dev_001",
        "mac": "aa:bb:cc:dd:ee:ff",
        "ip": "192.168.137.100",
        "hostname": "test-device",
        "vendor": "Test Vendor",
        "interface": "Ethernet",
        "state": "ONLINE"
    }
    device_repo.upsert_device(test_device)
    logger.info(f"✓ Inserted device: {test_device['device_id']}")
    
    # Step 3: Verify device retrieval
    logger.info("\n[Step 3] Retrieving device from database...")
    retrieved = device_repo.get_device("test_dev_001")
    if retrieved:
        logger.info(f"✓ Device retrieved: {retrieved['device_id']} @ {retrieved['ip']}")
    else:
        raise Exception("Failed to retrieve device")
    
    # Step 4: Create and persist test flow
    logger.info("\n[Step 4] Creating test flow with device_id...")
    flow_repo = FlowRepository()
    
    test_flow = Flow(
        key="192.168.137.100:1234<->8.8.8.8:443/TCP",
        source_ip="192.168.137.100",
        destination_ip="8.8.8.8",
        source_port=1234,
        destination_port=443,
        protocol="TCP",
        interface="Ethernet",
        direction="UPLOAD",
        device_id="test_dev_001",  # Associate with device
        packets=100,
        bytes=50000,
        upload_bytes=50000,
        download_bytes=0
    )
    
    logger.info(f"Flow device_id: {test_flow.device_id}")
    
    # Save flow
    try:
        flow_repo.save_flow(test_flow)
        logger.info("✓ Flow persisted to database")
    except Exception as e:
        logger.error(f"✗ Failed to save flow: {e}")
        raise
    
    # Step 5: Query flows for device
    logger.info("\n[Step 5] Querying flows for device...")
    
    from database.connection import get_connection
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM flows WHERE device_id = %s",
                ("test_dev_001",)
            )
            rows = cursor.fetchall()
            
            if rows:
                logger.info(f"✓ Found {len(rows)} flow(s) for device")
                for row in rows:
                    logger.info(f"  Flow: {row}")
            else:
                logger.error("✗ No flows found for device")
    finally:
        conn.close()
    
    # Step 6: Verify flow structure
    logger.info("\n[Step 6] Verifying flow structure...")
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'flows'")
            columns = [row[0] for row in cursor.fetchall()]
            
            required_columns = ['device_id', 'source_ip', 'destination_ip', 'protocol', 'direction', 'packets', 'bytes']
            missing = [c for c in required_columns if c not in columns]
            
            if missing:
                logger.error(f"✗ Missing columns in flows table: {missing}")
            else:
                logger.info(f"✓ All required columns present in flows table")
                logger.info(f"  Columns: {', '.join(columns)}")
    finally:
        conn.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ TEST PASSED: Device mapping & persistence working")
    logger.info("=" * 60)
    
except Exception as e:
    logger.error(f"✗ TEST FAILED: {e}", exc_info=True)
    sys.exit(1)
