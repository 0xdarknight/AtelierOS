from uagents import Agent, Context
from typing import Dict, List, Tuple
import logging

from models.messages import InventoryForecastRequest, InventoryForecastResponse
from utils.config import Config
from utils.helpers import get_current_timestamp

logger = logging.getLogger(__name__)


def create_inventory_forecasting_agent(metta_kb):
    agent = Agent(
        name="inventory_demand_forecaster",
        seed=Config.AGENT_SEEDS.get("inventory_forecasting", "inventory_forecasting_seed_unique_004"),
        port=Config.AGENT_PORTS.get("inventory_forecasting", 8003),
        endpoint=Config.ENDPOINTS.get("inventory_forecasting", ["http://localhost:8003/submit"])
    )

    @agent.on_message(InventoryForecastRequest)
    async def handle_forecast_request(ctx: Context, sender: str, msg: InventoryForecastRequest):
        logger.info(f"Inventory Demand Forecaster: Processing request from {sender}")
        logger.info(f"Product: {msg.product_name}, Units: {msg.total_units}, Fit: {msg.fit_type}, Demo: {msg.target_demographic}")

        size_curve = calculate_size_curve(
            metta_kb,
            msg.fit_type,
            msg.target_demographic,
            msg.category
        )

        size_allocation = apply_size_curve(
            msg.total_units,
            size_curve
        )

        color_allocation = calculate_color_distribution(
            metta_kb,
            msg.colors,
            msg.total_units,
            msg.color_strategy
        )

        sku_matrix = generate_sku_matrix(
            msg.product_name,
            size_allocation,
            color_allocation
        )

        reorder_triggers = calculate_reorder_points(
            metta_kb,
            sku_matrix,
            msg.lead_time_weeks,
            msg.expected_weekly_sales
        )

        dead_stock_risks = identify_dead_stock_risks(
            sku_matrix,
            msg.expected_weekly_sales
        )

        sell_through_forecast = forecast_sell_through(
            metta_kb,
            msg.total_units,
            msg.expected_weekly_sales,
            msg.selling_season_weeks
        )

        recommendations = generate_inventory_recommendations(
            size_allocation,
            color_allocation,
            dead_stock_risks,
            sell_through_forecast
        )

        response = InventoryForecastResponse(
            request_id=msg.request_id,
            product_name=msg.product_name,
            total_units=msg.total_units,
            total_skus=len(sku_matrix),
            size_curve_applied=size_curve["name"],
            size_allocation=size_allocation,
            color_allocation=color_allocation,
            sku_matrix=sku_matrix,
            reorder_triggers=reorder_triggers,
            dead_stock_risks=dead_stock_risks,
            sell_through_forecast=sell_through_forecast,
            recommendations=recommendations,
            timestamp=get_current_timestamp()
        )

        await ctx.send(sender, response)
        logger.info(f"Sent inventory forecast: {len(sku_matrix)} SKUs, {len(dead_stock_risks)} dead stock risks")

    return agent


