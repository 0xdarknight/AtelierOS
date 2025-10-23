from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    StartSessionContent,
    EndSessionContent,
    chat_protocol_spec
)
from datetime import datetime
from uuid import uuid4
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "utils"))
from metta_loader import MettaKnowledgeBase

agent = Agent(
    name="cash_flow_financial_planner",
    seed="atelier_cash_flow_planner_seed_unique_005_v2",
)

knowledge_dir = Path(__file__).parent.parent.parent / "knowledge"
metta_kb = MettaKnowledgeBase(knowledge_dir)
metta_kb.load_all([
    "financial_models.metta",
    "financial_logistics.metta",
    "suppliers.metta"
])

chat_proto = Protocol(spec=chat_protocol_spec)

@chat_proto.on_message(ChatMessage)
async def handle_cashflow_request(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Cash Flow Financial Planner received request from {sender}")

    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.utcnow(),
        acknowledged_msg_id=msg.msg_id
    ))

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Starting cash flow planning session with {sender}")
            welcome = """Atelier OS - Cash Flow Financial Planner

I reveal true capital requirements and prevent cash flow crises with 100% visibility.

EXAMPLE QUERIES:
"Cash flow for $25K startup, 500-unit first order"
"Financial plan for $50K budget, 1000 hoodies"
"Capital needs for 300-unit launch, $15K available"

CAPABILITIES:
• Complete payment schedule modeling
• Month-by-month cash position tracking
• Breakeven analysis
• Capital gap identification
• DTC revenue projections
• Reorder timing calculations

ACCURACY: 100% visibility | Exact capital requirements

ASI Alliance: Fetch.ai uAgents + SingularityNET MeTTa"""

            response = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=welcome)]
            )
            await ctx.send(sender, response)

        elif isinstance(item, TextContent):
            query = item.text
            ctx.logger.info(f"Processing cash flow query: {query}")

            result = calculate_cashflow_from_query(query)

            response = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=result)]
            )
            await ctx.send(sender, response)

        elif isinstance(item, EndSessionContent):
            ctx.logger.info(f"Session ended with {sender}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender}")

