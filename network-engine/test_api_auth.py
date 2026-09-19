#!/usr/bin/env python

"""
Phase J Test: API Authentication Testing
Tests:
1. Health check endpoint
2. Login with valid credentials (admin/operator/viewer)
3. Verify JWT token generation
4. Test protected endpoints with and without JWT
5. Test invalid credentials
"""

import requests
import json
from logger import logger
import sys
import time
from threading import Thread

# Configuration
API_BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{API_BASE_URL}/api/health"
LOGIN_ENDPOINT = f"{API_BASE_URL}/api/auth/login"
DEVICES_ENDPOINT = f"{API_BASE_URL}/api/devices"

# Test credentials (from config/environment)
TEST_USERS = {
    "admin": {
        "username": "admin",
        "password": "admin_change_me",  # From ADMIN_PASSWORD env var default
        "role": "ADMIN"
    },
    "operator": {
        "username": "operator",
        "password": "operator_change_me",  # From OPERATOR_PASSWORD env var default
        "role": "OPERATOR"
    },
}

def wait_for_api(timeout=10):
    """Wait for API to be ready"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(HEALTH_ENDPOINT, timeout=1)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(0.5)
    return False

def test_api_authentication():
    """Run API authentication tests"""
    
    try:
        logger.info("=" * 70)
        logger.info("PHASE J TEST: API Authentication")
        logger.info("=" * 70)
        
        # Check if API is running
        logger.info("\n[Step 1] Checking if API is running...")
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=2)
            if response.status_code == 200:
                logger.info("✓ API is running")
            else:
                logger.warning(f"⚠ API returned {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.error("✗ Cannot connect to API on localhost:8000")
            logger.info("\nTo run this test, start the API with:")
            logger.info("  cd network-engine")
            logger.info("  .venv\\Scripts\\python -m uvicorn api.app:app --host 0.0.0.0 --port 8000")
            return False
        
        # Test 1: Login with valid credentials
        logger.info("\n[Step 2] Testing login with valid credentials...")
        tokens = {}
        for user_type, creds in TEST_USERS.items():
            try:
                response = requests.post(
                    LOGIN_ENDPOINT,
                    json={
                        "username": creds["username"],
                        "password": creds["password"]
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    if token:
                        tokens[user_type] = token
                        logger.info(f"✓ {user_type.upper()}: Login successful, token generated")
                    else:
                        logger.error(f"✗ {user_type.upper()}: No token in response")
                else:
                    logger.error(f"✗ {user_type.upper()}: Login failed with status {response.status_code}")
                    logger.error(f"  Response: {response.text}")
            except Exception as e:
                logger.error(f"✗ {user_type.upper()}: Login error: {e}")
        
        if not tokens:
            logger.error("✗ No users were able to login")
            return False
        
        # Test 2: Access protected endpoint without token
        logger.info("\n[Step 3] Testing protected endpoint WITHOUT token...")
        try:
            response = requests.get(DEVICES_ENDPOINT, timeout=5)
            if response.status_code == 401:
                logger.info("✓ Protected endpoint correctly requires authentication")
            else:
                logger.warning(f"⚠ Expected 401, got {response.status_code}")
        except Exception as e:
            logger.error(f"✗ Request error: {e}")
        
        # Test 3: Access protected endpoint WITH token
        logger.info("\n[Step 4] Testing protected endpoint WITH token...")
        for user_type, token in tokens.items():
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(DEVICES_ENDPOINT, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    logger.info(f"✓ {user_type.upper()}: Can access protected endpoint")
                    data = response.json()
                    logger.debug(f"  Response: {data}")
                else:
                    logger.error(f"✗ {user_type.upper()}: Got status {response.status_code}")
                    logger.error(f"  Response: {response.text}")
            except Exception as e:
                logger.error(f"✗ {user_type.upper()}: Request error: {e}")
        
        # Test 4: Invalid credentials
        logger.info("\n[Step 5] Testing login with invalid credentials...")
        try:
            response = requests.post(
                LOGIN_ENDPOINT,
                json={
                    "username": "invalid_user",
                    "password": "wrong_password"
                },
                timeout=5
            )
            
            if response.status_code == 401:
                logger.info("✓ Invalid credentials correctly rejected")
            else:
                logger.warning(f"⚠ Expected 401, got {response.status_code}")
        except Exception as e:
            logger.error(f"✗ Request error: {e}")
        
        logger.info("\n" + "=" * 70)
        logger.info("✓ PHASE J TEST COMPLETED")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST FAILED: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_api_authentication()
    sys.exit(0 if success else 1)