def calculate_size_curve(metta_kb, fit_type: str, demographic: str, category: str) -> Dict:
    size_curves = {
        "activewear-standard": {
            "name": "Activewear Standard Fit",
            "xs": 4,
            "s": 18,
            "m": 32,
            "l": 28,
            "xl": 14,
            "xxl": 4,
            "reasoning": "Athletic demographic, M/L bias"
        },
        "athletic-fit": {
            "name": "Athletic Fit (M/L Bias)",
            "xs": 3,
            "s": 16,
            "m": 34,
            "l": 30,
            "xl": 13,
            "xxl": 4,
            "reasoning": "Performance-focused consumers, muscular builds"
        },
        "relaxed-fit": {
            "name": "Relaxed Fit (Broader Distribution)",
            "xs": 5,
            "s": 20,
            "m": 30,
            "l": 25,
            "xl": 15,
            "xxl": 5,
            "reasoning": "Comfort-focused, less size concentration"
        },
        "plus-inclusive": {
            "name": "Plus-Inclusive Sizing",
            "xs": 6,
            "s": 18,
            "m": 26,
            "l": 24,
            "xl": 16,
            "xxl": 10,
            "reasoning": "Inclusive sizing strategy, stronger XL/XXL"
        },
        "streetwear": {
            "name": "Streetwear Oversized",
            "xs": 2,
            "s": 15,
            "m": 35,
            "l": 32,
            "xl": 12,
            "xxl": 4,
            "reasoning": "Trend toward larger sizes, drop shoulder fits"
        },
        "womens-fashion": {
            "name": "Women's Fashion Standard",
            "xs": 8,
            "s": 24,
            "m": 32,
            "l": 22,
            "xl": 10,
            "xxl": 4,
            "reasoning": "Traditional women's sizing, S/M peak"
        }
    }

    key = f"{category}-{fit_type}".lower()

    for curve_key in size_curves:
        if curve_key in key or fit_type.lower() in curve_key:
            return size_curves[curve_key]

    if "athletic" in fit_type.lower():
        return size_curves["athletic-fit"]
    elif "relaxed" in fit_type.lower() or "oversized" in fit_type.lower():
        return size_curves["relaxed-fit"]
    elif "inclusive" in fit_type.lower() or "plus" in fit_type.lower():
        return size_curves["plus-inclusive"]
    elif "womens" in demographic.lower() or "female" in demographic.lower():
        return size_curves["womens-fashion"]

    return size_curves["activewear-standard"]


def apply_size_curve(total_units: int, size_curve: Dict) -> Dict:
    allocation = {}

    sizes = ["xs", "s", "m", "l", "xl", "xxl"]

    for size in sizes:
        percentage = size_curve.get(size, 0)
        units = int(round(total_units * (percentage / 100)))
        allocation[size.upper()] = {
            "percentage": percentage,
            "units": units
        }

    allocated_total = sum(a["units"] for a in allocation.values())
    diff = total_units - allocated_total

    if diff != 0:
        allocation["M"]["units"] += diff

    return allocation


