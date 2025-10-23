from uagents import Agent, Context
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import logging

from models.messages import ProductionTimelineRequest, ProductionTimelineResponse
from utils.config import Config
from utils.helpers import get_current_timestamp

logger = logging.getLogger(__name__)


def create_production_timeline_agent(metta_kb):
    agent = Agent(
        name="production_timeline_manager",
        seed=Config.AGENT_SEEDS.get("production_timeline", "production_timeline_seed_unique_003"),
        port=Config.AGENT_PORTS.get("production_timeline", 8002),
        endpoint=Config.ENDPOINTS.get("production_timeline", ["http://localhost:8002/submit"])
    )

    @agent.on_message(ProductionTimelineRequest)
    async def handle_timeline_request(ctx: Context, sender: str, msg: ProductionTimelineRequest):
        logger.info(f"Production Timeline Manager: Processing request from {sender}")
        logger.info(f"Garment: {msg.garment_type}, Units: {msg.units}, Supplier: {msg.supplier}, Launch: {msg.target_launch_date}")

        supplier_data = get_supplier_data(msg.supplier)

        if not supplier_data:
            logger.error(f"Supplier not found: {msg.supplier}")
            return

        phases = calculate_production_phases(
            metta_kb,
            msg.garment_type,
            msg.units,
            supplier_data,
            msg.order_month
        )

        quality_gates = insert_quality_checkpoints(
            metta_kb,
            msg.garment_type,
            msg.units,
            phases
        )

        risk_factors = assess_risk_factors(
            metta_kb,
            supplier_data["location"],
            msg.order_month,
            msg.target_launch_date,
            msg.complexity
        )

        critical_path = identify_critical_path(phases, risk_factors)

        total_timeline_days = sum(phase["duration_days"] for phase in phases)

        if msg.target_launch_date:
            launch_date = datetime.strptime(msg.target_launch_date, "%Y-%m-%d")
            earliest_start = launch_date - timedelta(days=total_timeline_days)
            is_achievable = earliest_start <= datetime.now()
            buffer_needed = 0 if is_achievable else (datetime.now() - earliest_start).days
        else:
            is_achievable = True
            buffer_needed = 0

        expedite_options = calculate_expedite_options(
            supplier_data,
            phases,
            buffer_needed
        )

        response = ProductionTimelineResponse(
            request_id=msg.request_id,
            supplier=msg.supplier,
            total_timeline_days=total_timeline_days,
            production_phases=phases,
            quality_gates=quality_gates,
            risk_factors=risk_factors,
            critical_path=critical_path,
            is_timeline_achievable=is_achievable,
            buffer_recommendation_days=max(7, len(risk_factors) * 3),
            expedite_options=expedite_options,
            estimated_completion_date=calculate_completion_date(datetime.now(), total_timeline_days),
            timestamp=get_current_timestamp()
        )

        await ctx.send(sender, response)
        logger.info(f"Sent production timeline: {total_timeline_days} days total")

    return agent


def get_supplier_data(supplier_name: str) -> Dict:
    suppliers = {
        "EcoKnits-Tirupur": {
            "location": "India",
            "lead_time_sampling": 14,
            "lead_time_bulk": 35,
            "lead_time_rush": 25,
            "rush_premium_pct": 10,
            "quality_defect_rate": 1.8,
            "response_time_hours": 6
        },
        "VietnamTex-HoChiMinh": {
            "location": "Vietnam",
            "lead_time_sampling": 18,
            "lead_time_bulk": 42,
            "lead_time_rush": 32,
            "rush_premium_pct": 15,
            "quality_defect_rate": 1.2,
            "response_time_hours": 12
        },
        "PortugalPremium-Porto": {
            "location": "Portugal",
            "lead_time_sampling": 10,
            "lead_time_bulk": 28,
            "lead_time_rush": None,
            "rush_premium_pct": 0,
            "quality_defect_rate": 0.6,
            "response_time_hours": 24
        },
        "ChinaScale-Guangzhou": {
            "location": "China",
            "lead_time_sampling": 16,
            "lead_time_bulk": 30,
            "lead_time_rush": 22,
            "rush_premium_pct": 8,
            "quality_defect_rate": 2.5,
            "response_time_hours": 8
        },
        "MakersRow-LosAngeles": {
            "location": "USA",
            "lead_time_sampling": 7,
            "lead_time_bulk": 21,
            "lead_time_rush": 14,
            "rush_premium_pct": 20,
            "quality_defect_rate": 1.0,
            "response_time_hours": 4
        },
        "BangladeshValue-Dhaka": {
            "location": "Bangladesh",
            "lead_time_sampling": 20,
            "lead_time_bulk": 45,
            "lead_time_rush": None,
            "rush_premium_pct": 0,
            "quality_defect_rate": 3.2,
            "response_time_hours": 24
        }
    }

    return suppliers.get(supplier_name)


