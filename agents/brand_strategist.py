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
import logging

from models.messages import BudgetValidationRequest
from utils.metta_loader import MettaKnowledgeBase
from utils.config import Config
from utils.helpers import get_current_timestamp

logger = logging.getLogger(__name__)


def create_brand_strategist_agent(metta_kb: MettaKnowledgeBase, financial_ops_address: str):
    agent = Agent(
        name="brand_strategist",
        seed=Config.AGENT_SEEDS["brand_strategist"],
        port=Config.AGENT_PORTS["brand_strategist"],
        endpoint=Config.ENDPOINTS["brand_strategist"]
    )

    chat_proto = Protocol(spec=chat_protocol_spec)

    @chat_proto.on_message(ChatMessage)
    async def handle_brand_inquiry(ctx: Context, sender: str, msg: ChatMessage):
        logger.info(f"Brand Strategist received message from {sender}")

        await ctx.send(sender, ChatAcknowledgement(
            timestamp=datetime.utcnow(),
            acknowledged_msg_id=msg.msg_id
        ))

        for item in msg.content:
            if isinstance(item, StartSessionContent):
                logger.info(f"Starting brand consultation session with {sender}")

            elif isinstance(item, TextContent):
                user_input = item.text.lower()
                logger.info(f"Processing brand inquiry: {user_input}")

                concept = extract_brand_concept(user_input)

                competitors = metta_kb.get_competitor_analysis(concept["category"])
                trends = metta_kb.get_market_trends(2025)

                strategy = generate_brand_strategy(concept, competitors, trends)

                budget_available = concept.get("budget", 15000)
                estimated_units = calculate_initial_units(budget_available, concept["category"])

                response_text = format_strategy_response(strategy, estimated_units, budget_available)

                validation_request = BudgetValidationRequest(
                    concept=concept,
                    strategy=strategy,
                    estimated_units=estimated_units,
                    requested_by=sender,
                    timestamp=get_current_timestamp()
                )

                await ctx.send(financial_ops_address, validation_request)
                logger.info(f"Sent budget validation request to financial operations")

                response = ChatMessage(
                    timestamp=datetime.utcnow(),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text=response_text)]
                )
                await ctx.send(sender, response)

            elif isinstance(item, EndSessionContent):
                logger.info(f"Ending brand consultation session with {sender}")

    @chat_proto.on_message(ChatAcknowledgement)
    async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
        logger.info(f"Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}")

    agent.include(chat_proto, publish_manifest=True)

    return agent


def extract_brand_concept(user_input: str) -> dict:
    concept = {
        "category": "activewear",
        "niche": "general",
        "values": [],
        "budget": 15000,
        "raw_input": user_input
    }

    if any(word in user_input for word in ["sustainable", "eco", "organic", "green"]):
        concept["values"].append("sustainable")

    if any(word in user_input for word in ["activewear", "athletic", "fitness", "workout"]):
        concept["category"] = "activewear"
    elif any(word in user_input for word in ["streetwear", "urban", "casual"]):
        concept["category"] = "streetwear"
    elif any(word in user_input for word in ["luxury", "premium", "high-end"]):
        concept["category"] = "luxury"

    if "cyclist" in user_input or "cycling" in user_input or "bike" in user_input:
        concept["niche"] = "urban-cyclists"
    elif "yoga" in user_input or "pilates" in user_input:
        concept["niche"] = "yoga-enthusiasts"
    elif "running" in user_input or "runner" in user_input:
        concept["niche"] = "runners"

    budget_keywords = ["$", "budget", "capital"]
    for word in user_input.split():
        if word.startswith("$"):
            try:
                amount = int(word.replace("$", "").replace(",", "").replace("k", "000"))
                concept["budget"] = amount
            except ValueError:
                pass

    return concept


def generate_brand_strategy(concept: dict, competitors: list, trends: list) -> dict:
    avg_price = sum([c["avg_price"] for c in competitors]) / len(competitors) if competitors else 85

    positioning_map = {
        "urban-cyclists": "Tech-forward sustainable commuter gear",
        "yoga-enthusiasts": "Mindful movement apparel",
        "runners": "Performance-driven running gear",
        "general": "Modern activewear essentials"
    }

    positioning = positioning_map.get(concept["niche"], "Modern activewear essentials")

    if "sustainable" in concept["values"]:
        positioning = f"Sustainable {positioning.lower()}"

    target_audience_map = {
        "urban-cyclists": "Urban professionals aged 25-40 who bike commute",
        "yoga-enthusiasts": "Wellness-focused individuals aged 22-38",
        "runners": "Active runners aged 25-45",
        "general": "Fitness enthusiasts aged 20-45"
    }

    target_audience = target_audience_map.get(concept["niche"],
                                               "Active lifestyle consumers aged 20-45")

    price_adjustment = 1.0
    if "sustainable" in concept["values"]:
        price_adjustment = 1.15

    suggested_price_min = int(avg_price * 0.90 * price_adjustment)
    suggested_price_max = int(avg_price * 1.10 * price_adjustment)

    market_opportunity = "Growing demand for sustainable activewear"
    if concept["niche"] == "urban-cyclists":
        market_opportunity = "Underserved market for stylish cycling commuter gear"

    strategy = {
        "positioning": positioning,
        "target_audience": target_audience,
        "price_range": f"{suggested_price_min}-{suggested_price_max}",
        "initial_products": determine_initial_products(concept["category"], concept["niche"]),
        "market_opportunity": market_opportunity,
        "competitive_advantage": "Sustainable materials with technical performance",
        "brand_values": concept["values"] if concept["values"] else ["quality", "performance"]
    }

    return strategy


def determine_initial_products(category: str, niche: str) -> list:
    if niche == "urban-cyclists":
        return ["Commuter Hoodie", "Technical Pants"]
    elif niche == "yoga-enthusiasts":
        return ["Flow Leggings", "Studio Tank"]
    elif niche == "runners":
        return ["Performance Tee", "Running Shorts"]
    else:
        return ["Essential Hoodie", "Training Leggings"]


def calculate_initial_units(budget: float, category: str) -> int:
    estimated_cost_per_unit_map = {
        "activewear": 65,
        "streetwear": 55,
        "luxury": 95
    }

    cost_per_unit = estimated_cost_per_unit_map.get(category, 65)

    units = int(budget / cost_per_unit)

    moq_standard = 250
    if units < moq_standard:
        units = moq_standard

    return units


def format_strategy_response(strategy: dict, units: int, budget: float) -> str:
    products = ", ".join(strategy["initial_products"])

    response = f"""Brand Strategy Analysis Complete

Positioning: {strategy['positioning']}
Target Audience: {strategy['target_audience']}
Recommended Price Range: ${strategy['price_range']}

Initial Product Line:
{products}

Market Opportunity:
{strategy['market_opportunity']}

Competitive Advantage:
{strategy['competitive_advantage']}

Production Plan:
- Estimated Units: {units}
- Available Budget: ${budget:,.0f}
- Financial validation in progress...

Our financial operations team is analyzing the viability of this strategy."""

    return response
