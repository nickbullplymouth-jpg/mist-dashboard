import os
from typing import Dict, Any, List, Optional
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

MIST_HOST = os.getenv("MIST_HOST", "api.eu.mist.com")
MIST_API_TOKEN = os.getenv("MIST_API_TOKEN", "")
MIST_ORG_ID = os.getenv("MIST_ORG_ID", "")

app = FastAPI(
    title="Mist Org Stats & Monitoring Dashboard",
    description="Real-time Juniper Mist Org Monitoring & Statistics API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_mist_headers() -> Dict[str, str]:
    if not MIST_API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="MIST_API_TOKEN is not configured. Please set it in your .env file."
        )
    return {
        "Authorization": f"Token {MIST_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

async def fetch_mist_endpoint(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
    url = f"https://{MIST_HOST}/api/v1{endpoint}"
    headers = get_mist_headers()
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Unauthorized: Check your Mist API Token.")
            elif response.status_code == 403:
                raise HTTPException(status_code=403, detail="Forbidden: Insufficient privileges on Mist Org.")
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail="Resource not found on Mist Cloud.")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Error connecting to Mist API: {str(exc)}")

@app.get("/api/config")
async def get_config():
    """Returns basic non-sensitive config status"""
    return {
        "host": MIST_HOST,
        "org_id": MIST_ORG_ID,
        "token_configured": bool(MIST_API_TOKEN)
    }

@app.get("/api/org")
async def get_org_details():
    """Get current Mist Organization details"""
    if not MIST_ORG_ID:
        raise HTTPException(status_code=400, detail="MIST_ORG_ID is not configured in .env")
    return await fetch_mist_endpoint(f"/orgs/{MIST_ORG_ID}")

@app.get("/api/stats")
async def get_org_stats():
    """Get summarized high-level statistics for the Organization"""
    if not MIST_ORG_ID:
        raise HTTPException(status_code=400, detail="MIST_ORG_ID is not configured in .env")
    
    # Run requests concurrently or gather key resources
    try:
        sites = await fetch_mist_endpoint(f"/orgs/{MIST_ORG_ID}/sites")
    except Exception:
        sites = []

    try:
        device_stats = await fetch_mist_endpoint(f"/orgs/{MIST_ORG_ID}/stats/devices")
    except Exception:
        device_stats = []

    try:
        client_stats = await fetch_mist_endpoint(f"/orgs/{MIST_ORG_ID}/stats/clients")
    except Exception:
        client_stats = []

    try:
        alarms = await fetch_mist_endpoint(f"/orgs/{MIST_ORG_ID}/alarms", params={"limit": 10})
    except Exception:
        alarms = []

    # Calculate aggregate numbers
    total_aps = len(device_stats)
    aps_connected = sum(1 for d in device_stats if d.get("status") == "connected")
    aps_disconnected = total_aps - aps_connected

    # Clients count & split
    total_clients = len(client_stats) if isinstance(client_stats, list) else 0

    return {
        "org_id": MIST_ORG_ID,
        "sites_count": len(sites) if isinstance(sites, list) else 0,
        "devices": {
            "total": total_aps,
            "connected": aps_connected,
            "disconnected": aps_disconnected,
            "list": device_stats[:50]  # top 50 devices
        },
        "clients": {
            "total": total_clients,
            "list": client_stats[:50]
        },
        "alarms": alarms if isinstance(alarms, list) else alarms.get("results", [])
    }

@app.get("/api/sites")
async def get_sites():
    """Get all sites for the organization"""
    if not MIST_ORG_ID:
        raise HTTPException(status_code=400, detail="MIST_ORG_ID is not configured in .env")
    return await fetch_mist_endpoint(f"/orgs/{MIST_ORG_ID}/sites")

@app.get("/api/devices")
async def get_devices():
    """Get device inventory & statuses (APs, Switches, Gateways)"""
    if not MIST_ORG_ID:
        raise HTTPException(status_code=400, detail="MIST_ORG_ID is not configured in .env")
    return await fetch_mist_endpoint(f"/orgs/{MIST_ORG_ID}/stats/devices")

@app.get("/api/clients")
async def get_clients(limit: int = Query(default=100, le=500)):
    """Get wireless clients connected across the organization"""
    if not MIST_ORG_ID:
        raise HTTPException(status_code=400, detail="MIST_ORG_ID is not configured in .env")
    return await fetch_mist_endpoint(f"/orgs/{MIST_ORG_ID}/stats/clients", params={"limit": limit})

@app.get("/api/sle")
async def get_sle_metrics(scope: str = Query(default="wifi")):
    """Get Service Level Expectations (SLE) overview"""
    if not MIST_ORG_ID:
        raise HTTPException(status_code=400, detail="MIST_ORG_ID is not configured in .env")
    return await fetch_mist_endpoint(f"/orgs/{MIST_ORG_ID}/insights/sle", params={"scope": scope})

# Mount static frontend directory
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "Mist Dashboard API is running. Build UI in /static to display."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
