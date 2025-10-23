#!/usr/bin/env python3
"""
Atelier OS - Automated Agentverse Deployment Script
Deploys all 5 agents to Agentverse using the API
"""

import requests
import json
import time

# Your Agentverse API token
API_TOKEN = "eyJhbGciOiJSUzI1NiJ9.eyJleHAiOjE3NjM2NjgyNjUsImlhdCI6MTc2MTA3NjI2NSwiaXNzIjoiZmV0Y2guYWkiLCJqdGkiOiI5MTVkMGE4ZDJhYjNkZmZlNWIxZjM2ZjgiLCJzY29wZSI6ImF2Iiwic3ViIjoiMjI2ZTQ0ZjdiZWQ4M2M4ZjU5NWNhYTdkY2Y3ODFkYzZlODUxMGY1OGEyYWQ4NjJkIn0.mgVvZsoROhptiyruOagz6BHDLMiQbmvJzfztMxdmHhd6R3A9ENNusS63Yyx-E_dRuGct_p_sTAkhgmTvIXGjwQXBUW55G6x1ODKn6DhMZgJC_YmPHc0iHXxKcJfP_xNBA49f3w_0YXZNFsbh0iIXVNo5Z5V1p6FKKP_ieobHt0z5NR1E5zsvaUls-_uTGSt4bqzfz-ahnFuC3WDV5Y5Nt9BsTXpC1W02LUikHuL9yiKAp8tkQAWT_7uAQYazZirD7YbmkfsoL6hujDfK78NMoezHaDwzktGQBpnwrdWUcOguZQSrvOeRaf3v10JcV3jNryemwe33OcUlVqMZZZ_vQw"

API_BASE = "https://agentverse.ai/v1"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Agent files to deploy
AGENTS = [
    {
        "file": "agent1_agentverse.py",
        "name": "BOM & Costing Specialist",
        "description": "Calculate precise BOMs and landed costs with ±2% accuracy"
    },
    {
        "file": "agent2_moq_agentverse.py",
        "name": "MOQ Negotiation Strategist",
        "description": "Reduce minimum order quantities by 30-50% through strategic negotiation"
    },
    {
        "file": "agent3_timeline_agentverse.py",
        "name": "Production Timeline Manager",
        "description": "Map complete production schedules with 95% on-time delivery"
    },
    {
        "file": "agent4_inventory_agentverse.py",
        "name": "Inventory & Demand Forecaster",
        "description": "Optimize inventory allocation to reduce dead stock to <10%"
    },
    {
        "file": "agent5_cashflow_agentverse.py",
        "name": "Cash Flow Financial Planner",
        "description": "Model complete cash flow with 100% financial visibility"
    }
]

def read_agent_code(filename):
    """Read agent code from file"""
    with open(filename, 'r') as f:
        return f.read()

def create_agent(name, code, description):
    """Create agent via Agentverse API"""
    payload = {
        "name": name,
        "code": code,
        "description": description,
        "protocol": "chat"
    }

    response = requests.post(
        f"{API_BASE}/agents",
        headers=HEADERS,
        json=payload
    )

    return response

def deploy_all_agents():
    """Deploy all agents to Agentverse"""
    print("=" * 60)
    print("Atelier OS - Agentverse Deployment")
    print("=" * 60)
    print()

    results = []

    for i, agent_info in enumerate(AGENTS, 1):
        print(f"[{i}/5] Deploying {agent_info['name']}...")
        print(f"       Reading {agent_info['file']}...")

        try:
            # Read agent code
            code = read_agent_code(agent_info['file'])
            print(f"       Code loaded ({len(code)} bytes)")

            # Create agent
            print(f"       Sending to Agentverse...")
            response = create_agent(
                agent_info['name'],
                code,
                agent_info['description']
            )

            if response.status_code in [200, 201]:
                data = response.json()
                agent_address = data.get('address', 'N/A')
                print(f"       ✓ SUCCESS - Agent Address: {agent_address}")
                results.append({
                    "name": agent_info['name'],
                    "status": "success",
                    "address": agent_address
                })
            else:
                print(f"       ✗ FAILED - Status: {response.status_code}")
                print(f"       Error: {response.text}")
                results.append({
                    "name": agent_info['name'],
                    "status": "failed",
                    "error": response.text
                })

        except Exception as e:
            print(f"       ✗ ERROR: {str(e)}")
            results.append({
                "name": agent_info['name'],
                "status": "error",
                "error": str(e)
            })

        print()
        time.sleep(2)  # Rate limiting

    # Summary
    print("=" * 60)
    print("DEPLOYMENT SUMMARY")
    print("=" * 60)
    print()

    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] != 'success']

    print(f"Successful: {len(successful)}/5")
    print(f"Failed: {len(failed)}/5")
    print()

    if successful:
        print("DEPLOYED AGENTS:")
        for agent in successful:
            print(f"  • {agent['name']}")
            print(f"    Address: {agent['address']}")
            print()

    if failed:
        print("FAILED DEPLOYMENTS:")
        for agent in failed:
            print(f"  • {agent['name']}")
            print(f"    Error: {agent.get('error', 'Unknown')}")
            print()

    # Save results
    with open('deployment_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("Results saved to deployment_results.json")
    print()

    return results

if __name__ == "__main__":
    deploy_all_agents()
