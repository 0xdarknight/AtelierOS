from uagents import Agent, Context
import logging
import asyncio
from typing import Dict, List

from models.messages import (
    ProductionCompleteMessage,
    InventoryAllocationPlan,
    ReorderRequest,
    ShippingCoordination
)
from utils.metta_loader import MettaKnowledgeBase
from utils.config import Config
from utils.helpers import (
    calculate_size_allocation,
    calculate_reorder_point,
    generate_tracking_number,
    get_current_timestamp
)

logger = logging.getLogger(__name__)


def create_logistics_fulfillment_agent(metta_kb: MettaKnowledgeBase,
                                         production_coordinator_address: str):
    agent = Agent(
        name="logistics_fulfillment",
        seed=Config.AGENT_SEEDS["logistics_fulfillment"],
        port=Config.AGENT_PORTS["logistics_fulfillment"],
        endpoint=Config.ENDPOINTS["logistics_fulfillment"]
    )

    inventory_state = {}

    @agent.on_message(ProductionCompleteMessage)
    async def coordinate_shipping(ctx: Context, sender: str, msg: ProductionCompleteMessage):
        logger.info(f"Logistics & Fulfillment: Processing shipment for {msg.product_name}")
        logger.info(f"Units: {msg.units}, Location: {msg.location}")

        shipping_cost = calculate_shipping_cost(msg.location, msg.units)
        shipping_days = get_shipping_duration(msg.location)

        shipment_id = f"SHIP-{msg.product_id}-{hash(get_current_timestamp()) % 10000:04d}"
        tracking_number = generate_tracking_number(shipment_id)

        shipping_coordination = ShippingCoordination(
            shipment_id=shipment_id,
            origin=msg.location,
            destination=Config.DEFAULT_WAREHOUSE_LOCATION,
            units=msg.units,
            shipping_method="Sea Freight",
            cost=shipping_cost,
            estimated_delivery=f"{shipping_days} days",
            tracking_number=tracking_number,
            timestamp=get_current_timestamp()
        )

        logger.info(f"Shipping booked: {msg.location} → {Config.DEFAULT_WAREHOUSE_LOCATION}")
        logger.info(f"Cost: ${shipping_cost:.2f}, ETA: {shipping_days} days, Tracking: {tracking_number}")

        await asyncio.sleep(0.2)

        logger.info("Calculating optimal inventory allocation...")

        size_allocation = calculate_size_allocation(
            msg.units,
            Config.SIZE_DISTRIBUTION_DEFAULT
        )

        allocations = []
        for size, qty in size_allocation.items():
            allocations.append({
                "size": size,
                "quantity": qty,
                "percentage": (qty / msg.units) * 100
            })

        allocation_plan = InventoryAllocationPlan(
            product_id=msg.product_id,
            total_units=msg.units,
            allocations=allocations,
            warehouse_location=Config.DEFAULT_WAREHOUSE_LOCATION,
            receiving_date=f"{shipping_days} days from now",
            timestamp=get_current_timestamp()
        )

        logger.info("Inventory allocation plan:")
        for alloc in allocations:
            logger.info(f"  Size {alloc['size']}: {alloc['quantity']} units ({alloc['percentage']:.1f}%)")

        inventory_state[msg.product_id] = {
            "product_name": msg.product_name,
            "total_units": msg.units,
            "allocations": allocations,
            "status": "in_transit",
            "shipment_id": shipment_id
        }

        await asyncio.sleep(0.2)

        logger.info(f"Inventory received at {Config.DEFAULT_WAREHOUSE_LOCATION}")
        inventory_state[msg.product_id]["status"] = "in_warehouse"

        await simulate_sales_and_reorder(
            ctx, msg.product_id, msg.product_name, size_allocation,
            production_coordinator_address
        )

    return agent