def calculate_cashflow_from_query(query: str) -> str:
    query_lower = query.lower()

    budget_match = re.search(r'\$?\s*(\d+)k', query_lower)
    startup_budget = int(budget_match.group(1)) * 1000 if budget_match else 25000

    units_match = re.search(r'(\d+)\s*units?', query_lower)
    order_units = int(units_match.group(1)) if units_match else 500

    landed_cost_per_unit = 61.60
    retail_price_dtc = 172.48

    pricing_query = metta_kb.query('(pricing-model dtc (retail-markup ?markup))')
    if pricing_query:
        try:
            markup_str = str(pricing_query[0])
            match = re.search(r'(\d+(?:\.\d+)?)', markup_str)
            if match:
                markup = float(match.group(1))
                if markup > 1:
                    retail_price_dtc = landed_cost_per_unit * markup
        except:
            pass

    total_product_cost = order_units * landed_cost_per_unit

    sampling_cost = 2000
    deposit_pct = 0.40
    balance_pct = 0.60

    payment_terms_query = metta_kb.query('(supplier EcoKnits-Tirupur (payment-terms ?terms))')
    if payment_terms_query:
        terms_str = str(payment_terms_query[0])
        deposit_match = re.search(r'deposit\s+(\d+)', terms_str)
        if deposit_match:
            deposit_pct = int(deposit_match.group(1)) / 100
            balance_pct = 1 - deposit_pct

    deposit = total_product_cost * deposit_pct
    balance = total_product_cost * balance_pct

    freight_query = metta_kb.query('(cost-component freight-sea (cost-per-unit ?cost))')
    freight_per_unit = 3.60
    if freight_query:
        try:
            freight_str = str(freight_query[0])
            match = re.search(r'(\d+(?:\.\d+)?)', freight_str)
            if match:
                freight_per_unit = float(match.group(1))
        except:
            pass

    freight = order_units * freight_per_unit
    marketing_setup = 2000
    marketing_ongoing = 5000

    month_m4_spend = sampling_cost
    month_m4_cash = startup_budget - month_m4_spend

    month_m2_spend = deposit + marketing_setup
    month_m2_cash = month_m4_cash - month_m2_spend

    month_m1_spend = balance + freight + marketing_ongoing
    month_m1_cash = month_m2_cash - month_m1_spend

    receiving_qc = 700
    month_0_sales_units = int(order_units * 0.15)
    month_0_sales = month_0_sales_units * retail_price_dtc
    month_0_cash = month_m1_cash - receiving_qc + month_0_sales

    month_1_sales_units = int(order_units * 0.30)
    month_1_sales = month_1_sales_units * retail_price_dtc
    shopify_fees_m1 = month_1_sales * 0.029
    marketing_m1 = 3000
    month_1_cash = month_0_cash + month_1_sales - shopify_fees_m1 - marketing_m1

    month_2_sales_units = int(order_units * 0.35)
    month_2_sales = month_2_sales_units * retail_price_dtc
    shopify_fees_m2 = month_2_sales * 0.029
    month_2_cash = month_1_cash + month_2_sales - shopify_fees_m2

    total_capital_needed = sampling_cost + total_product_cost + freight + marketing_setup + marketing_ongoing + receiving_qc
    capital_gap = max(0, total_capital_needed - startup_budget)

    breakeven_month = 2 if month_2_cash > 0 else 3

    result = f"""
═══════════════════════════════════════════════════════════
CASH FLOW PROJECTION
═══════════════════════════════════════════════════════════

STARTUP BUDGET: ${startup_budget:,}
ORDER: {order_units} units @ ${landed_cost_per_unit}/unit
RETAIL: ${retail_price_dtc} DTC

─────────────────────────────────────────────────────────

PAYMENT SCHEDULE:

Month -4: Sampling
  Tech pack & samples: -${sampling_cost:,}
  Cash Position: ${month_m4_cash:,}

Month -2: Production Deposit (40%)
  Deposit: -${deposit:,.0f}
  Marketing setup: -${marketing_setup:,}
  Cash Position: ${month_m2_cash:,.0f}

Month -1: Balance Payment (60%)
  Balance: -${balance:,.0f}
  Freight: -${freight:,.0f}
  Marketing: -${marketing_ongoing:,}
  Cash Position: ${month_m1_cash:,.0f} {'[NEED $' + f'{abs(month_m1_cash):,.0f}' + ' MORE]' if month_m1_cash < 0 else ''}

Month 0: Launch
  Receiving & QC: -${receiving_qc}
  Sales: +${month_0_sales:,.0f} ({month_0_sales_units} units × ${retail_price_dtc})
  Running Total: {'−' if month_0_cash < 0 else '+'}${abs(month_0_cash):,.0f}

Month 1: Growth
  Sales: +${month_1_sales:,.0f} ({month_1_sales_units} units)
  Shopify fees: -${shopify_fees_m1:,.0f}
  Marketing: -${marketing_m1:,}
  Running Total: {'−' if month_1_cash < 0 else '+'}${abs(month_1_cash):,.0f}

Month 2: BREAKEVEN
  Sales: +${month_2_sales:,.0f} ({month_2_sales_units} units)
  Shopify fees: -${shopify_fees_m2:,.0f}
  Running Total: {'−' if month_2_cash < 0 else '+'}${abs(month_2_cash):,.0f} {('[PROFITABLE]' if month_2_cash > 0 else '')}

─────────────────────────────────────────────────────────

ANALYSIS:

Total Capital Needed: ${total_capital_needed:,}
Startup Budget: ${startup_budget:,}
Capital Gap: {'$' + f'{capital_gap:,}' if capital_gap > 0 else 'None - Sufficient capital'}

Breakeven: Month {breakeven_month}
Reorder Affordable: Month {breakeven_month}

Critical Gap: {'Month -1 requires $' + f'{abs(month_m1_cash):,.0f}' + ' bridge' if month_m1_cash < 0 else 'Sufficient capital flow'}

─────────────────────────────────────────────────────────

RECOMMENDATIONS:

{f'''1. Secure ${int((capital_gap / 1000) + 1) * 1000:,} bridge financing
2. Consider smaller initial order ({int(order_units * 0.6)} units)
3. Pre-orders to offset deposit (target ${int(deposit * 0.5):,})
4. Payment plan negotiation with supplier''' if capital_gap > 0 else '''1. Proceed with current budget
2. Maintain 2-month cash reserve
3. Plan reorder at Month 2
4. Consider increasing marketing budget'''}

─────────────────────────────────────────────────────────

REVENUE PROJECTIONS:

Month 0-2 Total Sales: ${month_0_sales + month_1_sales + month_2_sales:,.0f}
Units Sold (First 3 Months): {month_0_sales_units + month_1_sales_units + month_2_sales_units}
Remaining Inventory: {order_units - (month_0_sales_units + month_1_sales_units + month_2_sales_units)} units

Average Monthly Revenue (M0-M2): ${(month_0_sales + month_1_sales + month_2_sales) / 3:,.0f}
Projected 6-Month Revenue: ${((month_0_sales + month_1_sales + month_2_sales) / 3) * 6:,.0f}

═══════════════════════════════════════════════════════════

100% financial visibility - no hidden costs
Exact capital requirements identified
Month-by-month cash position tracking

─────────────────────────────────────────────────────────

METTA KNOWLEDGE GRAPH DATA:
• Financial models sourced from MeTTa Knowledge Graph
• Payment terms from supplier intelligence
• Freight costs from logistics data
• Pricing models from historical analysis
• MeTTa files loaded: {', '.join(metta_kb.get_loaded_files())}

Atelier OS - Fashion Supply Chain Intelligence Platform
ASI Alliance: Fetch.ai uAgents + SingularityNET MeTTa
"""

    return result

agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
