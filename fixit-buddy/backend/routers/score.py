from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# Mock device database (replace with real DB queries later)
DEVICES = {
    "iphone15pro": {"brand":"Apple","model":"iPhone 15 Pro","score":6.5,"grade":"B","msrp":1199,
        "note":"Self-repair program available. Battery and display are easiest to fix."},
    "galaxys23":   {"brand":"Samsung","model":"Galaxy S23","score":5.8,"grade":"C","msrp":849,
        "note":"Parts program expanding in EU. Battery needs heat to remove."},
    "fairphone5":  {"brand":"Fairphone","model":"Fairphone 5","score":9.3,"grade":"A","msrp":699,
        "note":"Gold standard of repairability — every module snaps off without tools."},
    "macbookairm2":{"brand":"Apple","model":"MacBook Air M2","score":2.9,"grade":"E","msrp":1299,
        "note":"RAM and SSD are soldered. Complex disassembly required."},
    "dellxps13":   {"brand":"Dell","model":"Dell XPS 13","score":7.2,"grade":"B","msrp":999,
        "note":"Official service manuals available. SSD is user-upgradeable."},
}

class ScoreResponse(BaseModel):
    brand: str
    model: str
    score: float
    grade: str
    msrp: float
    price_cap_30pct: float
    note: str

@router.get("/search")
def search_devices(q: str = ""):
    """Search devices by name"""
    results = []
    for key, d in DEVICES.items():
        if q.lower() in d["model"].lower() or q.lower() in d["brand"].lower():
            results.append({"id": key, **d})
    return results

@router.get("/{device_id}", response_model=ScoreResponse)
def get_score(device_id: str):
    """Get repairability score for a device"""
    d = DEVICES.get(device_id)
    if not d:
        return {"error": "Device not found"}
    return ScoreResponse(
        brand=d["brand"], model=d["model"],
        score=d["score"], grade=d["grade"],
        msrp=d["msrp"],
        price_cap_30pct=round(d["msrp"] * 0.3, 2),
        note=d["note"]
    )