def calculate_production_phases(metta_kb, garment_type: str, units: int, supplier: Dict, order_month: str) -> List[Dict]:
    phases = []

    phases.append({
        "phase_name": "Tech Pack Finalization & Fabric Procurement",
        "description": "Finalize technical specifications and source materials",
        "duration_days": 14,
        "activities": [
            "Tech pack review and approval",
            "Fabric swatch approval",
            "Trim procurement",
            "Sample fabric cutting"
        ],
        "dependencies": [],
        "checkpoints": ["Tech pack approval", "Fabric swatch approval"],
        "communication_frequency": "Daily"
    })

    phases.append({
        "phase_name": "Sampling & Development",
        "description": "Create and revise pre-production samples",
        "duration_days": supplier["lead_time_sampling"],
        "activities": [
            "Pre-production sample creation",
            "Sample shipping to brand",
            "Fit and quality review",
            "Revision request submission"
        ],
        "dependencies": ["Tech Pack Finalization & Fabric Procurement"],
        "checkpoints": ["Pre-production sample approval"],
        "communication_frequency": "Daily during development"
    })

    revision_rounds = estimate_revision_rounds(garment_type, supplier["quality_defect_rate"])
    if revision_rounds > 0:
        phases.append({
            "phase_name": "Sample Revisions",
            "description": f"Address fit and construction issues ({revision_rounds} rounds estimated)",
            "duration_days": revision_rounds * 7,
            "activities": [
                "Implement revision feedback",
                "Create revised samples",
                "Ship and review",
                "Final approval"
            ],
            "dependencies": ["Sampling & Development"],
            "checkpoints": ["Revised sample approval"],
            "communication_frequency": "Per revision cycle"
        })

    phases.append({
        "phase_name": "Bulk Production",
        "description": "Full-scale manufacturing with quality checkpoints",
        "duration_days": supplier["lead_time_bulk"],
        "activities": [
            "Fabric inspection and cutting",
            "Sewing operations",
            "Finishing and pressing",
            "Inline quality inspections"
        ],
        "dependencies": ["Sample Revisions" if revision_rounds > 0 else "Sampling & Development"],
        "checkpoints": [
            "Fabric inspection (Day 0)",
            "First article inspection (Day 5)",
            "Inline 20% inspection (Day 12)",
            "Inline 50% inspection (Day 20)",
            "Inline 80% inspection (Day 28)"
        ],
        "communication_frequency": "Every 3 days with photo updates"
    })

    phases.append({
        "phase_name": "Quality Control & Inspection",
        "description": "Final random inspection before shipment",
        "duration_days": 3,
        "activities": [
            "Third-party inspection booking",
            "Final random inspection (AQL 2.5)",
            "Defect sorting and rework if needed",
            "Packing verification"
        ],
        "dependencies": ["Bulk Production"],
        "checkpoints": ["Final random inspection pass"],
        "communication_frequency": "Immediate reporting"
    })

    shipping_days = calculate_shipping_duration(supplier["location"])
    phases.append({
        "phase_name": "Shipping & Logistics",
        "description": f"Sea freight and customs clearance to destination",
        "duration_days": shipping_days,
        "activities": [
            "Container loading and booking",
            "Ocean transit",
            "Customs clearance",
            "Warehouse delivery"
        ],
        "dependencies": ["Quality Control & Inspection"],
        "checkpoints": ["Container departure", "Arrival at port", "Customs cleared"],
        "communication_frequency": "Tracking updates every 3-5 days"
    })

    phases.append({
        "phase_name": "Receiving & Distribution",
        "description": "Warehouse receiving and inventory allocation",
        "duration_days": 4,
        "activities": [
            "Container unloading",
            "Receiving inspection",
            "Inventory count and allocation",
            "Distribution to 3PL or fulfillment center"
        ],
        "dependencies": ["Shipping & Logistics"],
        "checkpoints": ["Receiving complete", "Inventory live"],
        "communication_frequency": "Daily during receiving"
    })

    return phases


