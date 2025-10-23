from uagents import Agent, Context
from typing import Dict, List, Tuple
import logging

from models.messages import CashFlowRequest, CashFlowResponse
from utils.config import Config
from utils.helpers import get_current_timestamp

logger = logging.getLogger(__name__)


def create_cash_flow_agent(metta_kb):
    agent = Agent(
        name="cash_flow_financial_planner",
        seed=Config.AGENT_SEEDS.get("cash_flow", "cash_flow_seed_unique_005"),
        port=Config.AGENT_PORTS.get("cash_flow", 8004),
        endpoint=Config.ENDPOINTS.get("cash_flow", ["http://localhost:8004/submit"])
    )

    @agent.on_message(CashFlowRequest)
    async def handle_cash_flow_request(ctx: Context, sender: str, msg: CashFlowRequest):
        logger.info(f"Cash Flow Financial Planner: Processing request from {sender}")
        logger.info(f"Budget: ${msg.initial_capital}, FOB: ${msg.fob_cost_per_unit}, Units: {msg.units}, Retail: ${msg.retail_price}")

        payment_schedule = calculate_payment_schedule(
            metta_kb,
            msg.fob_cost_per_unit,
            msg.units,
            msg.landed_cost_per_unit,
            msg.payment_terms
        )

        monthly_cashflow = model_monthly_cashflow(
            metta_kb,
            msg.initial_capital,
            payment_schedule,
            msg.units,
            msg.retail_price,
            msg.expected_monthly_sales,
            msg.selling_channel
        )

        cumulative_analysis = calculate_cumulative_cash_position(
            msg.initial_capital,
            monthly_cashflow
        )

        capital_requirements = assess_capital_requirements(
            cumulative_analysis,
            msg.initial_capital,
            payment_schedule
        )

        breakeven_analysis = calculate_breakeven(
            monthly_cashflow,
            cumulative_analysis
        )

        pricing_recommendations = generate_pricing_recommendations(
            metta_kb,
            msg.landed_cost_per_unit,
            msg.retail_price,
            msg.positioning_strategy
        )

        reorder_planning = plan_reorder_cashflow(
            metta_kb,
            msg.units,
            msg.expected_monthly_sales,
            msg.fob_cost_per_unit,
            cumulative_analysis
        )

        risk_scenarios = model_risk_scenarios(
            monthly_cashflow,
            cumulative_analysis,
            msg.initial_capital
        )

        response = CashFlowResponse(
            request_id=msg.request_id,
            initial_capital=msg.initial_capital,
            payment_schedule=payment_schedule,
            monthly_cashflow=monthly_cashflow,
            cumulative_cash_position=cumulative_analysis,
            capital_requirements=capital_requirements,
            breakeven_analysis=breakeven_analysis,
            pricing_recommendations=pricing_recommendations,
            reorder_planning=reorder_planning,
            risk_scenarios=risk_scenarios,
            timestamp=get_current_timestamp()
        )

        await ctx.send(sender, response)
        logger.info(f"Sent cash flow analysis: Breakeven month {breakeven_analysis.get('breakeven_month', 'N/A')}, Capital gap ${capital_requirements.get('additional_capital_needed', 0):,.0f}")

    return agent