async def simulate_sales_and_reorder(ctx: Context, product_id: str, product_name: str,
                                      size_allocation: Dict[str, int],
                                      production_address: str):

    await asyncio.sleep(0.2)

    logger.info("Store launched - tracking sales...")

    sales_velocity = {
        "M": 0.35,
        "L": 0.28,
        "S": 0.20,
        "XL": 0.12,
        "XS": 0.03,
        "XXL": 0.02
    }

    current_stock = size_allocation.copy()

    await asyncio.sleep(0.15)

    for size in ["M", "L"]:
        units_sold = int(size_allocation[size] * sales_velocity[size])
        current_stock[size] -= units_sold

        logger.info(f"Size {size}: {units_sold} units sold, {current_stock[size]} remaining")

    for size, stock in current_stock.items():
        initial_stock = size_allocation[size]
        stock_percent = (stock / initial_stock) * 100 if initial_stock > 0 else 0

        if stock_percent <= Config.REORDER_THRESHOLD_PERCENT:
            logger.warning(f"Size {size} at reorder threshold: {stock} units ({stock_percent:.1f}%)")

            avg_daily_sales = (initial_stock - stock) / 7
            reorder_qty = calculate_reorder_quantity(
                current_stock=stock,
                avg_daily_sales=avg_daily_sales,
                lead_time_days=Config.BULK_PRODUCTION_DAYS,
                safety_stock_days=Config.SAFETY_STOCK_DAYS
            )

            if reorder_qty > 0:
                sku = f"{product_id}-{size}"

                stockout_days = int(stock / avg_daily_sales) if avg_daily_sales > 0 else 30

                reorder = ReorderRequest(
                    sku=sku,
                    product_name=product_name,
                    current_stock=stock,
                    quantity=reorder_qty,
                    urgency="high" if stockout_days < 14 else "medium",
                    estimated_stockout_date=f"{stockout_days} days",
                    reason=f"Stock at {stock_percent:.1f}%, approaching stockout",
                    timestamp=get_current_timestamp()
                )

                await ctx.send(production_address, reorder)
                logger.info(f"Reorder request sent: {reorder_qty} units of size {size}")

    await asyncio.sleep(0.2)

    returns_count = int(sum(size_allocation.values()) * 0.08)
    logger.info(f"Processing {returns_count} returns...")

    return_conditions = {
        "light_wear": int(returns_count * 0.60),
        "deodorant_stain": int(returns_count * 0.25),
        "damaged": int(returns_count * 0.15)
    }

    restocked = process_returns(return_conditions)
    logger.info(f"Returns processed: {restocked} units restocked, {returns_count - restocked} liquidated")


def calculate_shipping_cost(origin: str, units: int) -> float:
    cost_per_unit_map = {
        "Vietnam": 3.50,
        "China": 2.80,
        "Portugal": 8.50,
        "Bangladesh": 2.50,
        "Taiwan": 3.20,
        "USA": 1.20
    }

    base_cost = 850

    for location, cost_per_unit in cost_per_unit_map.items():
        if location in origin:
            return base_cost

    return base_cost


def get_shipping_duration(origin: str) -> int:
    duration_map = {
        "Vietnam": 14,
        "China": 16,
        "Portugal": 21,
        "Bangladesh": 18,
        "Taiwan": 15,
        "USA": 2
    }

    for location, days in duration_map.items():
        if location in origin:
            return days

    return 14


def calculate_reorder_quantity(current_stock: int, avg_daily_sales: float,
                                lead_time_days: int, safety_stock_days: int) -> int:
    demand_during_lead = avg_daily_sales * lead_time_days
    safety_stock = avg_daily_sales * safety_stock_days
    optimal_stock = demand_during_lead + safety_stock

    reorder_qty = optimal_stock - current_stock

    return max(0, int(reorder_qty))


def process_returns(return_conditions: Dict[str, int]) -> int:
    restocked = 0

    restock_decisions = {
        "light_wear": True,
        "deodorant_stain": False,
        "damaged": False
    }

    for condition, count in return_conditions.items():
        if restock_decisions.get(condition, False):
            restocked += count
            logger.info(f"  {condition}: {count} units restocked")
        else:
            logger.info(f"  {condition}: {count} units liquidated")

    return restocked
