from uagents import Model
from typing import List, Dict, Optional


class BOMCostingRequest(Model):
    request_id: str
    garment_type: str
    size: str
    fabric_type: str
    supplier: str
    units: int
    colors: Optional[List[str]] = None
    additional_trims: Optional[Dict] = None


class BOMCostingResponse(Model):
    request_id: str
    garment_type: str
    size: str
    fabric_type: str
    supplier: str
    units: int
    fabric_consumption_meters: float
    fabric_cost: float
    trim_costs: Dict
    labor_cost: float
    overhead_cost: float
    factory_profit: float
    fob_cost_per_unit: float
    fob_cost_total: float
    freight_cost_per_unit: float
    duty_cost_per_unit: float
    customs_broker_per_unit: float
    receiving_per_unit: float
    inspection_per_unit: float
    landed_cost_per_unit: float
    landed_cost_total: float
    recommended_retail_price: float
    gross_margin_percentage: float
    cost_breakdown: Dict
    timestamp: str


class MOQNegotiationRequest(Model):
    request_id: str
    category: str
    num_styles: int
    target_units: int
    budget: float
    timing_month: Optional[str] = None
    payment_flexibility: Optional[str] = None
    fabrics: Optional[List[str]] = None
    colors: Optional[List[str]] = None


class MOQNegotiationResponse(Model):
    request_id: str
    recommended_supplier: str
    negotiation_strategies: List[Dict]
    consolidation_opportunities: Dict
    expected_success_rate: float
    estimated_final_moq: int
    total_units_required: int
    alternative_options: List[Dict]
    timestamp: str


class ProductionTimelineRequest(Model):
    request_id: str
    garment_type: str
    units: int
    supplier: str
    order_month: Optional[str] = None
    target_launch_date: Optional[str] = None
    complexity: Optional[str] = None


class ProductionTimelineResponse(Model):
    request_id: str
    supplier: str
    total_timeline_days: int
    production_phases: List[Dict]
    quality_gates: List[Dict]
    risk_factors: List[Dict]
    critical_path: List[Dict]
    is_timeline_achievable: bool
    buffer_recommendation_days: int
    expedite_options: List[Dict]
    estimated_completion_date: str
    timestamp: str


class InventoryForecastRequest(Model):
    request_id: str
    product_name: str
    total_units: int
    fit_type: str
    target_demographic: str
    category: str
    colors: List[str]
    color_strategy: str
    lead_time_weeks: int
    expected_weekly_sales: float
    selling_season_weeks: int


class InventoryForecastResponse(Model):
    request_id: str
    product_name: str
    total_units: int
    total_skus: int
    size_curve_applied: str
    size_allocation: Dict
    color_allocation: Dict
    sku_matrix: List[Dict]
    reorder_triggers: List[Dict]
    dead_stock_risks: List[Dict]
    sell_through_forecast: Dict
    recommendations: List[str]
    timestamp: str


class CashFlowRequest(Model):
    request_id: str
    initial_capital: float
    fob_cost_per_unit: float
    landed_cost_per_unit: float
    units: int
    retail_price: float
    expected_monthly_sales: List[int]
    payment_terms: str
    selling_channel: str
    positioning_strategy: str


class CashFlowResponse(Model):
    request_id: str
    initial_capital: float
    payment_schedule: Dict
    monthly_cashflow: List[Dict]
    cumulative_cash_position: Dict
    capital_requirements: Dict
    breakeven_analysis: Dict
    pricing_recommendations: Dict
    reorder_planning: Dict
    risk_scenarios: List[Dict]
    timestamp: str