def calculate_payment_schedule(metta_kb, fob_per_unit: float, units: int, landed_per_unit: float, payment_terms: str) -> Dict:
    total_fob = fob_per_unit * units
    total_landed = landed_per_unit * units
    freight_and_duties = total_landed - total_fob

    if payment_terms == "standard":
        deposit_pct = 40
        balance_pct = 60
    elif payment_terms == "prepayment":
        deposit_pct = 100
        balance_pct = 0
    elif payment_terms == "50-50":
        deposit_pct = 50
        balance_pct = 50
    elif payment_terms == "30-70":
        deposit_pct = 30
        balance_pct = 70
    else:
        deposit_pct = 40
        balance_pct = 60

    deposit_amount = total_fob * (deposit_pct / 100)
    balance_amount = total_fob * (balance_pct / 100)

    sampling_cost = 1500
    techpack_cost = 500
    marketing_prelaunch = 3000
    photography = 1200
    website_setup = 800

    schedule = {
        "month_minus_4": {
            "description": "Sample Development",
            "outflows": {
                "sampling_cost": sampling_cost,
                "techpack_development": techpack_cost
            },
            "total_outflow": sampling_cost + techpack_cost,
            "total_inflow": 0
        },
        "month_minus_2": {
            "description": "Production Deposit",
            "outflows": {
                "production_deposit": deposit_amount
            },
            "total_outflow": deposit_amount,
            "total_inflow": 0
        },
        "month_minus_1": {
            "description": "Balance Payment & Launch Prep",
            "outflows": {
                "production_balance": balance_amount,
                "freight_and_duties": freight_and_duties,
                "marketing_prelaunch": marketing_prelaunch,
                "photography": photography,
                "website_launch": website_setup
            },
            "total_outflow": balance_amount + freight_and_duties + marketing_prelaunch + photography + website_setup,
            "total_inflow": 0
        }
    }

    return schedule


def model_monthly_cashflow(metta_kb, initial_capital: float, payment_schedule: Dict, units: int, retail_price: float, expected_monthly_sales: List[int], selling_channel: str) -> List[Dict]:
    monthly_cashflow = []

    for month_key in ["month_minus_4", "month_minus_2", "month_minus_1"]:
        if month_key in payment_schedule:
            month_data = payment_schedule[month_key]
            monthly_cashflow.append({
                "month": month_key,
                "month_number": get_month_number(month_key),
                "description": month_data["description"],
                "revenue": 0,
                "cogs_fulfilled": 0,
                "gross_profit": 0,
                "operating_expenses": month_data["total_outflow"],
                "net_cashflow": -month_data["total_outflow"]
            })

    monthly_cashflow.append({
        "month": "month_0",
        "month_number": 0,
        "description": "Launch Month - Inventory Receiving",
        "revenue": 0,
        "cogs_fulfilled": 0,
        "gross_profit": 0,
        "operating_expenses": 1000,
        "net_cashflow": -1000
    })

    channel_fee_pct = get_channel_fee_percentage(selling_channel)
    cogs_per_unit = (payment_schedule["month_minus_1"]["outflows"]["production_balance"] +
                     payment_schedule["month_minus_2"]["outflows"]["production_deposit"] +
                     payment_schedule["month_minus_1"]["outflows"]["freight_and_duties"]) / units

    for month_idx, units_sold in enumerate(expected_monthly_sales[:6], start=1):
        revenue = units_sold * retail_price
        cogs = units_sold * cogs_per_unit
        channel_fees = revenue * (channel_fee_pct / 100)
        payment_processing = revenue * 0.029
        fulfillment = units_sold * 3.50

        ops_expenses = channel_fees + payment_processing + fulfillment + 800

        gross_profit = revenue - cogs
        net_cashflow = revenue - cogs - ops_expenses

        monthly_cashflow.append({
            "month": f"month_{month_idx}",
            "month_number": month_idx,
            "description": f"Sales Month {month_idx}",
            "revenue": round(revenue, 2),
            "cogs_fulfilled": round(cogs, 2),
            "gross_profit": round(gross_profit, 2),
            "operating_expenses": round(ops_expenses, 2),
            "channel_fees": round(channel_fees, 2),
            "fulfillment_costs": round(fulfillment, 2),
            "net_cashflow": round(net_cashflow, 2)
        })

    return monthly_cashflow


def get_month_number(month_key: str) -> int:
    mapping = {
        "month_minus_4": -4,
        "month_minus_3": -3,
        "month_minus_2": -2,
        "month_minus_1": -1,
        "month_0": 0
    }
    return mapping.get(month_key, 0)


