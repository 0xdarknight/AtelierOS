from uagents import Agent, Context
from datetime import datetime
import logging

from models.messages import (
    BudgetValidationRequest,
    FinancialApproval,
    DesignBriefRequest,
    QualityIssueAlert,
    ApprovalMessage,
    FinancialReport
)
from utils.metta_loader import MettaKnowledgeBase
from utils.config import Config
from utils.helpers import (
    calculate_margin,
    calculate_roi,
    calculate_total_variable_cost,
    calculate_fees,
    get_current_timestamp
)

logger = logging.getLogger(__name__)


def create_financial_operations_agent(metta_kb: MettaKnowledgeBase,
                                       design_sourcing_address: str):
    agent = Agent(
        name="financial_operations",
        seed=Config.AGENT_SEEDS["financial_operations"],
        port=Config.AGENT_PORTS["financial_operations"],
        endpoint=Config.ENDPOINTS["financial_operations"]
    )

    @agent.on_message(BudgetValidationRequest)
    async def validate_budget(ctx: Context, sender: str, msg: BudgetValidationRequest):
        logger.info("Financial Operations: Validating budget request")

        concept = msg.concept
        strategy = msg.strategy
        units = msg.estimated_units

        estimated_cogs = estimate_cogs_from_category(concept["category"])
        retail_price = extract_price_from_range(strategy["price_range"])

        fixed_costs = calculate_fixed_costs()
        variable_cost_per_unit = calculate_variable_cost_per_unit(estimated_cogs)
        total_production_cost = estimated_cogs * units

        shipping_estimate = units * 3.50
        warehousing_estimate = units * 2.00
        marketing_budget = 3000
        samples_budget = 2000

        total_costs = (total_production_cost + shipping_estimate +
                       warehousing_estimate + marketing_budget +
                       samples_budget + fixed_costs)

        sell_through_rate = 0.80
        units_sold = int(units * sell_through_rate)
        projected_revenue = retail_price * units_sold

        marketplace_fees = units_sold * retail_price * (Config.MARKETPLACE_FEE_PERCENT / 100)
        payment_fees = units_sold * retail_price * (Config.PAYMENT_PROCESSING_PERCENT / 100)
        total_fees = marketplace_fees + payment_fees

        projected_profit = projected_revenue - total_costs - total_fees

        break_even = calculate_break_even_units(
            total_costs,
            retail_price,
            variable_cost_per_unit
        )

        roi = calculate_roi(projected_profit, total_costs) if total_costs > 0 else 0

        gross_margin = calculate_margin(retail_price, estimated_cogs)

        approved = (projected_profit > 0 and
                    roi >= Config.MIN_ROI_PERCENT and
                    gross_margin >= Config.MIN_MARGIN_PERCENT and
                    total_costs <= concept["budget"])

        cash_flow_analysis = generate_cash_flow_analysis(
            total_costs, projected_revenue, units
        )

        reasoning = generate_approval_reasoning(
            approved, projected_profit, roi, gross_margin, total_costs, concept["budget"]
        )

        logger.info(f"Financial Analysis: Profit=${projected_profit:.0f}, ROI={roi:.1f}%, Approved={approved}")

        approval = FinancialApproval(
            approved=approved,
            total_cost=total_costs,
            projected_revenue=projected_revenue,
            projected_profit=projected_profit,
            break_even_units=break_even,
            roi_percent=roi,
            cash_flow_analysis=cash_flow_analysis,
            reasoning=reasoning,
            timestamp=get_current_timestamp()
        )

        await ctx.send(sender, approval)

        if approved:
            logger.info("Budget approved, sending design brief to design & sourcing")

            design_brief = DesignBriefRequest(
                concept=concept,
                strategy=strategy,
                budget_approved=True,
                financial_constraints={
                    "max_cogs": estimated_cogs,
                    "target_retail_price": retail_price,
                    "units": units,
                    "total_budget": concept["budget"]
                },
                timestamp=get_current_timestamp()
            )

            await ctx.send(design_sourcing_address, design_brief)

    @agent.on_message(QualityIssueAlert)
    async def evaluate_quality_issue(ctx: Context, sender: str, msg: QualityIssueAlert):
        logger.info(f"Financial Operations: Evaluating quality issue - {msg.issue_type}")

        approved = msg.fix_cost < 500 and msg.delay_days < 7

        reasoning = f"Fix cost ${msg.fix_cost:.0f} and {msg.delay_days} day delay"
        if approved:
            reasoning += " - Within acceptable thresholds, approved"
        else:
            reasoning += " - Exceeds thresholds, requires review"

        logger.info(f"Quality issue decision: {reasoning}")

        approval = ApprovalMessage(
            approved=approved,
            request_type="quality_issue_fix",
            reasoning=reasoning,
            timestamp=get_current_timestamp()
        )

        await ctx.send(sender, approval)

    return agent


