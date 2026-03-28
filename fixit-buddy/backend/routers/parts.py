"""
routers/parts.py — EU Spare Parts Optimizer

Implements the EU Right-to-Repair Directive requirement that spare part prices
must not exceed 30% of the device's original retail price (MSRP).

Endpoints:
  GET  /api/parts/{device_id}   — list parts with EU compliance check
  POST /api/parts/check-price   — check any custom price against the cap
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()
logger = logging.getLogger(__name__)

EU_PRICE_CAP_PERCENT = 0.30   # 30% of device MSRP — EU mandate

PARTS_DB: dict = {
    "iphone15pro": {
        "msrp": 1199,
        "parts": [
            {
                "name": "Battery", "part_number": "661-25038",
                "oem_price": 89, "third_party_price": 35,
                "difficulty": "Medium", "time_estimate": "45 min",
                "ifixit_url": "https://www.ifixit.com/Guide/iPhone+15+Pro+Battery+Replacement",
                "tools_needed": ["Pentalobe P2 screwdriver", "Suction cup", "Plastic prying tool"],
            },
            {
                "name": "OLED Display", "part_number": "661-24050",
                "oem_price": 299, "third_party_price": 120,
                "difficulty": "Hard", "time_estimate": "1.5 hours",
                "ifixit_url": "https://www.ifixit.com/Guide/iPhone+15+Pro+Screen+Replacement",
                "tools_needed": ["Pentalobe P2 screwdriver", "Heat gun", "Suction cup", "Spudger"],
            },
            {
                "name": "Back Glass", "part_number": "923-06660",
                "oem_price": 199, "third_party_price": 75,
                "difficulty": "Hard", "time_estimate": "2 hours",
                "ifixit_url": "https://www.ifixit.com/Guide/iPhone+15+Pro+Back+Glass+Replacement",
                "tools_needed": ["Pentalobe P2 screwdriver", "Heat gun", "Adhesive strips"],
            },
            {
                "name": "Charging Port", "part_number": "923-05861",
                "oem_price": 59, "third_party_price": 22,
                "difficulty": "Easy", "time_estimate": "30 min",
                "ifixit_url": "https://www.ifixit.com/Guide/iPhone+15+Pro+USB-C+Port+Replacement",
                "tools_needed": ["Pentalobe P2 screwdriver", "Tri-point Y000 screwdriver"],
            },
        ],
    },
    "galaxys23": {
        "msrp": 849,
        "parts": [
            {
                "name": "Battery", "part_number": "GH82-30627A",
                "oem_price": 65, "third_party_price": 28,
                "difficulty": "Medium", "time_estimate": "1 hour",
                "ifixit_url": "https://www.ifixit.com/Guide/Samsung+Galaxy+S23+Battery+Replacement",
                "tools_needed": ["Phillips #00 screwdriver", "Heat gun", "Plastic prying tool"],
            },
            {
                "name": "Display Assembly", "part_number": "GH82-30633A",
                "oem_price": 219, "third_party_price": 95,
                "difficulty": "Hard", "time_estimate": "1.5 hours",
                "ifixit_url": "https://www.ifixit.com/Guide/Samsung+Galaxy+S23+Screen+Replacement",
                "tools_needed": ["Phillips #00 screwdriver", "Heat gun", "Suction cup"],
            },
            {
                "name": "Rear Camera Module", "part_number": "GH96-15658A",
                "oem_price": 185, "third_party_price": 80,
                "difficulty": "Medium", "time_estimate": "45 min",
                "ifixit_url": "https://www.ifixit.com/Guide/Samsung+Galaxy+S23+Rear+Camera+Replacement",
                "tools_needed": ["Phillips #00 screwdriver", "Tweezers"],
            },
            {
                "name": "USB-C Charging Port", "part_number": "GH82-29937A",
                "oem_price": 35, "third_party_price": 15,
                "difficulty": "Easy", "time_estimate": "30 min",
                "ifixit_url": "https://www.ifixit.com/Guide/Samsung+Galaxy+S23+Charging+Port+Replacement",
                "tools_needed": ["Phillips #00 screwdriver"],
            },
        ],
    },
    "fairphone5": {
        "msrp": 699,
        "parts": [
            {
                "name": "Battery (user-removable)", "part_number": "FP5-BAT",
                "oem_price": 35, "third_party_price": 35,
                "difficulty": "Very Easy", "time_estimate": "2 min",
                "ifixit_url": "https://www.ifixit.com/Guide/Fairphone+5+Battery+Replacement",
                "tools_needed": ["No tools needed — snaps off!"],
            },
            {
                "name": "Display Module", "part_number": "FP5-DIS",
                "oem_price": 99, "third_party_price": 99,
                "difficulty": "Easy", "time_estimate": "10 min",
                "ifixit_url": "https://www.ifixit.com/Guide/Fairphone+5+Display+Replacement",
                "tools_needed": ["Phillips #0 screwdriver"],
            },
            {
                "name": "Rear Camera Module", "part_number": "FP5-CAM-R",
                "oem_price": 79, "third_party_price": 79,
                "difficulty": "Easy", "time_estimate": "10 min",
                "ifixit_url": "https://www.ifixit.com/Guide/Fairphone+5+Camera+Replacement",
                "tools_needed": ["Phillips #0 screwdriver"],
            },
            {
                "name": "Speaker Module", "part_number": "FP5-SPK",
                "oem_price": 29, "third_party_price": 29,
                "difficulty": "Easy", "time_estimate": "5 min",
                "ifixit_url": "https://www.ifixit.com/Guide/Fairphone+5+Speaker+Replacement",
                "tools_needed": ["Phillips #0 screwdriver"],
            },
        ],
    },
    "macbookairm2": {
        "msrp": 1299,
        "parts": [
            {
                "name": "Battery", "part_number": "661-24307",
                "oem_price": 299, "third_party_price": 120,
                "difficulty": "Hard", "time_estimate": "2 hours",
                "ifixit_url": "https://www.ifixit.com/Guide/MacBook+Air+M2+Battery+Replacement",
                "tools_needed": ["Pentalobe P5 screwdriver", "Torx T5 screwdriver", "Heat gun"],
            },
            {
                "name": "Display Assembly", "part_number": "661-23460",
                "oem_price": 589, "third_party_price": 320,
                "difficulty": "Very Hard", "time_estimate": "3 hours",
                "ifixit_url": "https://www.ifixit.com/Guide/MacBook+Air+M2+Display+Replacement",
                "tools_needed": ["Pentalobe P5 screwdriver", "Torx T5 screwdriver", "Spudger"],
            },
            {
                "name": "Keyboard (full top case)", "part_number": "661-23445",
                "oem_price": 149, "third_party_price": 149,
                "difficulty": "Very Hard", "time_estimate": "3 hours",
                "ifixit_url": "https://www.ifixit.com/Guide/MacBook+Air+M2+Keyboard+Replacement",
                "tools_needed": ["Pentalobe P5 screwdriver", "Torx T5 screwdriver"],
            },
        ],
    },
    "dellxps13": {
        "msrp": 999,
        "parts": [
            {
                "name": "Battery", "part_number": "8YFRNG",
                "oem_price": 119, "third_party_price": 55,
                "difficulty": "Medium", "time_estimate": "45 min",
                "ifixit_url": "https://www.ifixit.com/Guide/Dell+XPS+13+Battery+Replacement",
                "tools_needed": ["Torx T5 screwdriver", "Phillips #00 screwdriver", "Plastic prying tool"],
            },
            {
                "name": "NVMe SSD (512 GB)", "part_number": "8M3V3",
                "oem_price": 129, "third_party_price": 65,
                "difficulty": "Easy", "time_estimate": "20 min",
                "ifixit_url": "https://www.ifixit.com/Guide/Dell+XPS+13+SSD+Replacement",
                "tools_needed": ["Torx T5 screwdriver", "Phillips #00 screwdriver"],
            },
            {
                "name": "Display Assembly", "part_number": "RN9GY",
                "oem_price": 289, "third_party_price": 150,
                "difficulty": "Hard", "time_estimate": "1.5 hours",
                "ifixit_url": "https://www.ifixit.com/Guide/Dell+XPS+13+Screen+Replacement",
                "tools_needed": ["Torx T5 screwdriver", "Plastic prying tool", "Spudger"],
            },
        ],
    },
}


class PartResult(BaseModel):
    name:                   str
    part_number:            str
    oem_price_eur:          float
    third_party_price_eur:  float
    price_cap_eur:          float
    eu_compliant:           bool
    compliance_note:        str
    savings_vs_new:         str
    best_price_eur:         float
    difficulty:             str
    time_estimate:          str
    tools_needed:           List[str]
    ifixit_url:             str


class PriceCheckRequest(BaseModel):
    device_id:    str
    part_name:    str
    custom_price: float


def _build_part_result(part: dict, msrp: float) -> PartResult:
    cap        = round(msrp * EU_PRICE_CAP_PERCENT, 2)
    oem        = part["oem_price"]
    tp         = part["third_party_price"]
    compliant  = oem <= cap
    best_price = min(oem, tp)
    savings    = round((1 - best_price / msrp) * 100)

    if compliant:
        note = (
            f"OEM price (EUR {oem}) is within the EU 30% cap (EUR {cap}). "
            "The manufacturer must supply this part to you or any repair shop."
        )
    else:
        note = (
            f"OEM price (EUR {oem}) exceeds the EU 30% cap (EUR {cap}) "
            f"by EUR {round(oem - cap, 2)}. "
            "Under the EU Right-to-Repair Directive you can challenge this. "
            f"Third-party alternatives available from EUR {tp}."
        )

    return PartResult(
        name=part["name"],
        part_number=part["part_number"],
        oem_price_eur=oem,
        third_party_price_eur=tp,
        price_cap_eur=cap,
        eu_compliant=compliant,
        compliance_note=note,
        savings_vs_new=f"Save {savings}% vs buying a new device",
        best_price_eur=best_price,
        difficulty=part["difficulty"],
        time_estimate=part["time_estimate"],
        tools_needed=part["tools_needed"],
        ifixit_url=part["ifixit_url"],
    )


@router.get("/{device_id}", response_model=List[PartResult])
def get_parts(device_id: str):
    """
    Return all spare parts for a device with EU 30% price compliance check.
    Each part shows OEM price, third-party price, the EU legal cap, and
    a plain-English explanation of whether the price complies with EU law.
    """
    device_data = PARTS_DB.get(device_id)
    if not device_data:
        raise HTTPException(
            status_code=404,
            detail=f"Device '{device_id}' not found. Search for it first."
        )
    msrp    = device_data["msrp"]
    results = [_build_part_result(p, msrp) for p in device_data["parts"]]
    logger.info(f"Parts for {device_id}: {len(results)} items, cap EUR {round(msrp*0.3)}")
    return results


@router.post("/check-price")
def check_custom_price(req: PriceCheckRequest):
    """
    Check whether a price found online is EU-compliant.
    Useful when shopping for parts from third-party sellers.
    """
    device_data = PARTS_DB.get(req.device_id)
    if not device_data:
        raise HTTPException(status_code=404, detail="Device not found.")

    msrp      = device_data["msrp"]
    cap       = round(msrp * EU_PRICE_CAP_PERCENT, 2)
    compliant = req.custom_price <= cap
    over_by   = round(req.custom_price - cap, 2) if not compliant else 0

    return {
        "part_name":    req.part_name,
        "custom_price": req.custom_price,
        "price_cap":    cap,
        "eu_compliant": compliant,
        "over_by_eur":  over_by,
        "message": (
            f"This price (EUR {req.custom_price}) is within the EU 30% cap — great find!"
            if compliant else
            f"This price is EUR {over_by} over the EU cap of EUR {cap}. "
            "You can contest it under EU Right-to-Repair Directive 2023/1670."
        ),
    }