def get_channel_fee_percentage(channel: str) -> float:
    channel_fees = {
        "dtc-shopify": 2.9,
        "dtc-own": 0,
        "amazon": 15,
        "wholesale": 0,
        "marketplace": 12,
        "hybrid": 8
    }

    return channel_fees.get(channel.lower(), 10)


def calculate_cumulative_cash_position(initial_capital: float, monthly_cashflow: List[Dict]) -> Dict:
    cumulative = initial_capital
    positions = []
    lowest_point = initial_capital
    lowest_month = 0

    for month_data in monthly_cashflow:
        cumulative += month_data["net_cashflow"]
        positions.append({
            "month": month_data["month"],
            "month_number": month_data["month_number"],
            "net_cashflow": month_data["net_cashflow"],
            "cumulative_cash": round(cumulative, 2)
        })

        if cumulative < lowest_point:
            lowest_point = cumulative
            lowest_month = month_data["month_number"]

    return {
        "starting_capital": initial_capital,
        "monthly_positions": positions,
        "lowest_cash_point": round(lowest_point, 2),
        "lowest_cash_month": lowest_month,
        "final_cash_position": round(cumulative, 2)
    }


def assess_capital_requirements(cumulative_analysis: Dict, initial_capital: float, payment_schedule: Dict) -> Dict:
    lowest_point = cumulative_analysis["lowest_cash_point"]
    lowest_month = cumulative_analysis["lowest_cash_month"]

    if lowest_point < 0:
        additional_needed = abs(lowest_point) + 2000
        capital_sufficient = False
        recommendation = f"Initial capital insufficient. Need additional ${additional_needed:,.0f} to avoid negative cash flow."
    else:
        additional_needed = 0
        capital_sufficient = True
        recommendation = f"Initial capital sufficient. Lowest point ${lowest_point:,.0f} at month {lowest_month}."

    total_investment = initial_capital + additional_needed

    return {
        "initial_capital": initial_capital,
        "lowest_cash_point": lowest_point,
        "lowest_cash_month": lowest_month,
        "additional_capital_needed": round(additional_needed, 2),
        "total_capital_required": round(total_investment, 2),
        "capital_sufficient": capital_sufficient,
        "recommendation": recommendation,
        "funding_options": [
            "Personal savings or friends & family",
            "Small business loan ($10K-50K)",
            "Revenue-based financing (Clearco, Shopify Capital)",
            "Crowdfunding (Kickstarter for pre-orders)",
            "Angel investors or fashion accelerators"
        ] if not capital_sufficient else []
    }


def calculate_breakeven(monthly_cashflow: List[Dict], cumulative_analysis: Dict) -> Dict:
    breakeven_month = None
    breakeven_month_name = None

    for position in cumulative_analysis["monthly_positions"]:
        if position["cumulative_cash"] >= cumulative_analysis["starting_capital"] and position["month_number"] > 0:
            breakeven_month = position["month_number"]
            breakeven_month_name = position["month"]
            break

    total_revenue = sum(m["revenue"] for m in monthly_cashflow if m.get("revenue", 0) > 0)
    total_cogs = sum(m["cogs_fulfilled"] for m in monthly_cashflow if m.get("cogs_fulfilled", 0) > 0)
    gross_margin_pct = ((total_revenue - total_cogs) / total_revenue * 100) if total_revenue > 0 else 0

    return {
        "breakeven_achieved": breakeven_month is not None,
        "breakeven_month": breakeven_month,
        "breakeven_month_name": breakeven_month_name,
        "months_to_breakeven": breakeven_month if breakeven_month else "Not achieved in 6 months",
        "total_revenue_at_breakeven": round(sum(m["revenue"] for m in monthly_cashflow[:breakeven_month+5] if m.get("revenue")), 2) if breakeven_month else 0,
        "gross_margin_pct": round(gross_margin_pct, 1),
        "interpretation": f"Breakeven at month {breakeven_month}" if breakeven_month else "Breakeven not achieved within forecast period"
    }


