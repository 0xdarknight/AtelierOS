from uagents import Agent, Context
import logging
from typing import List, Dict

from models.messages import (
    DesignBriefRequest,
    SupplierProposalMessage
)
from utils.metta_loader import MettaKnowledgeBase
from utils.config import Config
from utils.helpers import generate_sku, get_current_timestamp

logger = logging.getLogger(__name__)


def create_design_sourcing_agent(metta_kb: MettaKnowledgeBase,
                                   production_coordinator_address: str):
    agent = Agent(
        name="design_sourcing",
        seed=Config.AGENT_SEEDS["design_sourcing"],
        port=Config.AGENT_PORTS["design_sourcing"],
        endpoint=Config.ENDPOINTS["design_sourcing"]
    )

    @agent.on_message(DesignBriefRequest)
    async def create_designs(ctx: Context, sender: str, msg: DesignBriefRequest):
        logger.info("Design & Sourcing: Processing design brief")

        concept = msg.concept
        strategy = msg.strategy
        constraints = msg.financial_constraints

        designs = generate_design_concepts(
            concept["category"],
            concept["niche"],
            strategy["initial_products"],
            concept.get("values", [])
        )

        logger.info(f"Generated {len(designs)} design concepts")

        target_moq = constraints["units"]
        suppliers = metta_kb.query_suppliers(concept["category"], target_moq)

        if not suppliers:
            logger.warning(f"No suppliers found for category {concept['category']} with MOQ <= {target_moq}")
            suppliers = [
                {
                    "name": "EcoTextile",
                    "moq": 250,
                    "cost_per_unit": 42
                }
            ]

        best_supplier = select_optimal_supplier(
            suppliers,
            constraints["max_cogs"],
            target_moq,
            concept.get("values", [])
        )

        logger.info(f"Selected supplier: {best_supplier['name']} at ${best_supplier['cost_per_unit']}/unit")

        tech_packs = create_tech_packs(designs, best_supplier)

        total_cost = best_supplier["cost_per_unit"] * max(best_supplier["moq"], target_moq)

        proposal = SupplierProposalMessage(
            designs=designs,
            supplier=best_supplier,
            tech_packs=tech_packs,
            cost_per_unit=best_supplier["cost_per_unit"],
            moq=best_supplier["moq"],
            lead_time_days=best_supplier.get("lead_time", 28),
            total_production_cost=total_cost,
            timestamp=get_current_timestamp()
        )

        await ctx.send(production_coordinator_address, proposal)
        logger.info("Sent supplier proposal to production coordinator")

    return agent


def generate_design_concepts(category: str, niche: str,
                             product_names: List[str], values: List[str]) -> List[Dict]:
    designs = []

    materials = determine_materials(values)
    colors = determine_color_palette(category, niche)
    features = determine_features(category, niche)

    for i, product_name in enumerate(product_names):
        design = {
            "id": f"DESIGN-{i+1:03d}",
            "name": product_name,
            "category": category,
            "materials": materials,
            "colors": colors[:Config.COLOR_LIMIT_PER_DESIGN],
            "sizes": Config.SIZE_RANGE_STANDARD,
            "features": features,
            "description": generate_design_description(product_name, materials, features),
            "sustainability_score": calculate_sustainability_score(materials)
        }
        designs.append(design)

    return designs


def determine_materials(values: List[str]) -> List[str]:
    if "sustainable" in values:
        return ["Organic Cotton Blend", "Recycled Polyester", "Tencel"]
    return ["Performance Polyester", "Cotton Blend", "Spandex"]


def determine_color_palette(category: str, niche: str) -> List[str]:
    if niche == "urban-cyclists":
        return ["Slate Grey", "Olive Green", "Black", "Navy"]
    elif niche == "yoga-enthusiasts":
        return ["Lavender", "Mint", "Cream", "Peach"]
    elif niche == "runners":
        return ["Cobalt Blue", "Black", "Grey", "Neon Yellow"]
    return ["Black", "White", "Grey", "Navy"]


def determine_features(category: str, niche: str) -> List[str]:
    base_features = ["Moisture-wicking", "4-way stretch", "Breathable fabric"]

    if niche == "urban-cyclists":
        return base_features + ["Reflective details", "Hidden pockets", "Water-resistant coating"]
    elif niche == "yoga-enthusiasts":
        return base_features + ["High waistband", "Seamless construction", "Squat-proof"]
    elif niche == "runners":
        return base_features + ["Anti-chafe seams", "Ventilation panels", "Reflective trim"]

    return base_features


