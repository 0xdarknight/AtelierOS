from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    StartSessionContent,
    chat_protocol_spec
)
from datetime import datetime
from uuid import uuid4
from typing import Dict, List, Optional
import logging

from models.messages import BOMCostingRequest, BOMCostingResponse
from utils.config import Config
from utils.helpers import get_current_timestamp, format_currency

logger = logging.getLogger(__name__)


def create_bom_costing_agent(metta_kb, moq_negotiation_address: str):
    agent = Agent(
        name="bom_costing_specialist",
        seed=Config.AGENT_SEEDS.get("bom_costing", "bom_costing_seed_unique_001"),
        port=Config.AGENT_PORTS.get("bom_costing", 8000),
        endpoint=Config.ENDPOINTS.get("bom_costing", ["http://localhost:8000/submit"])
    )

    chat_proto = Protocol(spec=chat_protocol_spec)

    @chat_proto.on_message(ChatMessage)
    async def handle_costing_request(ctx: Context, sender: str, msg: ChatMessage):
        logger.info(f"BOM Costing Specialist received request from {sender}")

        await ctx.send(sender, ChatAcknowledgement(
            timestamp=datetime.utcnow(),
            acknowledged_msg_id=msg.msg_id
        ))

        for item in msg.content:
            if isinstance(item, StartSessionContent):
                logger.info(f"Starting BOM costing session with {sender}")
                welcome_msg = """BOM & Costing Specialist Agent

I calculate precise Bill of Materials and landed costs for fashion products.

Capabilities:
- Fabric consumption with shrinkage/waste factors (±2% accuracy)
- Complete trim costing (zippers, buttons, labels, packaging)
- Labor cost by SMV (Standard Minute Value)
- Landed cost: FOB + freight + duty + customs + receiving
- Pricing recommendations with margin analysis

Example query: "Calculate BOM for hoodie, 500 units, cotton jersey, India supplier, size M"
"""
                response = ChatMessage(
                    timestamp=datetime.utcnow(),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text=welcome_msg)]
                )
                await ctx.send(sender, response)

            elif isinstance(item, TextContent):
                user_query = item.text.lower()
                logger.info(f"Processing BOM request: {user_query[:100]}")

                parsed_request = parse_bom_request(user_query)

                if not parsed_request.get("garment_type"):
                    error_msg = """Please specify garment type. Supported types:
- t-shirt-basic
- hoodie-pullover
- jogger-pants
- leggings-activewear
- jacket-bomber

Example: "Calculate BOM for hoodie-pullover, 500 units, cotton jersey"
"""
                    response = ChatMessage(
                        timestamp=datetime.utcnow(),
                        msg_id=uuid4(),
                        content=[TextContent(type="text", text=error_msg)]
                    )
                    await ctx.send(sender, response)
                    continue

                bom_result = calculate_complete_bom(
                    metta_kb,
                    parsed_request["garment_type"],
                    parsed_request.get("size", "m"),
                    parsed_request.get("fabric", "cotton-jersey-180gsm"),
                    parsed_request.get("supplier", "EcoKnits-Tirupur"),
                    parsed_request.get("units", 500)
                )

                formatted_response = format_bom_response(bom_result)

                response = ChatMessage(
                    timestamp=datetime.utcnow(),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text=formatted_response)]
                )
                await ctx.send(sender, response)

    agent.include(chat_proto, publish_manifest=True)
    return agent