def generate_pricing_recommendations(metta_kb, landed_cost: float, retail_price: float, positioning: str) -> Dict:
    markup = (retail_price / landed_cost) if landed_cost > 0 else 0
    gross_margin_pct = ((retail_price - landed_cost) / retail_price * 100) if retail_price > 0 else 0

    pricing_strategies = {
        "dtc-standard": {"multiplier_min": 2.5, "multiplier_max": 3.0, "margin_target": "60-67%"},
        "dtc-premium": {"multiplier_min": 3.5, "multiplier_max": 4.5, "margin_target": "70-78%"},
        "wholesale-retail": {"multiplier_min": 4.4, "multiplier_max": 5.5, "margin_target": "55-65%"},
        "budget-value": {"multiplier_min": 2.0, "multiplier_max": 2.5, "margin_target": "50-60%"}
    }

    strategy = pricing_strategies.get(positioning, pricing_strategies["dtc-standard"])

    optimal_price_min = landed_cost * strategy["multiplier_min"]
    optimal_price_max = landed_cost * strategy["multiplier_max"]

    optimal_price_rounded = round_to_99(optimal_price_min + (optimal_price_max - optimal_price_min) / 2)

    if markup < strategy["multiplier_min"]:
        pricing_health = "underpriced"
        recommendation = f"Increase price to ${optimal_price_rounded:.2f} for sustainable margins"
    elif markup > strategy["multiplier_max"]:
        pricing_health = "premium"
        recommendation = "Pricing at premium level - ensure brand story and quality justify"
    else:
        pricing_health = "optimal"
        recommendation = "Pricing is within optimal range for category"

    return {
        "landed_cost_per_unit": round(landed_cost, 2),
        "current_retail_price": round(retail_price, 2),
        "current_markup_multiplier": round(markup, 2),
        "current_gross_margin_pct": round(gross_margin_pct, 1),
        "recommended_retail_price": round(optimal_price_rounded, 2),
        "target_margin_range": strategy["margin_target"],
        "pricing_health": pricing_health,
        "recommendation": recommendation,
        "competitive_context": get_competitive_pricing_context(retail_price)
    }


def round_to_99(price: float) -> float:
    base = int(price / 10) * 10
    return base + 9.99 if price > 20 else round(price, 2)


def get_competitive_pricing_context(retail_price: float) -> str:
    if retail_price < 30:
        return "Budget/Fast Fashion tier (H&M, Uniqlo range)"
    elif retail_price < 60:
        return "Mid-market tier (Everlane, Allbirds range)"
    elif retail_price < 100:
        return "Premium Contemporary (Outdoor Voices, Girlfriend Collective)"
    elif retail_price < 200:
        return "Premium/Designer tier (Lululemon, Alo Yoga)"
    else:
        return "Luxury tier (Veilance, Stone Island)"


