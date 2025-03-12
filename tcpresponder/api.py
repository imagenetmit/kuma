from fastapi import FastAPI, HTTPException
from db_manager import DatabaseManager, IPConfig
from pydantic import BaseModel
from typing import List

app = FastAPI()
db_manager = DatabaseManager()

class IPConfigRequest(BaseModel):
    ip_address: str
    device_name: str
    client_name: str
    location_name: str
    is_static_ip: bool
    push_url: str

@app.post("/ip", status_code=201)
async def add_ip(ip_config: IPConfigRequest):
    try:
        db_config = IPConfig(**ip_config.dict())
        db_manager.add_ip(db_config)
        return {"message": "IP configuration added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/ip", response_model=List[IPConfigRequest])
async def get_ips():
    return db_manager.get_all_ips()

@app.get("/ip/{ip_address}")
async def get_ip(ip_address: str):
    ip_config = db_manager.get_ip_details(ip_address)
    if not ip_config:
        raise HTTPException(status_code=404, detail="IP configuration not found")
    return ip_config

@app.delete("/ip/{ip_address}")
async def delete_ip(ip_address: str):
    if not db_manager.is_ip_allowed(ip_address):
        raise HTTPException(status_code=404, detail="IP configuration not found")
    db_manager.remove_ip(ip_address)
    return {"message": "IP configuration deleted successfully"} 