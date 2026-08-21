#!/usr/bin/env python

"""
Integration Test: Full Data Pipeline
Tests:
1. Database initialization
2. Device discovery and persistence
3. Flow creation and device association
4. Flow persistence to database
5. Traffic sampling
6. Query and verification of complete pipeline
"""

from engine import NetworkEngine
from database.migrations import initialize_database
from database.repository import DeviceRepository, FlowRepository, TrafficRepository
from models.flow import Flow
from datetime import datetime
from logger import logger
import sys

def run_pipeline_test():
    """Run full pipeline test"""
    
    try:
        logger.info("=" * 70)
        logger.info("INTEGRATION TEST: Full Data Pipeline")
        logger.info("=" * 70)
        
        # Step 1: Database setup
        logger.info("\n[Step 1] Database Setup...")
        initialize_database()
        logger.info("✓ Database schema initialized")
        
        repos = {
            "device": DeviceRepository(),
            "flow": FlowRepository(),
            "traffic": TrafficRepository(),
        }
        
        # Step 2: Insert multiple test devices
        logger.info("\n[Step 2] Inserting test devices...")
        devices = [
            {
                "device_id": "dev_laptop",
                "mac": "aa:bb:cc:dd:ee:01",
                "ip": "192.168.137.100",
                "hostname": "laptop",
                "vendor": "Dell",
                "interface": "Ethernet",
                "state": "ONLINE"
            },
            {
                "device_id": "dev_phone",
                "mac": "aa:bb:cc:dd:ee:02",
                "ip": "192.168.137.101",
                "hostname": "phone",
                "vendor": "Apple",
                "interface": "Ethernet",
                "state": "ONLINE"
            },
            {
                "device_id": "dev_printer",
                "mac": "aa:bb:cc:dd:ee:03",
                "ip": "192.168.137.102",
                "hostname": "printer",
                "vendor": "HP",
                "interface": "Ethernet",
                "state": "ONLINE"
            },
        ]
        
        for device in devices:
            repos["device"].upsert_device(device)
        logger.info(f"✓ Inserted {len(devices)} devices")
        
        # Step 3: Create flows for each device
        logger.info("\n[Step 3] Creating flows for devices...")
        flows_created = 0
        for device in devices:
            # Create 2 flows per device
            for i in range(2):
                flow = Flow(
                    key=f"{device['ip']}:100{i}<->8.8.8.{i}/TCP",
                    source_ip=device["ip"],
                    destination_ip=f"8.8.8.{i}",
                    source_port=1000 + i,
                    destination_port=443,
                    protocol="TCP",
                    interface="Ethernet",
                    direction="UPLOAD",
                    device_id=device["device_id"],
                    packets=100 + i,
                    bytes=50000 + (i * 1000),
                    upload_bytes=50000 + (i * 1000),
                    download_bytes=0
                )
                repos["flow"].save_flow(flow)
                flows_created += 1
        
        logger.info(f"✓ Created and persisted {flows_created} flows")
        
        # Step 4: Save traffic samples
        logger.info("\n[Step 4] Saving traffic samples...")
        for device in devices:
            repos["traffic"].save_sample(
                device_id=device["device_id"],
                download_bytes=10000,
                upload_bytes=5000,
                packets=1000,
                connections=5
            )
        logger.info(f"✓ Saved traffic samples for {len(devices)} devices")
        
        # Step 5: Verify device retrieval
        logger.info("\n[Step 5] Verifying device retrieval...")
        for device in devices:
            retrieved = repos["device"].get_device(device["device_id"])
            if not retrieved:
                raise Exception(f"Failed to retrieve device {device['device_id']}")
        logger.info(f"✓ All {len(devices)} devices retrieved successfully")
        
        # Step 6: Verify flow queries
        logger.info("\n[Step 6] Verifying flow queries...")
        from database.connection import get_connection
        
        total_flows_in_db = 0
        for device in devices:
            conn = get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM flows WHERE device_id = %s",
                        (device["device_id"],)
                    )
                    count = cursor.fetchone()[0]
                    logger.info(f"  {device['device_id']}: {count} flows")
                    total_flows_in_db += count
            finally:
                conn.close()
        
        if total_flows_in_db == flows_created:
            logger.info(f"✓ All {total_flows_in_db} flows retrieved successfully")
        else:
            raise Exception(f"Flow count mismatch: {total_flows_in_db} != {flows_created}")
        
        # Step 7: Verify traffic samples
        logger.info("\n[Step 7] Verifying traffic samples...")
        samples_found = 0
        for device in devices:
            samples = repos["traffic"].get_recent_samples(device["device_id"], hours=1)
            if samples:
                samples_found += len(samples)
                logger.info(f"  {device['device_id']}: {len(samples)} samples")
        
        logger.info(f"✓ Found {samples_found} total traffic samples")
        
        # Step 8: Advanced queries
        logger.info("\n[Step 8] Running advanced queries...")
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                # Query: Total bandwidth per device
                cursor.execute("""
                    SELECT device_id, SUM(bytes) as total_bytes, COUNT(*) as flow_count
                    FROM flows
                    GROUP BY device_id
                    ORDER BY total_bytes DESC
                """)
                logger.info("  Top devices by bandwidth:")
                for row in cursor.fetchall():
                    logger.info(f"    {row[0]}: {row[1]} bytes ({row[2]} flows)")
                
                # Query: Protocol distribution
                cursor.execute("""
                    SELECT protocol, COUNT(*) as count
                    FROM flows
                    GROUP BY protocol
                """)
                logger.info("  Protocol distribution:")
                for row in cursor.fetchall():
                    logger.info(f"    {row[0]}: {row[1]} flows")
        finally:
            conn.close()
        
        logger.info("\n" + "=" * 70)
        logger.info("✓ INTEGRATION TEST PASSED")
        logger.info("=" * 70)
        logger.info(f"\nSummary:")
        logger.info(f"  - {len(devices)} devices created")
        logger.info(f"  - {flows_created} flows persisted")
        logger.info(f"  - {samples_found} traffic samples recorded")
        logger.info(f"  - All queries executed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST FAILED: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = run_pipeline_test()
    sys.exit(0 if success else 1)