def plan_reorder_cashflow(metta_kb, initial_units: int, expected_monthly_sales: List[int], fob_per_unit: float, cumulative_analysis: Dict) -> Dict:
    cumulative_sold = 0
    reorder_month = None
    reorder_trigger_pct = 30

    for month_idx, units_sold in enumerate(expected_monthly_sales[:6], start=1):
        cumulative_sold += units_sold
        remaining_pct = ((initial_units - cumulative_sold) / initial_units * 100) if initial_units > 0 else 0

        if remaining_pct <= reorder_trigger_pct and reorder_month is None:
            reorder_month = month_idx
            break

    if reorder_month is None:
        return {
            "reorder_needed": False,
            "reasoning": "Inventory sufficient for 6+ months based on sales forecast"
        }

    reorder_units = int(initial_units * 0.6)
    reorder_fob_total = reorder_units * fob_per_unit
    reorder_deposit_40 = reorder_fob_total * 0.40

    cash_at_reorder_month = 0
    for pos in cumulative_analysis["monthly_positions"]:
        if pos["month_number"] == reorder_month:
            cash_at_reorder_month = pos["cumulative_cash"]
            break

    can_afford_reorder = cash_at_reorder_month >= reorder_deposit_40

    return {
        "reorder_needed": True,
        "reorder_trigger_month": reorder_month,
        "reorder_units": reorder_units,
        "reorder_total_cost": round(reorder_fob_total, 2),
        "reorder_deposit_40pct": round(reorder_deposit_40, 2),
        "cash_available_at_reorder": round(cash_at_reorder_month, 2),
        "can_afford_reorder": can_afford_reorder,
        "shortfall": round(max(0, reorder_deposit_40 - cash_at_reorder_month), 2),
        "recommendation": "Cash sufficient for reorder" if can_afford_reorder else f"Need ${reorder_deposit_40 - cash_at_reorder_month:,.0f} more capital for reorder"
    }


def model_risk_scenarios(monthly_cashflow: List[Dict], cumulative_analysis: Dict, initial_capital: float) -> List[Dict]:
    scenarios = []

    slower_sales_cashflow = []
    for month_data in monthly_cashflow:
        adjusted = month_data.copy()
        if adjusted.get("revenue", 0) > 0:
            adjusted["revenue"] *= 0.70
            adjusted["cogs_fulfilled"] *= 0.70
            adjusted["gross_profit"] *= 0.70
            adjusted["net_cashflow"] = adjusted["revenue"] - adjusted["cogs_fulfilled"] - adjusted["operating_expenses"]
        slower_sales_cashflow.append(adjusted)

    slower_cumulative = calculate_cumulative_cash_position(initial_capital, slower_sales_cashflow)

    scenarios.append({
        "scenario_name": "Slower Sales (30% below forecast)",
        "probability": "Medium",
        "lowest_cash_point": slower_cumulative["lowest_cash_point"],
        "lowest_cash_month": slower_cumulative["lowest_cash_month"],
        "final_cash_position": slower_cumulative["final_cash_position"],
        "impact": "Negative" if slower_cumulative["lowest_cash_point"] < 0 else "Manageable",
        "mitigation": "Reduce marketing spend, negotiate extended payment terms, plan earlier markdowns"
    })

    higher_costs_cashflow = []
    for month_data in monthly_cashflow:
        adjusted = month_data.copy()
        if adjusted.get("operating_expenses", 0) > 0:
            adjusted["operating_expenses"] *= 1.25
            adjusted["net_cashflow"] = adjusted.get("revenue", 0) - adjusted.get("cogs_fulfilled", 0) - adjusted["operating_expenses"]
        higher_costs_cashflow.append(adjusted)

    higher_costs_cumulative = calculate_cumulative_cash_position(initial_capital, higher_costs_cashflow)

    scenarios.append({
        "scenario_name": "Higher Operating Costs (25% above budget)",
        "probability": "Medium",
        "lowest_cash_point": higher_costs_cumulative["lowest_cash_point"],
        "lowest_cash_month": higher_costs_cumulative["lowest_cash_month"],
        "final_cash_position": higher_costs_cumulative["final_cash_position"],
        "impact": "Negative" if higher_costs_cumulative["lowest_cash_point"] < 0 else "Moderate",
        "mitigation": "Control marketing spend, negotiate better 3PL rates, reduce sampling iterations"
    })

    scenarios.append({
        "scenario_name": "Production Delay (1 month)",
        "probability": "Low-Medium",
        "impact_description": "Launch delayed, marketing spend wasted, potential lost pre-orders",
        "estimated_cost": "$3000-5000 in sunk marketing costs",
        "mitigation": "Choose reliable supplier, build timeline buffers, avoid peak season ordering"
    })

    return scenarios