def calculate_color_distribution(metta_kb, colors: List[str], total_units: int, strategy: str) -> Dict:
    num_colors = len(colors)

    if num_colors == 0:
        return {}

    if strategy == "neutral-heavy":
        if num_colors == 1:
            return {colors[0]: {"percentage": 100, "units": total_units}}
        elif num_colors == 2:
            return {
                colors[0]: {"percentage": 60, "units": int(total_units * 0.60)},
                colors[1]: {"percentage": 40, "units": int(total_units * 0.40)}
            }
        elif num_colors == 3:
            return {
                colors[0]: {"percentage": 40, "units": int(total_units * 0.40)},
                colors[1]: {"percentage": 35, "units": int(total_units * 0.35)},
                colors[2]: {"percentage": 25, "units": int(total_units * 0.25)}
            }
        else:
            return distribute_evenly_with_bias(colors, total_units, bias_first=True)

    elif strategy == "balanced":
        percentages = [100 // num_colors] * num_colors
        remainder = 100 - sum(percentages)
        percentages[0] += remainder

        distribution = {}
        for i, color in enumerate(colors):
            units = int(total_units * (percentages[i] / 100))
            distribution[color] = {"percentage": percentages[i], "units": units}

        return distribution

    elif strategy == "trend-accent":
        if num_colors <= 2:
            return calculate_color_distribution(metta_kb, colors, total_units, "balanced")
        else:
            neutrals_pct = 75
            accent_pct = 25

            num_neutrals = num_colors - 1
            neutral_each = neutrals_pct // num_neutrals

            distribution = {}
            for i, color in enumerate(colors):
                if i < num_neutrals:
                    pct = neutral_each
                else:
                    pct = accent_pct

                distribution[color] = {
                    "percentage": pct,
                    "units": int(total_units * (pct / 100))
                }

            return distribution

    return distribute_evenly_with_bias(colors, total_units, bias_first=False)


def distribute_evenly_with_bias(colors: List[str], total_units: int, bias_first: bool) -> Dict:
    num_colors = len(colors)
    base_pct = 100 // num_colors
    remainder = 100 - (base_pct * num_colors)

    distribution = {}
    for i, color in enumerate(colors):
        pct = base_pct
        if i == 0 and bias_first:
            pct += remainder

        distribution[color] = {
            "percentage": pct,
            "units": int(total_units * (pct / 100))
        }

    allocated_total = sum(d["units"] for d in distribution.values())
    diff = total_units - allocated_total
    if diff != 0:
        distribution[colors[0]]["units"] += diff

    return distribution


def generate_sku_matrix(product_name: str, size_allocation: Dict, color_allocation: Dict) -> List[Dict]:
    sku_matrix = []

    sku_counter = 1
    for color, color_data in color_allocation.items():
        color_total = color_data["units"]

        for size, size_data in size_allocation.items():
            size_pct = size_data["percentage"] / 100

            sku_units = int(round(color_total * size_pct))

            sku_code = f"{product_name[:3].upper()}-{color[:3].upper()}-{size}"

            sku_matrix.append({
                "sku_code": sku_code,
                "color": color,
                "size": size,
                "units": sku_units,
                "status": "pending_production"
            })

            sku_counter += 1

    return sku_matrix


def calculate_reorder_points(metta_kb, sku_matrix: List[Dict], lead_time_weeks: int, expected_weekly_sales: float) -> List[Dict]:
    reorder_triggers = []

    avg_weekly_per_sku = expected_weekly_sales / len(sku_matrix) if len(sku_matrix) > 0 else 0

    safety_stock_weeks = 2

    for sku in sku_matrix:
        initial_stock = sku["units"]

        size_multiplier = get_size_velocity_multiplier(sku["size"])
        sku_weekly_sales = avg_weekly_per_sku * size_multiplier

        lead_time_demand = sku_weekly_sales * lead_time_weeks
        safety_stock = sku_weekly_sales * safety_stock_weeks

        reorder_point = lead_time_demand + safety_stock

        reorder_quantity = int(lead_time_demand + safety_stock)

        weeks_of_inventory = initial_stock / sku_weekly_sales if sku_weekly_sales > 0 else 999

        reorder_triggers.append({
            "sku_code": sku["sku_code"],
            "initial_stock": initial_stock,
            "expected_weekly_sales": round(sku_weekly_sales, 1),
            "reorder_point": int(reorder_point),
            "reorder_quantity": reorder_quantity,
            "lead_time_weeks": lead_time_weeks,
            "safety_stock_units": int(safety_stock),
            "weeks_of_inventory": round(weeks_of_inventory, 1),
            "reorder_urgency": "high" if weeks_of_inventory < lead_time_weeks else "medium" if weeks_of_inventory < lead_time_weeks + 4 else "low"
        })

    return reorder_triggers


def get_size_velocity_multiplier(size: str) -> float:
    multipliers = {
        "XS": 0.5,
        "S": 0.9,
        "M": 1.3,
        "L": 1.1,
        "XL": 0.8,
        "XXL": 0.5
    }

    return multipliers.get(size.upper(), 1.0)


def identify_dead_stock_risks(sku_matrix: List[Dict], expected_weekly_sales: float) -> List[Dict]:
    dead_stock_risks = []

    avg_weekly_per_sku = expected_weekly_sales / len(sku_matrix) if len(sku_matrix) > 0 else 0

    for sku in sku_matrix:
        size_multiplier = get_size_velocity_multiplier(sku["size"])
        sku_weekly_sales = avg_weekly_per_sku * size_multiplier

        weeks_to_sell = sku["units"] / sku_weekly_sales if sku_weekly_sales > 0 else 999

        if weeks_to_sell > 20:
            risk_level = "high"
            recommendation = f"Reduce units by 40-50% in next order. Consider markdown at week 8."
        elif weeks_to_sell > 12:
            risk_level = "medium"
            recommendation = f"Monitor closely. Potential markdown needed at week 10-12."
        else:
            continue

        dead_stock_risks.append({
            "sku_code": sku["sku_code"],
            "units": sku["units"],
            "estimated_weeks_to_sell": round(weeks_to_sell, 1),
            "risk_level": risk_level,
            "recommendation": recommendation,
            "markdown_timing": "Week 8-10" if risk_level == "high" else "Week 10-14",
            "markdown_percentage": "30-40%" if risk_level == "high" else "20-30%"
        })

    return dead_stock_risks


def forecast_sell_through(metta_kb, total_units: int, expected_weekly_sales: float, selling_season_weeks: int) -> Dict:
    total_expected_sales = expected_weekly_sales * selling_season_weeks

    sell_through_pct = (total_expected_sales / total_units * 100) if total_units > 0 else 0

    weeks_to_sell_out = total_units / expected_weekly_sales if expected_weekly_sales > 0 else 999

    if sell_through_pct >= 85:
        performance = "excellent"
        risk = "Potential stockout risk - consider reorder timing"
    elif sell_through_pct >= 70:
        performance = "good"
        risk = "Healthy sell-through expected"
    elif sell_through_pct >= 50:
        performance = "moderate"
        risk = "Some dead stock likely - plan markdowns"
    else:
        performance = "poor"
        risk = "Significant dead stock risk - reduce next order"

    monthly_breakdown = []
    for month in range(1, min(7, int(weeks_to_sell_out // 4) + 2)):
        month_start_week = (month - 1) * 4
        month_end_week = month * 4

        if month_end_week > selling_season_weeks:
            month_end_week = selling_season_weeks

        weeks_in_month = month_end_week - month_start_week
        units_sold_month = int(expected_weekly_sales * weeks_in_month)

        cumulative_sold = int(expected_weekly_sales * month_end_week)
        remaining = max(0, total_units - cumulative_sold)

        monthly_breakdown.append({
            "month": month,
            "weeks": f"{month_start_week+1}-{month_end_week}",
            "units_sold": units_sold_month,
            "cumulative_sold": cumulative_sold,
            "remaining_inventory": remaining,
            "inventory_weeks_remaining": round(remaining / expected_weekly_sales, 1) if expected_weekly_sales > 0 else 0
        })

    return {
        "total_units": total_units,
        "expected_total_sales": int(total_expected_sales),
        "expected_sell_through_pct": round(sell_through_pct, 1),
        "weeks_to_sell_out": round(weeks_to_sell_out, 1),
        "performance_rating": performance,
        "risk_assessment": risk,
        "monthly_breakdown": monthly_breakdown
    }


def generate_inventory_recommendations(size_allocation: Dict, color_allocation: Dict, dead_stock_risks: List[Dict], sell_through_forecast: Dict) -> List[str]:
    recommendations = []

    xs_pct = size_allocation.get("XS", {}).get("percentage", 0)
    xxl_pct = size_allocation.get("XXL", {}).get("percentage", 0)

    if xs_pct > 5 or xxl_pct > 5:
        recommendations.append(f"Consider reducing XS ({xs_pct}%) and XXL ({xxl_pct}%) to 3-4% each. These sizes typically have lowest velocity.")

    if len(color_allocation) > 3:
        recommendations.append(f"You have {len(color_allocation)} colors. Consider consolidating to 3 core colors to reduce SKU complexity and meet fabric MOQs.")

    high_risk_count = len([r for r in dead_stock_risks if r["risk_level"] == "high"])
    if high_risk_count > 0:
        recommendations.append(f"{high_risk_count} SKUs at high dead stock risk. Plan markdowns early (week 8-10) to clear inventory.")

    sell_through = sell_through_forecast.get("expected_sell_through_pct", 0)
    if sell_through > 90:
        recommendations.append("Strong sell-through forecast (>90%). Consider producing 10-15% more units or planning faster reorder.")
    elif sell_through < 60:
        recommendations.append(f"Low sell-through forecast ({sell_through:.0f}%). Reduce initial order by 20-30% to minimize dead stock risk.")

    m_units = size_allocation.get("M", {}).get("units", 0)
    l_units = size_allocation.get("L", {}).get("units", 0)
    ml_total_pct = size_allocation.get("M", {}).get("percentage", 0) + size_allocation.get("L", {}).get("percentage", 0)

    if ml_total_pct < 55:
        recommendations.append(f"M+L allocation is {ml_total_pct:.0f}%. Consider increasing to 60-65% as these are fastest-moving sizes.")

    if len(recommendations) == 0:
        recommendations.append("Inventory allocation looks well-optimized. Monitor actual sales data and adjust for reorders.")

    return recommendations
