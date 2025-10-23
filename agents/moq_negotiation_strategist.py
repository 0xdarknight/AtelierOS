from uagents import Agent, Context
from typing import Dict, List, Tuple
import logging

from models.messages import MOQNegotiationRequest, MOQNegotiationResponse
from utils.config import Config
from utils.helpers import get_current_timestamp

logger = logging.getLogger(__name__)


def create_moq_negotiation_agent(metta_kb):
    agent = Agent(
        name="moq_negotiation_strategist",
        seed=Config.AGENT_SEEDS.get("moq_negotiation", "moq_negotiation_seed_unique_002"),
        port=Config.AGENT_PORTS.get("moq_negotiation", 8001),
        endpoint=Config.ENDPOINTS.get("moq_negotiation", ["http://localhost:8001/submit"])
    )

    @agent.on_message(MOQNegotiationRequest)
    async def handle_negotiation_request(ctx: Context, sender: str, msg: MOQNegotiationRequest):
        logger.info(f"MOQ Negotiation Strategist: Processing request from {sender}")
        logger.info(f"Styles: {msg.num_styles}, Budget: ${msg.budget}, Target units: {msg.target_units}")

        suppliers = identify_suitable_suppliers(
            metta_kb,
            msg.category,
            msg.target_units,
            msg.budget
        )

        strategies = []
        for supplier in suppliers:
            strategy = calculate_negotiation_strategy(
                metta_kb,
                supplier,
                msg.num_styles,
                msg.target_units,
                msg.budget,
                msg.timing_month,
                msg.payment_flexibility
            )
            strategies.append(strategy)

        strategies.sort(key=lambda x: x["expected_moq_per_style"])

        best_strategy = strategies[0] if strategies else None

        consolidation_opportunities = analyze_consolidation_opportunities(
            metta_kb,
            msg.num_styles,
            msg.fabrics,
            msg.colors
        )

        response = MOQNegotiationResponse(
            request_id=msg.request_id,
            recommended_supplier=best_strategy["supplier"] if best_strategy else "None found",
            negotiation_strategies=strategies,
            consolidation_opportunities=consolidation_opportunities,
            expected_success_rate=best_strategy["success_probability"] if best_strategy else 0,
            estimated_final_moq=best_strategy["expected_moq_per_style"] if best_strategy else 0,
            total_units_required=best_strategy["total_units"] if best_strategy else 0,
            alternative_options=strategies[1:3] if len(strategies) > 1 else [],
            timestamp=get_current_timestamp()
        )

        await ctx.send(sender, response)
        logger.info(f"Sent negotiation strategy: {best_strategy['supplier'] if best_strategy else 'None'}")

    return agent


def identify_suitable_suppliers(metta_kb, category: str, target_units: int, budget: float) -> List[Dict]:

    supplier_database = {
        "EcoKnits-Tirupur": {
            "specialization": ["knit-activewear", "t-shirts", "hoodies"],
            "moq_standard": 300,
            "moq_negotiable": 150,
            "success_rate": 0.75,
            "labor_rate": 0.65,
            "location": "India"
        },
        "VietnamTex-HoChiMinh": {
            "specialization": ["technical-activewear", "performance-wear"],
            "moq_standard": 500,
            "moq_negotiable": 250,
            "success_rate": 0.65,
            "labor_rate": 0.75,
            "location": "Vietnam"
        },
        "PortugalPremium-Porto": {
            "specialization": ["premium-knits", "sustainable-luxury", "small-batch"],
            "moq_standard": 200,
            "moq_negotiable": 100,
            "success_rate": 0.85,
            "labor_rate": 2.20,
            "location": "Portugal"
        },
        "ChinaScale-Guangzhou": {
            "specialization": ["high-volume-basics", "streetwear"],
            "moq_standard": 1000,
            "moq_negotiable": 600,
            "success_rate": 0.55,
            "labor_rate": 0.45,
            "location": "China"
        },
        "MakersRow-LosAngeles": {
            "specialization": ["small-batch", "custom-development", "made-in-usa"],
            "moq_standard": 100,
            "moq_negotiable": 50,
            "success_rate": 0.90,
            "labor_rate": 3.50,
            "location": "USA"
        },
        "BangladeshValue-Dhaka": {
            "specialization": ["basics-volume", "t-shirts", "budget-production"],
            "moq_standard": 1500,
            "moq_negotiable": 1000,
            "success_rate": 0.45,
            "labor_rate": 0.35,
            "location": "Bangladesh"
        }
    }

    suitable = []
    estimated_cost_per_unit = budget / target_units if target_units > 0 else 50

    for name, data in supplier_database.items():
        if data["moq_negotiable"] <= (target_units * 1.5):
            suitable.append({
                "name": name,
                **data
            })

    return suitable