def generate_design_description(product_name: str, materials: List[str],
                                features: List[str]) -> str:
    material_str = " and ".join(materials)
    features_str = ", ".join(features[:3])

    return (f"{product_name} crafted from {material_str}. "
            f"Features include {features_str}. "
            f"Designed for performance and durability.")


def calculate_sustainability_score(materials: List[str]) -> int:
    sustainable_keywords = ["organic", "recycled", "tencel", "bamboo"]
    score = 50

    for material in materials:
        material_lower = material.lower()
        for keyword in sustainable_keywords:
            if keyword in material_lower:
                score += 15
                break

    return min(score, 95)


def select_optimal_supplier(suppliers: List[Dict], max_cogs: float,
                            target_units: int, values: List[str]) -> Dict:
    suitable = []

    for supplier in suppliers:
        if supplier["cost_per_unit"] <= max_cogs and supplier["moq"] <= target_units:
            suitable.append(supplier)

    if not suitable:
        suitable = suppliers

    if "sustainable" in values:
        suitable.sort(key=lambda x: x.get("quality_rating", 4.0), reverse=True)
    else:
        suitable.sort(key=lambda x: x["cost_per_unit"])

    selected = suitable[0] if suitable else suppliers[0]

    full_supplier_details = {
        "name": selected["name"],
        "moq": selected["moq"],
        "cost_per_unit": selected["cost_per_unit"],
        "lead_time": selected.get("lead_time", 28),
        "location": selected.get("location", "Vietnam"),
        "certifications": selected.get("certifications", ["OEKO-TEX"]),
        "quality_rating": selected.get("quality_rating", 4.5)
    }

    return full_supplier_details


def create_tech_packs(designs: List[Dict], supplier: Dict) -> List[Dict]:
    tech_packs = []

    for design in designs:
        skus = []
        sku_count = 0

        for color in design["colors"]:
            for size in design["sizes"]:
                sku = generate_sku(design["name"], size, color, sku_count)
                skus.append({
                    "sku": sku,
                    "size": size,
                    "color": color
                })
                sku_count += 1

        tech_pack = {
            "design_id": design["id"],
            "product_name": design["name"],
            "skus": skus,
            "total_skus": len(skus),
            "materials": design["materials"],
            "construction_specs": {
                "seam_type": "Flatlock seams",
                "closures": "YKK zippers where applicable",
                "labels": "Woven brand label at neck, care label at side seam"
            },
            "measurements": generate_size_chart(design["name"]),
            "quality_standards": {
                "fabric_inspection": "4-point system",
                "defect_tolerance": "2% maximum",
                "color_matching": "Within Delta E 2.0"
            },
            "packaging": {
                "type": "Recycled poly bag with branded insert",
                "labeling": "SKU barcode and size sticker"
            },
            "supplier": supplier["name"],
            "estimated_cost_per_unit": supplier["cost_per_unit"]
        }

        tech_packs.append(tech_pack)

    return tech_packs


def generate_size_chart(product_name: str) -> Dict[str, Dict]:
    if "hoodie" in product_name.lower() or "shirt" in product_name.lower():
        return {
            "XS": {"chest": 34, "length": 26, "sleeve": 32},
            "S": {"chest": 36, "length": 27, "sleeve": 33},
            "M": {"chest": 38, "length": 28, "sleeve": 34},
            "L": {"chest": 40, "length": 29, "sleeve": 35},
            "XL": {"chest": 42, "length": 30, "sleeve": 36},
            "XXL": {"chest": 44, "length": 31, "sleeve": 37}
        }
    elif "pant" in product_name.lower() or "legging" in product_name.lower():
        return {
            "XS": {"waist": 24, "hip": 34, "inseam": 28},
            "S": {"waist": 26, "hip": 36, "inseam": 28},
            "M": {"waist": 28, "hip": 38, "inseam": 29},
            "L": {"waist": 30, "hip": 40, "inseam": 29},
            "XL": {"waist": 32, "hip": 42, "inseam": 30},
            "XXL": {"waist": 34, "hip": 44, "inseam": 30}
        }
    else:
        return {
            "XS": {"chest": 32, "length": 24},
            "S": {"chest": 34, "length": 25},
            "M": {"chest": 36, "length": 26},
            "L": {"chest": 38, "length": 27},
            "XL": {"chest": 40, "length": 28},
            "XXL": {"chest": 42, "length": 29}
        }
