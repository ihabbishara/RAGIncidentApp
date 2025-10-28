"""Unified mock app entry point that can run either Confluence or ServiceNow mock."""

import os
import sys

# Get service type from environment variable
service_type = os.getenv("SERVICE_TYPE", "confluence").lower()
port = int(os.getenv("PORT", "8000"))

if service_type == "confluence":
    from src.mocks.confluence_mock import app
    print(f"Starting Confluence Mock API on port {port}")
elif service_type == "servicenow":
    from src.mocks.servicenow_mock import app
    print(f"Starting ServiceNow Mock API on port {port}")
else:
    print(f"Unknown SERVICE_TYPE: {service_type}")
    print("Valid values: confluence, servicenow")
    sys.exit(1)

# App is exported for uvicorn to use
__all__ = ["app"]