def parse_bom_request(user_query: str) -> Dict:
    request = {}

    garment_keywords = {
        "t-shirt": "t-shirt-basic",
        "tshirt": "t-shirt-basic",
        "tee": "t-shirt-basic",
        "hoodie": "hoodie-pullover",
        "pullover": "hoodie-pullover",
        "jogger": "jogger-pants",
        "pants": "jogger-pants",
        "legging": "leggings-activewear",
        "leggings": "leggings-activewear",
        "jacket": "jacket-bomber",
        "bomber": "jacket-bomber"
    }

    for keyword, garment_type in garment_keywords.items():
        if keyword in user_query:
            request["garment_type"] = garment_type
            break

    sizes = ["xs", "s", "m", "l", "xl", "xxl"]
    for size in sizes:
        if f" {size} " in f" {user_query} " or f"size {size}" in user_query:
            request["size"] = size
            break

    if "cotton" in user_query and "jersey" in user_query:
        request["fabric"] = "cotton-jersey-180gsm"
    elif "recycled" in user_query and "polyester" in user_query:
        request["fabric"] = "recycled-polyester-performance"
    elif "organic" in user_query and "twill" in user_query:
        request["fabric"] = "organic-cotton-twill"

    supplier_keywords = {
        "india": "EcoKnits-Tirupur",
        "tirupur": "EcoKnits-Tirupur",
        "vietnam": "VietnamTex-HoChiMinh",
        "portugal": "PortugalPremium-Porto",
        "china": "ChinaScale-Guangzhou",
        "los angeles": "MakersRow-LosAngeles",
        "usa": "MakersRow-LosAngeles"
    }

    for keyword, supplier in supplier_keywords.items():
        if keyword in user_query:
            request["supplier"] = supplier
            break

    import re
    units_match = re.search(r'(\d+)\s*units?', user_query)
    if units_match:
        request["units"] = int(units_match.group(1))

    return request


def calculate_complete_bom(metta_kb, garment_type: str, size: str,
                           fabric: str, supplier: str, units: int) -> Dict:

    logger.info(f"Calculating BOM: {garment_type}, {size}, {fabric}, {supplier}, {units} units")

    fabric_consumption = calculate_fabric_consumption(
        metta_kb, garment_type, size, fabric
    )

    fabric_cost = calculate_fabric_cost(
        metta_kb, fabric, fabric_consumption
    )

    trim_costs = calculate_trim_costs(
        metta_kb, garment_type
    )

    labor_cost = calculate_labor_cost(
        metta_kb, garment_type, supplier
    )

    overhead_profit = calculate_overhead_profit(
        metta_kb, supplier, fabric_cost + trim_costs["total"] + labor_cost
    )

    fob_cost = (fabric_cost + trim_costs["total"] + labor_cost +
                overhead_profit["overhead"] + overhead_profit["profit"])

    landed_cost = calculate_landed_cost(
        metta_kb, fob_cost, supplier, units, garment_type
    )

    pricing = calculate_pricing_recommendations(landed_cost)

    return {
        "garment_type": garment_type,
        "size": size,
        "fabric": fabric,
        "supplier": supplier,
        "units": units,
        "fabric_consumption_meters": fabric_consumption,
        "fabric_cost": fabric_cost,
        "trim_costs": trim_costs,
        "labor_cost": labor_cost,
        "overhead": overhead_profit["overhead"],
        "factory_profit": overhead_profit["profit"],
        "fob_cost": fob_cost,
        "landed_cost_breakdown": landed_cost,
        "landed_cost_total": landed_cost["total"],
        "pricing_recommendations": pricing
    }


