#!/usr/bin/env python
"""
Wrapper script to run the API server with proper module path
"""
import sys
import os

# Add network-engine to path so relative imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'network-engine'))

# Now we can import and run uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )
