#!/usr/bin/env python3
"""
Atelier OS - Frontend-to-Agent Bridge
This local agent receives HTTP requests from the frontend and communicates with deployed Agentverse agents
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from uagents import Agent, Context
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
import asyncio

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Create a local bridge agent
bridge = Agent(
    name="atelier_frontend_bridge",
    seed="atelier_frontend_bridge_unique_seed_001",
    port=8765,
    endpoint=["http://localhost:8765/submit"]
)

# Agent addresses on Agentverse
AGENT_ADDRESSES = {
    "1": "agent1qtkc97vr85qv7quhn0z6g7sa4muyckmchkf504r6wv6mdpqre8g3gjmykj3",  # BOM Costing
    "2": "agent1qgpzkhllh269rlnk0eeall8vm7eljd790pfcytyjezrfgkz6p89f2wv385w",  # MOQ Negotiation
    "3": "agent1q25ha9svq0telj3umkn5hpfjxwsvd2wqa9zj4ac2m8g6mfle33a750c04pa",  # Production Timeline
    "4": "agent1q0ytwhm43g25cny75kd0vx774z2ytswu2rs6ru6vddthg9gh2f2fkm3yu5w",  # Inventory Forecasting
    "5": "agent1qffu0yhwwvzhsdhlsvm5zg9jzfpzjxt834gk80r79hv8wzfun0djqgakvyj"   # Cash Flow Planning
}

# Store pending responses
pending_responses = {}

@bridge.on_message(ChatMessage)
async def handle_agent_response(ctx: Context, sender: str, msg: ChatMessage):
    """Handle responses from Agentverse agents"""
    ctx.logger.info(f"Received response from {sender}")

    # Send acknowledgement
    await ctx.send(sender, ChatAcknowledgement(
        timestamp=datetime.utcnow(),
        acknowledged_msg_id=msg.msg_id
    ))

    # Extract text content
    response_text = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            response_text += item.text + "\n"

    # Store the response
    pending_responses[sender] = response_text.strip()
    ctx.logger.info(f"Stored response from {sender}: {len(response_text)} characters")

@bridge.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender}")

# Flask endpoints
@app.route('/api/message', methods=['POST'])
async def send_message_to_agent():
    """Endpoint for frontend to send messages to agents"""
    data = request.json
    agent_id = data.get('agent_id')
    message_text = data.get('message')
    session_action = data.get('session_action', 'text')  # 'start', 'text', or 'end'

    if not agent_id or agent_id not in AGENT_ADDRESSES:
        return jsonify({'error': 'Invalid agent ID'}), 400

    if not message_text and session_action == 'text':
        return jsonify({'error': 'Message is required'}), 400

    agent_address = AGENT_ADDRESSES[agent_id]

    try:
        # Create appropriate content based on session action
        if session_action == 'start':
            content = [StartSessionContent(type="start_session")]
        elif session_action == 'end':
            content = [EndSessionContent(type="end_session")]
        else:
            content = [TextContent(type="text", text=message_text)]

        # Create and send ChatMessage
        chat_msg = ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=content
        )

        # Clear any previous response from this agent
        if agent_address in pending_responses:
            del pending_responses[agent_address]

        # Get bridge context and send message
        ctx = bridge._ctx
        await ctx.send(agent_address, chat_msg)

        # Wait for response (with timeout)
        max_wait = 10  # 10 seconds timeout
        waited = 0
        while agent_address not in pending_responses and waited < max_wait:
            await asyncio.sleep(0.1)
            waited += 0.1

        if agent_address in pending_responses:
            response = pending_responses[agent_address]
            del pending_responses[agent_address]
            return jsonify({'success': True, 'response': response})
        else:
            return jsonify({'error': 'Agent response timeout'}), 504

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'bridge_address': str(bridge.address),
        'agents_configured': len(AGENT_ADDRESSES)
    })

if __name__ == '__main__':
    # Run Flask in a separate thread
    from threading import Thread

    def run_flask():
        app.run(host='0.0.0.0', port=5001, debug=False)

    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print("=" * 60)
    print("Atelier OS - Frontend-to-Agent Bridge")
    print("=" * 60)
    print(f"Bridge Agent Address: {bridge.address}")
    print(f"HTTP API: http://localhost:5001")
    print(f"Connected to {len(AGENT_ADDRESSES)} Agentverse agents")
    print("=" * 60)

    # Run the bridge agent
    bridge.run()
