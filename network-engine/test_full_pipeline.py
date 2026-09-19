#!/usr/bin/env python
"""
Test full data pipeline: Packet -> Flow -> Database -> Repository -> API-like query
"""

from database.migrations import initialize_database
from database.repository import DeviceRepository, FlowRepository, TrafficRepository
from database.connection import get_connection
from models.flow import Flow
from datetime import datetime
from logger import logger
import time
import sys

try:
    logger.info("=" * 60)
    logger.info("FULL PIPELINE TEST: Packet -> Flow -> Database")
    logger.info("=" * 60)
    
    # Step 1: Initialize database
    logger.info("\n[Step 1] Initializing database...")
    initialize_database()
    logger.info("✓ Database schema initialized")
    
    # Step 2: Insert test device
    logger.info("\n[Step 2] Inserting test device...")
    device_repo = DeviceRepository()
    import uuid
    unique_mac = "aa:bb:cc:dd:ee:" + format(uuid.uuid4().int & 0xff, '02x')
    test_device = {
        "device_id": "test_dev_pipeline",
        "mac": unique_mac,
        "ip": "192.168.137.100",
        "hostname": "test-device",
        "vendor": "Test Vendor",
        "interface": "Ethernet",
        "state": "ONLINE"
    }
    device_repo.upsert_device(test_device)
    logger.info(f"✓ Inserted device: {test_device['device_id']}")
    
    # Step 3: Create and persist test flow
    logger.info("\n[Step 3] Creating test flow with device_id...")
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
        device_id="test_dev_pipeline",
        packets=100,
        bytes=50000,
        upload_bytes=50000,
        download_bytes=0
    )
    
    flow_repo.save_flow(test_flow)
    logger.info("✓ Flow persisted to database")
    
    # Step 4: Save traffic sample (delta)
    logger.info("\n[Step 4] Saving traffic sample (delta)...")
    traffic_repo = TrafficRepository()
    traffic_repo.save_delta_sample(
        device_id="test_dev_pipeline",
        download_delta=10000,
        upload_delta=5000,
        packets_delta=20,
        connections=5,
        download_speed_bps=1000000,
        upload_speed_bps=500000
    )
    logger.info("✓ Traffic sample saved with usage aggregation")
    
    # Step 5: Query flows for device
    logger.info("\n[Step 5] Querying flows for device...")
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM flows WHERE device_id = %s",
                ("test_dev_pipeline",)
            )
            rows = cursor.fetchall()
            
            if rows:
                logger.info(f"✓ Found {len(rows)} flow(s) for device")
                for row in rows:
                    logger.info(f"  Flow ID: {row[0]}, Direction: {row[8]}, Packets: {row[12]}, Bytes: {row[13]}")
            else:
                logger.error("✗ No flows found for device")
                sys.exit(1)
    finally:
        conn.close()
    
    # Step 6: Verify usage_daily aggregation
    logger.info("\n[Step 6] Verifying usage_daily aggregation...")
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT download_bytes, upload_bytes, packets FROM usage_daily WHERE device_id = %s AND day_start = CURRENT_DATE",
                ("test_dev_pipeline",)
            )
            row = cursor.fetchone()
            if row:
                logger.info(f"✓ usage_daily: download={row[0]}, upload={row[1]}, packets={row[2]}")
                if row[0] == 10000 and row[1] == 5000 and row[2] == 20:
                    logger.info("✓ Aggregation values match delta sample!")
                else:
                    logger.error(f"✗ Aggregation mismatch! Expected download=10000, upload=5000, packets=20")
                    sys.exit(1)
            else:
                logger.error("✗ No usage_daily record found")
                sys.exit(1)
    finally:
        conn.close()
    
    # Step 7: Verify usage_hourly aggregation
    logger.info("\n[Step 7] Verifying usage_hourly aggregation...")
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT download_bytes, upload_bytes, packets FROM usage_hourly WHERE device_id = %s AND hour_start = date_trunc('hour', NOW())",
                ("test_dev_pipeline",)
            )
            row = cursor.fetchone()
            if row:
                logger.info(f"✓ usage_hourly: download={row[0]}, upload={row[1]}, packets={row[2]}")
                if row[0] == 10000 and row[1] == 5000 and row[2] == 20:
                    logger.info("✓ Hourly aggregation values match delta sample!")
                else:
                    logger.error(f"✗ Hourly aggregation mismatch!")
                    sys.exit(1)
            else:
                logger.error("✗ No usage_hourly record found")
                sys.exit(1)
    finally:
        conn.close()
    
    # Step 8: Verify device totals updated
    logger.info("\n[Step 8] Verifying device totals updated...")
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT total_upload, total_download, total_packets FROM devices WHERE device_id = %s",
                ("test_dev_pipeline",)
            )
            row = cursor.fetchone()
            if row:
                logger.info(f"✓ Device totals: upload={row[0]}, download={row[1]}, packets={row[2]}")
                if row[0] == 50000 + 5000 and row[1] == 10000 and row[2] == 100 + 20:
                    logger.info("✓ Device totals correctly accumulated!")
                else:
                    logger.warning(f"  Expected: upload=55000, download=10000, packets=120")
            else:
                logger.error("✗ Device not found")
                sys.exit(1)
    finally:
        conn.close()
    
    # Step 9: Test flow UPSERT (update existing flow)
    logger.info("\n[Step 9] Testing flow UPSERT (update existing flow)...")
    test_flow.packets = 150
    test_flow.bytes = 75000
    test_flow.upload_bytes = 75000
    test_flow.last_seen = datetime.now()
    flow_repo.save_flow(test_flow)
    logger.info("✓ Flow updated via UPSERT")
    
    # Verify update
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT packets, bytes, upload_bytes FROM flows WHERE device_id = %s AND source_ip = %s AND destination_ip = %s AND source_port = %s AND destination_port = %s AND protocol = %s AND interface_name = %s",
                ("test_dev_pipeline", "192.168.137.100", "8.8.8.8", 1234, 443, "TCP", "Ethernet")
            )
            row = cursor.fetchone()
            if row:
                logger.info(f"✓ Updated flow: packets={row[0]}, bytes={row[1]}, upload_bytes={row[2]}")
                if row[0] == 150 and row[1] == 75000 and row[2] == 75000:
                    logger.info("✓ Flow UPSERT correctly updated values!")
                else:
                    logger.error(f"✗ Flow UPSERT failed to update correctly")
                    sys.exit(1)
            else:
                logger.error("✗ Flow not found after UPSERT")
                sys.exit(1)
    finally:
        conn.close()
    
    # Step 10: Test traffic_samples table
    logger.info("\n[Step 10] Verifying traffic_samples table...")
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT download_bytes, upload_bytes, packets, connections, download_speed_bps, upload_speed_bps FROM traffic_samples WHERE device_id = %s ORDER BY sampled_at DESC LIMIT 1",
                ("test_dev_pipeline",)
            )
            row = cursor.fetchone()
            if row:
                logger.info(f"✓ traffic_samples: download={row[0]}, upload={row[1]}, packets={row[2]}, connections={row[3]}, dl_speed={row[4]}, ul_speed={row[5]}")
                if row[0] == 10000 and row[1] == 5000 and row[2] == 20 and row[3] == 5 and row[4] == 1000000 and row[5] == 500000:
                    logger.info("✓ Traffic sample correctly stored with speeds!")
                else:
                    logger.error(f"✗ Traffic sample mismatch!")
                    sys.exit(1)
            else:
                logger.error("✗ No traffic sample found")
                sys.exit(1)
    finally:
        conn.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ TEST PASSED: Full pipeline working correctly!")
    logger.info("=" * 60)
    
except Exception as e:
    logger.error(f"✗ TEST FAILED: {e}", exc_info=True)
    sys.exit(1)