def estimate_cogs_from_category(category: str) -> float:
    cogs_map = {
        "activewear": 45.0,
        "streetwear": 38.0,
        "luxury": 68.0
    }
    return cogs_map.get(category, 45.0)


def extract_price_from_range(price_range: str) -> float:
    parts = price_range.split("-")
    if len(parts) == 2:
        try:
            low = float(parts[0])
            high = float(parts[1])
            return (low + high) / 2
        except ValueError:
            pass
    return 95.0


def calculate_fixed_costs() -> float:
    return (500 + 300 + 1500 + 200)


def calculate_variable_cost_per_unit(cogs: float) -> float:
    shipping = 3.50
    warehousing = 2.00
    packaging = 1.50
    marketing_per_unit = 15.0

    return cogs + shipping + warehousing + packaging + marketing_per_unit


def calculate_break_even_units(total_fixed_costs: float, retail_price: float,
                                 variable_cost: float) -> int:
    contribution_margin = retail_price - variable_cost
    if contribution_margin <= 0:
        return 0

    marketplace_fee = retail_price * (Config.MARKETPLACE_FEE_PERCENT / 100)
    payment_fee = retail_price * (Config.PAYMENT_PROCESSING_PERCENT / 100)
    net_contribution = contribution_margin - marketplace_fee - payment_fee

    if net_contribution <= 0:
        return 0

    break_even = total_fixed_costs / net_contribution
    return int(break_even) + 1


def generate_cash_flow_analysis(total_costs: float, projected_revenue: float,
                                 units: int) -> dict:
    production_payment = total_costs * 0.70
    sample_payment = 2000
    marketing_launch = 3000

    initial_sales = projected_revenue * 0.40
    month2_sales = projected_revenue * 0.35
    month3_sales = projected_revenue * 0.25

    return {
        "month_minus_2": {
            "outflow": sample_payment,
            "inflow": 0,
            "net": -sample_payment
        },
        "month_minus_1": {
            "outflow": production_payment,
            "inflow": 0,
            "net": -production_payment
        },
        "month_0": {
            "outflow": marketing_launch,
            "inflow": 0,
            "net": -marketing_launch
        },
        "month_1": {
            "outflow": 1000,
            "inflow": initial_sales,
            "net": initial_sales - 1000
        },
        "month_2": {
            "outflow": 1200,
            "inflow": month2_sales,
            "net": month2_sales - 1200
        },
        "month_3": {
            "outflow": 1000,
            "inflow": month3_sales,
            "net": month3_sales - 1000
        }
    }


def generate_approval_reasoning(approved: bool, profit: float, roi: float,
                                gross_margin: float, total_cost: float,
                                budget: float) -> str:
    if not approved:
        reasons = []
        if profit <= 0:
            reasons.append(f"Negative profit projection (${profit:.0f})")
        if roi < Config.MIN_ROI_PERCENT:
            reasons.append(f"ROI {roi:.1f}% below minimum {Config.MIN_ROI_PERCENT}%")
        if gross_margin < Config.MIN_MARGIN_PERCENT:
            reasons.append(f"Margin {gross_margin:.1f}% below minimum {Config.MIN_MARGIN_PERCENT}%")
        if total_cost > budget:
            reasons.append(f"Cost ${total_cost:.0f} exceeds budget ${budget:.0f}")

        return "REJECTED: " + "; ".join(reasons)

    return (f"APPROVED: Projected profit ${profit:.0f}, "
            f"ROI {roi:.1f}%, "
            f"Gross margin {gross_margin:.1f}%, "
            f"within budget")