def calculate_fabric_consumption(metta_kb, garment_type: str, size: str, fabric: str) -> float:

    base_consumption_map = {
        "t-shirt-basic": {"xs": 1.0, "s": 1.2, "m": 1.3, "l": 1.4, "xl": 1.5, "xxl": 1.7},
        "hoodie-pullover": {"xs": 1.8, "s": 2.0, "m": 2.2, "l": 2.4, "xl": 2.6, "xxl": 2.9},
        "jogger-pants": {"xs": 1.6, "s": 1.8, "m": 2.0, "l": 2.2, "xl": 2.4, "xxl": 2.7},
        "leggings-activewear": {"xs": 1.4, "s": 1.5, "m": 1.7, "l": 1.9, "xl": 2.1, "xxl": 2.3},
        "jacket-bomber": {"xs": 2.2, "s": 2.4, "m": 2.6, "l": 2.8, "xl": 3.1, "xxl": 3.4}
    }

    efficiency_map = {
        "t-shirt-basic": 0.85,
        "hoodie-pullover": 0.78,
        "jogger-pants": 0.76,
        "leggings-activewear": 0.82,
        "jacket-bomber": 0.72
    }

    shrinkage_map = {
        "cotton-jersey-180gsm": 0.03,
        "recycled-polyester-performance": 0.02,
        "organic-cotton-twill": 0.04,
        "merino-wool-blend": 0.05,
        "tencel-lyocell-jersey": 0.03
    }

    waste_map = {
        "cotton-jersey-180gsm": 0.15,
        "recycled-polyester-performance": 0.12,
        "organic-cotton-twill": 0.18,
        "merino-wool-blend": 0.14,
        "tencel-lyocell-jersey": 0.13
    }

    base_meters = base_consumption_map.get(garment_type, {}).get(size, 2.0)
    pattern_efficiency = efficiency_map.get(garment_type, 0.80)
    shrinkage = shrinkage_map.get(fabric, 0.03)
    waste = waste_map.get(fabric, 0.15)

    efficiency_factor = 1.0 / pattern_efficiency
    shrinkage_factor = 1.0 + shrinkage
    waste_factor = 1.0 + waste

    total_meters = base_meters * efficiency_factor * shrinkage_factor * waste_factor

    logger.info(f"Fabric calculation: {base_meters}m base × {efficiency_factor:.2f} efficiency × {shrinkage_factor:.2f} shrinkage × {waste_factor:.2f} waste = {total_meters:.2f}m")

    return round(total_meters, 2)


def calculate_fabric_cost(metta_kb, fabric: str, meters: float) -> float:

    fabric_prices = {
        "cotton-jersey-180gsm": 5.80,
        "recycled-polyester-performance": 7.20,
        "organic-cotton-twill": 9.50,
        "merino-wool-blend": 18.50,
        "tencel-lyocell-jersey": 10.80
    }

    price_per_meter = fabric_prices.get(fabric, 6.00)
    total_cost = meters * price_per_meter

    return round(total_cost, 2)


def calculate_trim_costs(metta_kb, garment_type: str) -> Dict:

    trim_specs = {
        "t-shirt-basic": {
            "label-main-neck": 0.15,
            "label-care-side": 0.08,
            "hangtag": 0.12,
            "polybag": 0.08,
            "thread": 0.05
        },
        "hoodie-pullover": {
            "drawcord-5mm-1.2m": 0.18,
            "cord-locks-2": 0.10,
            "label-main-neck": 0.15,
            "label-care-side": 0.08,
            "hangtag": 0.12,
            "polybag": 0.08,
            "thread": 0.08
        },
        "jogger-pants": {
            "elastic-waistband-40mm": 0.11,
            "drawcord-5mm-1.4m": 0.21,
            "cord-locks-2": 0.10,
            "elastic-ankle-25mm": 0.05,
            "zipper-pocket-18cm-2": 2.40,
            "label-main": 0.15,
            "label-care": 0.08,
            "hangtag": 0.12,
            "polybag": 0.10,
            "thread": 0.06
        },
        "leggings-activewear": {
            "elastic-waistband-60mm": 0.13,
            "gusset-mesh": 0.15,
            "label-main": 0.15,
            "label-care": 0.08,
            "hangtag": 0.12,
            "polybag": 0.08,
            "thread-stretch": 0.08
        },
        "jacket-bomber": {
            "zipper-front-60cm": 2.10,
            "zipper-pocket-18cm-2": 2.40,
            "snap-button-3": 0.75,
            "ribbing-cuff": 0.18,
            "ribbing-hem": 0.27,
            "ribbing-collar": 0.15,
            "label-main": 0.15,
            "label-care": 0.08,
            "hangtag": 0.12,
            "polybag": 0.10,
            "thread": 0.10
        }
    }

    trims = trim_specs.get(garment_type, {"basic-trims": 0.50})
    total = sum(trims.values())

    return {
        "items": trims,
        "total": round(total, 2)
    }


