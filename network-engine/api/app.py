from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from ipaddress import IPv4Address, IPv6Address
import json
from typing import Optional

# Custom JSON encoder to handle IPv4Address/IPv6Address
class IPAddressEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (IPv4Address, IPv6Address)):
            return str(obj)
        return super().default(obj)

# Override FastAPI's jsonable_encoder
original_jsonable_encoder = jsonable_encoder

def custom_jsonable_encoder(obj, **kwargs):
    if isinstance(obj, (IPv4Address, IPv6Address)):
        return str(obj)
    if isinstance(obj, dict):
        return {k: custom_jsonable_encoder(v, **kwargs) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [custom_jsonable_encoder(item, **kwargs) for item in obj]
    return original_jsonable_encoder(obj, **kwargs)

from api.routes.alerts import router as alerts_router
from api.routes.analytics import router as analytics_router
from api.routes.applications import router as applications_router
from api.routes.auth import router as auth_router
from api.routes.control import router as control_router
from api.routes.data_management import router as data_management_router
from api.routes.devices import router as devices_router
from api.routes.dns import router as dns_router
from api.routes.flows import router as flows_router
from api.routes.reports import router as reports_router
from api.routes.system import router as system_router
from api.routes.traffic import router as traffic_router
from api.websocket import websocket_endpoint

app = FastAPI(
    title="Network Control API",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تسجيل جميع مسارات الـ API مع إضافة Tags لتنظيم Swagger UI
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(devices_router, prefix="/api/devices", tags=["Devices"])
app.include_router(traffic_router, prefix="/api/traffic", tags=["Traffic"])
app.include_router(flows_router, prefix="/api/flows", tags=["Flows"])
app.include_router(dns_router, prefix="/api/dns", tags=["DNS"])
app.include_router(applications_router, prefix="/api/applications", tags=["Applications"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(control_router, prefix="/api/control", tags=["Control"])
app.include_router(data_management_router, prefix="/api/data-management", tags=["Data Management"])
app.include_router(system_router, prefix="/api/system", tags=["System"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])


@app.get("/api/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "service": "network-control-api",
    }


@app.websocket("/ws")
async def websocket_route(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    await websocket_endpoint(websocket, token)