def calculate_negotiation_strategy(metta_kb, supplier: Dict, num_styles: int,
                                   target_units_total: int, budget: float,
                                   timing_month: str, payment_flexibility: str) -> Dict:

    base_moq = supplier["moq_standard"]
    negotiable_moq = supplier["moq_negotiable"]

    strategies_applied = []
    total_reduction_pct = 0

    if num_styles >= 3:
        multi_style_reduction = 0.40 if num_styles >= 5 else 0.30
        total_reduction_pct += multi_style_reduction
        strategies_applied.append({
            "name": "Multi-style commitment",
            "description": f"Committing to {num_styles} styles in collection",
            "reduction": multi_style_reduction * 100,
            "reasoning": "Suppliers prefer volume across multiple styles"
        })

    off_peak_months = ["february", "march", "august", "september"]
    if timing_month and timing_month.lower() in off_peak_months:
        timing_reduction = 0.25
        total_reduction_pct += timing_reduction
        strategies_applied.append({
            "name": "Off-peak timing",
            "description": f"Ordering in {timing_month}",
            "reduction": timing_reduction * 100,
            "reasoning": "Factories seek orders between peak seasons"
        })

    if payment_flexibility == "prepayment":
        prepayment_reduction = 0.20
        total_reduction_pct += prepayment_reduction
        strategies_applied.append({
            "name": "100% prepayment",
            "description": "Offering full payment upfront",
            "reduction": prepayment_reduction * 100,
            "reasoning": "Eliminates supplier cash flow risk"
        })
    elif payment_flexibility == "50_deposit":
        deposit_reduction = 0.15
        total_reduction_pct += deposit_reduction
        strategies_applied.append({
            "name": "50% deposit",
            "description": "Offering 50% deposit (vs standard 30-40%)",
            "reduction": deposit_reduction * 100,
            "reasoning": "Reduces supplier financial risk"
        })

    total_reduction_pct = min(total_reduction_pct, 0.65)

    expected_moq = int(base_moq * (1 - total_reduction_pct))
    expected_moq = max(expected_moq, negotiable_moq)

    units_per_style = expected_moq
    total_units = units_per_style * num_styles

    success_probability = supplier["success_rate"] * (1 - (total_reduction_pct * 0.3))
    success_probability = min(max(success_probability, 0.30), 0.95)

    return {
        "supplier": supplier["name"],
        "base_moq": base_moq,
        "negotiable_moq": negotiable_moq,
        "strategies": strategies_applied,
        "total_reduction_pct": round(total_reduction_pct * 100, 1),
        "expected_moq_per_style": units_per_style,
        "total_units": total_units,
        "success_probability": round(success_probability * 100, 1),
        "labor_rate": supplier["labor_rate"],
        "location": supplier["location"],
        "recommendation": generate_recommendation(
            supplier, units_per_style, total_units, target_units_total, budget
        )
    }


def analyze_consolidation_opportunities(metta_kb, num_styles: int,
                                        fabrics: List[str], colors: List[str]) -> Dict:

    opportunities = []

    if fabrics and len(set(fabrics)) > 1:
        unique_fabrics = set(fabrics)
        if len(unique_fabrics) > 2:
            opportunities.append({
                "type": "fabric-consolidation",
                "current_state": f"{len(unique_fabrics)} different fabrics across {num_styles} styles",
                "recommendation": f"Consolidate to 1-2 base fabrics (e.g., cotton jersey for all tops)",
                "impact": "Combines fabric MOQ across styles, 8-12% volume discount",
                "moq_reduction": 30,
                "example": "If each style needs 500m fabric, 5 styles = 2,500m order vs 5x 500m"
            })

    if colors and len(colors) > 3:
        opportunities.append({
            "type": "colorway-coordination",
            "current_state": f"{len(colors)} colors across collection",
            "recommendation": "Limit to 3 coordinated colors (e.g., black, grey, olive)",
            "impact": "Meets dye lot minimums more easily, 5-8% dyeing savings",
            "moq_reduction": 25,
            "example": "Same 3 colors across all styles allows bulk dye orders"
        })

    if num_styles >= 4:
        opportunities.append({
            "type": "style-complexity-reduction",
            "current_state": f"{num_styles} styles with varying complexity",
            "recommendation": "Design styles with shared components (same collar, cuffs, pockets)",
            "impact": "Shared trim orders meet MOQs, reduces SKU count per component",
            "moq_reduction": 15,
            "example": "Same zipper across 3 styles = 1,500 zippers vs 3x 500 orders"
        })

    if not opportunities:
        opportunities.append({
            "type": "no-consolidation-needed",
            "current_state": "Collection already well-consolidated",
            "recommendation": "Current fabric and color selection is optimal",
            "impact": "No additional consolidation opportunities identified",
            "moq_reduction": 0
        })

    total_potential_reduction = sum(
        opp.get("moq_reduction", 0) for opp in opportunities if opp["type"] != "no-consolidation-needed"
    )

    return {
        "opportunities": opportunities,
        "total_potential_moq_reduction_pct": total_potential_reduction,
        "implementation_priority": prioritize_opportunities(opportunities)
    }


def prioritize_opportunities(opportunities: List[Dict]) -> List[str]:

    priority = []

    for opp in opportunities:
        if opp["type"] == "fabric-consolidation" and opp.get("moq_reduction", 0) >= 25:
            priority.append("HIGH: Fabric consolidation (biggest impact)")
        elif opp["type"] == "colorway-coordination" and opp.get("moq_reduction", 0) >= 20:
            priority.append("MEDIUM: Colorway coordination (good ROI)")
        elif opp["type"] == "style-complexity-reduction":
            priority.append("LOW: Style simplification (long-term benefit)")

    if not priority:
        priority.append("Collection is already optimized for MOQ efficiency")

    return priority


def generate_recommendation(supplier: Dict, units_per_style: int, total_units: int,
                           target_units: int, budget: float) -> str:

    if total_units <= target_units * 1.2:
        recommendation = f"RECOMMENDED: {units_per_style} units per style achieves target within 20%"
    elif total_units <= target_units * 1.5:
        recommendation = f"ACCEPTABLE: {units_per_style} units per style, {total_units - target_units} over target"
    else:
        recommendation = f"CAUTION: {total_units} total units exceeds target by {((total_units/target_units)-1)*100:.0f}%"

    estimated_cost = total_units * 55
    if estimated_cost > budget:
        recommendation += f" | WARNING: Estimated cost ${estimated_cost:,.0f} exceeds budget ${budget:,.0f}"

    return recommendation