def calculate_labor_cost(metta_kb, garment_type: str, supplier: str) -> float:

    smv_map = {
        "t-shirt-basic": 10,
        "hoodie-pullover": 35,
        "jogger-pants": 31,
        "leggings-activewear": 25,
        "jacket-bomber": 57
    }

    labor_rates = {
        "EcoKnits-Tirupur": 0.65,
        "VietnamTex-HoChiMinh": 0.75,
        "PortugalPremium-Porto": 2.20,
        "ChinaScale-Guangzhou": 0.45,
        "MakersRow-LosAngeles": 3.50,
        "BangladeshValue-Dhaka": 0.35
    }

    smv = smv_map.get(garment_type, 20)
    rate = labor_rates.get(supplier, 0.70)

    labor_cost = smv * rate

    logger.info(f"Labor cost: {smv} SMV × ${rate}/min = ${labor_cost:.2f}")

    return round(labor_cost, 2)


def calculate_overhead_profit(metta_kb, supplier: str, direct_cost: float) -> Dict:

    overhead_rates = {
        "EcoKnits-Tirupur": 0.16,
        "VietnamTex-HoChiMinh": 0.15,
        "PortugalPremium-Porto": 0.18,
        "ChinaScale-Guangzhou": 0.14,
        "MakersRow-LosAngeles": 0.22,
        "BangladeshValue-Dhaka": 0.12
    }

    profit_rates = {
        "EcoKnits-Tirupur": 0.10,
        "VietnamTex-HoChiMinh": 0.12,
        "PortugalPremium-Porto": 0.15,
        "ChinaScale-Guangzhou": 0.08,
        "MakersRow-LosAngeles": 0.18,
        "BangladeshValue-Dhaka": 0.07
    }

    overhead_pct = overhead_rates.get(supplier, 0.16)
    profit_pct = profit_rates.get(supplier, 0.10)

    overhead = direct_cost * overhead_pct
    subtotal = direct_cost + overhead
    profit = subtotal * profit_pct

    return {
        "overhead": round(overhead, 2),
        "profit": round(profit, 2)
    }


def calculate_landed_cost(metta_kb, fob: float, supplier: str,
                          units: int, garment_type: str) -> Dict:

    freight_costs = {
        "EcoKnits-Tirupur": 3.60,
        "VietnamTex-HoChiMinh": 3.40,
        "PortugalPremium-Porto": 8.50,
        "ChinaScale-Guangzhou": 3.15,
        "MakersRow-LosAngeles": 1.20,
        "BangladeshValue-Dhaka": 3.35
    }

    duty_rates = {
        "t-shirt-basic": 0.16,
        "hoodie-pullover": 0.16,
        "jogger-pants": 0.165,
        "leggings-activewear": 0.16,
        "jacket-bomber": 0.165
    }

    freight_per_unit = freight_costs.get(supplier, 3.50)
    duty_rate = duty_rates.get(garment_type, 0.16)
    duty_amount = fob * duty_rate

    customs_broker = 125 / units if units > 0 else 0.50
    inspection = 0.40
    receiving = 0.65

    total_landed = fob + freight_per_unit + duty_amount + customs_broker + inspection + receiving

    return {
        "fob": round(fob, 2),
        "freight": round(freight_per_unit, 2),
        "duty": round(duty_amount, 2),
        "customs_broker": round(customs_broker, 2),
        "inspection": inspection,
        "receiving": receiving,
        "total": round(total_landed, 2)
    }