def insert_quality_checkpoints(metta_kb, garment_type: str, units: int, phases: List[Dict]) -> List[Dict]:
    quality_gates = []

    quality_gates.append({
        "checkpoint_name": "Pre-Production Sample (PPS) Approval",
        "timing": "Before bulk order",
        "phase": "Sampling & Development",
        "inspections": ["Fit test", "Fabric quality", "Construction accuracy", "Measurements"],
        "tolerance_fit": "±0.5cm",
        "tolerance_color": "Delta E 1.5",
        "approval_requirements": "Design team signoff + measurement spec sheet",
        "turnaround": "3-5 business days",
        "cost": "$50-100 per sample",
        "critical": True,
        "defect_prone_areas": get_defect_prone_areas(garment_type)
    })

    quality_gates.append({
        "checkpoint_name": "First Article Inspection (FAI)",
        "timing": "First 20 units of bulk production",
        "phase": "Bulk Production",
        "inspections": ["Construction consistency", "Measurement verification", "Defect check"],
        "tolerance_fit": "±1cm",
        "tolerance_defects": "0 critical, 1% major, 2% minor",
        "approval_requirements": "QC manager signoff",
        "turnaround": "Same day",
        "cost": "Included in production",
        "critical": True,
        "stop_production_if_failed": True
    })

    sample_size_20 = calculate_aql_sample_size(units * 0.2)
    quality_gates.append({
        "checkpoint_name": "Inline Inspection 20%",
        "timing": "20% production complete",
        "phase": "Bulk Production",
        "inspections": ["Random sampling AQL 2.5", "Workmanship check"],
        "sample_size": sample_size_20,
        "tolerance_defects": "0 critical, 1 major allowed, 3 minor allowed",
        "corrective_action": "Adjust process immediately",
        "turnaround": "4 hours",
        "cost": "Included in production",
        "critical": False
    })

    sample_size_50 = calculate_aql_sample_size(units * 0.5)
    quality_gates.append({
        "checkpoint_name": "Inline Inspection 50%",
        "timing": "50% production complete",
        "phase": "Bulk Production",
        "inspections": ["Random sampling AQL 2.5", "Packaging check"],
        "sample_size": sample_size_50,
        "tolerance_defects": "0 critical, 2 major allowed, 5 minor allowed",
        "corrective_action": "Rework defects, adjust process",
        "turnaround": "4 hours",
        "cost": "Included in production",
        "critical": False
    })

    sample_size_final = calculate_aql_sample_size(units)
    quality_gates.append({
        "checkpoint_name": "Final Random Inspection (FRI)",
        "timing": "100% production complete, before shipment",
        "phase": "Quality Control & Inspection",
        "inspections": ["Full random inspection AQL 2.5", "Packing verification"],
        "sample_size": sample_size_final,
        "tolerance_defects": "0 critical, 3 major allowed, 7 minor allowed",
        "approval_requirements": "Third-party inspection certificate",
        "turnaround": "1 business day",
        "cost": "$200-400",
        "critical": True,
        "stop_shipment_if_failed": True
    })

    return quality_gates


def get_defect_prone_areas(garment_type: str) -> List[str]:
    defect_map = {
        "t-shirt": ["Neck binding", "Shoulder seam"],
        "hoodie": ["Hood symmetry", "Pocket alignment", "Drawcord threading"],
        "jogger": ["Crotch seam", "Elastic evenness", "Pocket alignment"],
        "leggings": ["Gusset alignment", "Waistband roll", "Crotch seam strength"],
        "bomber-jacket": ["Zipper alignment", "Lining pucker", "Ribbing attachment", "Pocket symmetry"]
    }

    for key in defect_map:
        if key in garment_type.lower():
            return defect_map[key]

    return ["General construction"]


def calculate_aql_sample_size(lot_size: float) -> int:
    lot_size = int(lot_size)

    if lot_size <= 90:
        return 13
    elif lot_size <= 150:
        return 20
    elif lot_size <= 280:
        return 32
    elif lot_size <= 500:
        return 50
    elif lot_size <= 1200:
        return 80
    elif lot_size <= 3200:
        return 125
    else:
        return 200


def estimate_revision_rounds(garment_type: str, defect_rate: float) -> int:
    complexity_map = {
        "t-shirt": 0,
        "hoodie": 1,
        "jogger": 1,
        "leggings": 1,
        "bomber": 2,
        "jacket": 2
    }

    base_revisions = 1
    for key in complexity_map:
        if key in garment_type.lower():
            base_revisions = complexity_map[key]
            break

    if defect_rate > 2.5:
        base_revisions += 1

    return base_revisions


def calculate_shipping_duration(location: str) -> int:
    shipping_durations = {
        "China": 15,
        "Vietnam": 17,
        "India": 20,
        "Bangladesh": 23,
        "Portugal": 12,
        "USA": 0
    }

    return shipping_durations.get(location, 18)


