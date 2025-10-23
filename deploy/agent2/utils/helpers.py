from datetime import datetime, timedelta
from typing import Dict, List, Any
import hashlib


def format_currency(amount: float, currency: str = "USD") -> str:
    if currency == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f} {currency}"


def calculate_margin(revenue: float, cost: float) -> float:
    if revenue == 0:
        return 0.0
    return ((revenue - cost) / revenue) * 100


def generate_sku(product_name: str, size: str, color: str, variant_id: int) -> str:
    base = product_name.upper().replace(" ", "-")[:10]
    size_code = size.upper()
    color_code = color.upper()[:3]
    sku = f"{base}-{size_code}-{color_code}-{variant_id:03d}"
    return sku


def parse_metta_result(result: Any) -> Dict:
    if isinstance(result, dict):
        return result
    elif isinstance(result, (list, tuple)):
        if len(result) == 2:
            return {"key": result[0], "value": result[1]}
        elif len(result) == 3:
            return {"key": result[0], "value": result[1], "metadata": result[2]}
    return {"raw": str(result)}


def calculate_lead_time(start_date: str, days: int) -> str:
    start = datetime.fromisoformat(start_date)
    end = start + timedelta(days=days)
    return end.isoformat()


def generate_sample_id(product_name: str, timestamp: str) -> str:
    hash_input = f"{product_name}{timestamp}".encode('utf-8')
    hash_hex = hashlib.md5(hash_input).hexdigest()[:8]
    product_code = product_name.upper().replace(" ", "-")[:15]
    return f"SAMPLE-{product_code}-{hash_hex.upper()}"


def calculate_size_allocation(total_units: int, size_distribution: Dict[str, float]) -> Dict[str, int]:
    allocation = {}
    remaining = total_units

    sorted_sizes = sorted(size_distribution.items(), key=lambda x: x[1], reverse=True)

    for size, percentage in sorted_sizes[:-1]:
        units = int(total_units * percentage)
        allocation[size] = units
        remaining -= units

    allocation[sorted_sizes[-1][0]] = remaining

    return allocation


def calculate_reorder_point(avg_daily_sales: float, lead_time_days: int, safety_stock_days: int) -> int:
    demand_during_lead_time = avg_daily_sales * lead_time_days
    safety_stock = avg_daily_sales * safety_stock_days
    return int(demand_during_lead_time + safety_stock)


def calculate_total_variable_cost(cogs: float, shipping: float, warehousing: float,
                                   packaging: float, marketing: float) -> float:
    return cogs + shipping + warehousing + packaging + marketing


def calculate_fees(retail_price: float, marketplace_fee_pct: float,
                   payment_processing_pct: float) -> float:
    marketplace_fee = retail_price * (marketplace_fee_pct / 100)
    payment_fee = retail_price * (payment_processing_pct / 100)
    return marketplace_fee + payment_fee


def validate_moq(requested_units: int, supplier_moq: int) -> bool:
    return requested_units >= supplier_moq


def estimate_shipping_date(production_complete_date: str, shipping_days: int) -> str:
    production_date = datetime.fromisoformat(production_complete_date)
    shipping_date = production_date + timedelta(days=shipping_days)
    return shipping_date.isoformat()


def calculate_roi(net_profit: float, total_investment: float) -> float:
    if total_investment == 0:
        return 0.0
    return (net_profit / total_investment) * 100


def generate_tracking_number(shipment_id: str) -> str:
    hash_input = f"{shipment_id}{datetime.utcnow().isoformat()}".encode('utf-8')
    return f"TRK{hashlib.sha256(hash_input).hexdigest()[:12].upper()}"


def parse_quality_issues(issues: List[str]) -> List[Dict]:
    parsed = []
    for issue in issues:
        parts = issue.split("_")
        parsed.append({
            "type": issue,
            "category": parts[0] if parts else "unknown",
            "description": " ".join(parts).replace("_", " ").title()
        })
    return parsed


def calculate_inventory_value(units: int, cost_per_unit: float) -> float:
    return units * cost_per_unit


def get_current_timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"


def format_percentage(value: float) -> str:
    return f"{value:.1f}%"


def extract_numeric_from_string(text: str) -> float:
    import re
    numbers = re.findall(r'\d+\.?\d*', text)
    return float(numbers[0]) if numbers else 0.0