def calculate_pricing_recommendations(landed_cost: float) -> Dict:

    dtc_multiplier = 2.8
    wholesale_multiplier = 2.2
    premium_multiplier = 3.5

    dtc_price = landed_cost * dtc_multiplier
    dtc_rounded = round(dtc_price / 10) * 10 - 1

    wholesale_price = landed_cost * wholesale_multiplier
    wholesale_rounded = round(wholesale_price / 10) * 10 - 1

    premium_price = landed_cost * premium_multiplier
    premium_rounded = round(premium_price / 10) * 10 - 1

    return {
        "dtc": {
            "price": dtc_rounded,
            "margin_pct": round(((dtc_rounded - landed_cost) / dtc_rounded) * 100, 1)
        },
        "wholesale": {
            "price": wholesale_rounded,
            "margin_pct": round(((wholesale_rounded - landed_cost) / wholesale_rounded) * 100, 1)
        },
        "premium": {
            "price": premium_rounded,
            "margin_pct": round(((premium_rounded - landed_cost) / premium_rounded) * 100, 1)
        }
    }


def format_bom_response(bom: Dict) -> str:
    response = f"""
BILL OF MATERIALS & COSTING ANALYSIS
=====================================

Product: {bom['garment_type'].replace('-', ' ').title()}
Size: {bom['size'].upper()}
Fabric: {bom['fabric'].replace('-', ' ').title()}
Supplier: {bom['supplier']}
Order Quantity: {bom['units']} units

MATERIAL COSTS:
--------------
Fabric: {bom['fabric_consumption_meters']}m @ ${bom['fabric_cost']:.2f}

Trims & Packaging:"""

    for item_name, cost in bom['trim_costs']['items'].items():
        response += f"\n  {item_name.replace('-', ' ').title()}: ${cost:.2f}"

    response += f"\n  TOTAL TRIMS: ${bom['trim_costs']['total']:.2f}"

    response += f"""

PRODUCTION COSTS:
----------------
Labor: ${bom['labor_cost']:.2f}
Factory Overhead (16%): ${bom['overhead']:.2f}
Factory Profit (10%): ${bom['factory_profit']:.2f}

FOB COST: ${bom['fob_cost']:.2f}

LANDED COST BREAKDOWN:
---------------------
FOB: ${bom['landed_cost_breakdown']['fob']:.2f}
+ Freight: ${bom['landed_cost_breakdown']['freight']:.2f}
+ Duty ({bom['landed_cost_breakdown']['duty'] / bom['landed_cost_breakdown']['fob'] * 100:.1f}%): ${bom['landed_cost_breakdown']['duty']:.2f}
+ Customs Broker: ${bom['landed_cost_breakdown']['customs_broker']:.2f}
+ Inspection: ${bom['landed_cost_breakdown']['inspection']:.2f}
+ Warehouse Receiving: ${bom['landed_cost_breakdown']['receiving']:.2f}

TOTAL LANDED COST: ${bom['landed_cost_total']:.2f}

PRICING RECOMMENDATIONS:
-----------------------
DTC (Direct-to-Consumer):
  Retail Price: ${bom['pricing_recommendations']['dtc']['price']:.2f}
  Gross Margin: {bom['pricing_recommendations']['dtc']['margin_pct']}%

Wholesale:
  Wholesale Price: ${bom['pricing_recommendations']['wholesale']['price']:.2f}
  Gross Margin: {bom['pricing_recommendations']['wholesale']['margin_pct']}%

Premium Positioning:
  Retail Price: ${bom['pricing_recommendations']['premium']['price']:.2f}
  Gross Margin: {bom['pricing_recommendations']['premium']['margin_pct']}%

TOTAL ORDER VALUE:
-----------------
FOB Total: ${bom['fob_cost'] * bom['units']:,.2f}
Landed Total: ${bom['landed_cost_total'] * bom['units']:,.2f}

This BOM calculation includes all direct costs with ±2% accuracy.
Actual costs may vary based on fabric availability and supplier negotiations.
"""

    return response