def assess_risk_factors(metta_kb, location: str, order_month: str, target_launch: str, complexity: str) -> List[Dict]:
    risk_factors = []

    if location in ["China", "Vietnam", "Taiwan"]:
        if order_month and order_month.lower() in ["january", "february"]:
            risk_factors.append({
                "risk_name": "Chinese New Year Factory Closure",
                "impact": "14-21 day production halt",
                "probability": "High",
                "mitigation": "Place order 60 days before CNY or plan for delay",
                "delay_days": 21,
                "affected_regions": ["China", "Vietnam", "Taiwan"]
            })

    if location in ["India", "Bangladesh"]:
        if order_month and order_month.lower() in ["june", "july", "august", "september"]:
            risk_factors.append({
                "risk_name": "Monsoon Season Delays",
                "impact": "Shipping delays, fabric procurement delays",
                "probability": "Medium",
                "mitigation": "Add 1 week buffer to timeline",
                "delay_days": 7,
                "affected_regions": ["India", "Bangladesh", "South Asia"]
            })

    if order_month and order_month.lower() in ["october", "november", "december"]:
        risk_factors.append({
            "risk_name": "Peak Season Port Congestion",
            "impact": "1-2 weeks customs clearance delay",
            "probability": "Medium-High",
            "mitigation": "Book freight early, consider air freight backup",
            "delay_days": 10,
            "affected_ports": ["Los Angeles", "Long Beach", "New York"]
        })

    if complexity and complexity.lower() in ["high", "complex"]:
        risk_factors.append({
            "risk_name": "Complex Construction Quality Issues",
            "impact": "Additional sampling rounds or production rework",
            "probability": "Medium",
            "mitigation": "Allocate extra 1-2 weeks for revisions",
            "delay_days": 10,
            "affected_operations": ["Technical construction", "Multi-layer assembly"]
        })

    if location in ["Bangladesh", "China"] and order_month:
        risk_factors.append({
            "risk_name": "Compliance Audits & Factory Inspections",
            "impact": "Potential production delays if audit scheduled",
            "probability": "Low",
            "mitigation": "Verify supplier compliance status before ordering",
            "delay_days": 3,
            "affected_regions": ["Bangladesh", "China"]
        })

    return risk_factors


def identify_critical_path(phases: List[Dict], risk_factors: List[Dict]) -> List[str]:
    critical_path = []

    for phase in phases:
        if phase["phase_name"] in [
            "Sampling & Development",
            "Bulk Production",
            "Shipping & Logistics"
        ]:
            critical_path.append({
                "phase": phase["phase_name"],
                "duration": phase["duration_days"],
                "reasoning": "Sequential dependency, cannot be parallelized",
                "optimization_potential": get_optimization_potential(phase["phase_name"])
            })

    risk_delays = sum(risk["delay_days"] for risk in risk_factors if risk.get("probability") in ["High", "Medium-High"])
    if risk_delays > 0:
        critical_path.append({
            "phase": "Risk Factor Delays",
            "duration": risk_delays,
            "reasoning": f"{len([r for r in risk_factors if r.get('probability') in ['High', 'Medium-High']])} high-probability risks identified",
            "optimization_potential": "Mitigate through planning and contingencies"
        })

    return critical_path


def get_optimization_potential(phase_name: str) -> str:
    optimizations = {
        "Sampling & Development": "Use digital prototyping to reduce physical samples by 30%",
        "Bulk Production": "Parallel operations where possible, expedited rush available",
        "Shipping & Logistics": "Air freight option cuts 14+ days but adds $5-8/unit"
    }

    return optimizations.get(phase_name, "Limited optimization available")


def calculate_expedite_options(supplier: Dict, phases: List[Dict], buffer_needed: int) -> List[Dict]:
    expedite_options = []

    if supplier["lead_time_rush"]:
        bulk_phase = next((p for p in phases if p["phase_name"] == "Bulk Production"), None)
        if bulk_phase:
            days_saved = supplier["lead_time_bulk"] - supplier["lead_time_rush"]
            cost_increase_pct = supplier["rush_premium_pct"]

            expedite_options.append({
                "option": "Rush Production",
                "days_saved": days_saved,
                "cost_increase_pct": cost_increase_pct,
                "feasibility": "Available upon request",
                "recommendation": "Use if timeline critical" if buffer_needed > days_saved else "Not necessary"
            })

    expedite_options.append({
        "option": "Air Freight Instead of Sea",
        "days_saved": 14,
        "cost_increase_per_unit": "$5.00-8.00",
        "feasibility": "Always available",
        "recommendation": "Emergency option only, significantly increases landed cost"
    })

    expedite_options.append({
        "option": "Skip Sample Revisions (At Your Own Risk)",
        "days_saved": 7,
        "cost_increase_pct": 0,
        "feasibility": "Possible but risky",
        "recommendation": "Not recommended - quality issues will cost more than time saved"
    })

    return expedite_options


def calculate_completion_date(start_date: datetime, total_days: int) -> str:
    completion = start_date + timedelta(days=total_days)
    return completion.strftime("%Y-%m-%d")
