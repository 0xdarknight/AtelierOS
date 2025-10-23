from uagents import Agent, Context
import logging
import asyncio
from typing import Dict, List

from models.messages import (
    SupplierProposalMessage,
    SampleTrackingUpdate,
    QualityIssueAlert,
    ProductionCompleteMessage,
    ReorderRequest,
    ApprovalMessage
)
from utils.metta_loader import MettaKnowledgeBase
from utils.config import Config
from utils.helpers import generate_sample_id, get_current_timestamp

logger = logging.getLogger(__name__)


def create_production_coordinator_agent(metta_kb: MettaKnowledgeBase,
                                          logistics_fulfillment_address: str,
                                          financial_ops_address: str):
    agent = Agent(
        name="production_coordinator",
        seed=Config.AGENT_SEEDS["production_coordinator"],
        port=Config.AGENT_PORTS["production_coordinator"],
        endpoint=Config.ENDPOINTS["production_coordinator"]
    )

    production_state = {}

    @agent.on_message(SupplierProposalMessage)
    async def initiate_production(ctx: Context, sender: str, msg: SupplierProposalMessage):
        logger.info("Production Coordinator: Received supplier proposal")

        sample_id = generate_sample_id(
            msg.designs[0]["name"],
            get_current_timestamp()
        )

        production_state[sample_id] = {
            "designs": msg.designs,
            "supplier": msg.supplier,
            "tech_packs": msg.tech_packs,
            "status": "sample_ordered",
            "units": msg.moq,
            "current_stage": "sample-production"
        }

        tracking = SampleTrackingUpdate(
            sample_id=sample_id,
            product_name=msg.designs[0]["name"],
            status="sample_ordered",
            location=f"{msg.supplier['name']}, {msg.supplier['location']}",
            issues=[],
            next_milestone="sample_production_complete",
            estimated_completion=f"{Config.SAMPLE_PRODUCTION_DAYS} days",
            timestamp=get_current_timestamp()
        )

        logger.info(f"Sample order placed: {sample_id}")
        logger.info(f"Supplier: {msg.supplier['name']}, MOQ: {msg.moq} units")

        await simulate_production_workflow(
            ctx, sample_id, production_state, msg,
            logistics_fulfillment_address, financial_ops_address, metta_kb
        )

    @agent.on_message(ReorderRequest)
    async def handle_reorder(ctx: Context, sender: str, msg: ReorderRequest):
        logger.info(f"Production Coordinator: Received reorder request for {msg.sku}")

        sample_id = generate_sample_id(msg.product_name, get_current_timestamp())

        production_state[sample_id] = {
            "sku": msg.sku,
            "product_name": msg.product_name,
            "status": "reorder_production",
            "units": msg.quantity,
            "urgency": msg.urgency,
            "current_stage": "bulk-production"
        }

        logger.info(f"Reorder initiated: {msg.quantity} units of {msg.sku}")
        logger.info(f"Urgency level: {msg.urgency}, Expected stockout: {msg.estimated_stockout_date}")

        lead_time = Config.BULK_PRODUCTION_DAYS
        if msg.urgency == "high":
            lead_time = int(lead_time * 0.75)
            logger.info(f"Expedited production: {lead_time} days")

        await asyncio.sleep(0.5)

        completion_message = ProductionCompleteMessage(
            product_id=msg.sku,
            product_name=msg.product_name,
            units=msg.quantity,
            location="Vietnam",
            ready_to_ship=True,
            quality_report={
                "inspection_date": get_current_timestamp(),
                "defect_rate": 0.8,
                "passed": True
            },
            timestamp=get_current_timestamp()
        )

        await ctx.send(logistics_fulfillment_address, completion_message)
        logger.info(f"Reorder complete: {msg.quantity} units ready to ship")

    @agent.on_message(ApprovalMessage)
    async def handle_approval(ctx: Context, sender: str, msg: ApprovalMessage):
        logger.info(f"Production Coordinator: Received approval - {msg.request_type}")
        logger.info(f"Approved: {msg.approved}, Reasoning: {msg.reasoning}")

    return agent


async def simulate_production_workflow(ctx: Context, sample_id: str,
                                        production_state: Dict, proposal: SupplierProposalMessage,
                                        logistics_address: str, financial_address: str,
                                        metta_kb: MettaKnowledgeBase):

    await asyncio.sleep(0.2)

    logger.info(f"{sample_id}: Sample production in progress...")

    await asyncio.sleep(0.2)

    logger.info(f"{sample_id}: Sample received, initiating quality check")
    production_state[sample_id]["status"] = "quality_check"

    quality_issues = detect_quality_issues(proposal.designs[0])

    if quality_issues:
        logger.warning(f"{sample_id}: Quality issues detected: {', '.join(quality_issues)}")

        issue = quality_issues[0]
        issue_details = analyze_quality_issue(issue, metta_kb)

        alert = QualityIssueAlert(
            sample_id=sample_id,
            issue_type=issue,
            severity=issue_details["severity"],
            fix_cost=issue_details["fix_cost"],
            delay_days=issue_details["delay_days"],
            requires_approval=issue_details["requires_approval"],
            description=issue_details["description"],
            timestamp=get_current_timestamp()
        )

        await ctx.send(financial_address, alert)
        logger.info(f"{sample_id}: Quality issue alert sent to financial operations")

        await asyncio.sleep(0.2)

        logger.info(f"{sample_id}: Issue resolved, revised sample approved")
        production_state[sample_id]["status"] = "sample_approved"
    else:
        logger.info(f"{sample_id}: Sample approved - all quality checks passed")
        production_state[sample_id]["status"] = "sample_approved"

    await asyncio.sleep(0.2)

    logger.info(f"{sample_id}: Bulk production initiated - {proposal.moq} units")
    production_state[sample_id]["status"] = "bulk_production"
    production_state[sample_id]["current_stage"] = "bulk-production"

    checkpoints = ["week1-inspection", "week2-inspection", "week3-inspection", "final-qc"]
    progress_pct = [25, 50, 75, 100]

    for checkpoint, pct in zip(checkpoints, progress_pct):
        await asyncio.sleep(0.15)

        checkpoint_result = perform_checkpoint_inspection(checkpoint)

        logger.info(f"{sample_id}: {checkpoint} - {pct}% complete, Status: {checkpoint_result['status']}")

        if not checkpoint_result["passed"]:
            logger.warning(f"{sample_id}: {checkpoint} failed - corrective action initiated")

    await asyncio.sleep(0.2)

    logger.info(f"{sample_id}: Production complete - {proposal.moq} units ready")
    production_state[sample_id]["status"] = "production_complete"

    quality_report = {
        "inspection_date": get_current_timestamp(),
        "total_units": proposal.moq,
        "defect_rate": 1.2,
        "passed_qc": int(proposal.moq * 0.988),
        "failed_qc": int(proposal.moq * 0.012),
        "overall_status": "passed"
    }

    completion_message = ProductionCompleteMessage(
        product_id=proposal.designs[0]["id"],
        product_name=proposal.designs[0]["name"],
        units=proposal.moq,
        location=f"{proposal.supplier['location']}",
        ready_to_ship=True,
        quality_report=quality_report,
        timestamp=get_current_timestamp()
    )

    await ctx.send(logistics_address, completion_message)
    logger.info(f"{sample_id}: Notified logistics - shipment ready")


def detect_quality_issues(design: Dict) -> List[str]:
    import random
    random.seed(hash(design["name"]))

    possible_issues = [
        "sizing_incorrect",
        "color_mismatch",
        "loose_stitching",
        "fabric_defect"
    ]

    if random.random() < 0.3:
        num_issues = random.randint(1, 2)
        return random.sample(possible_issues, num_issues)

    return []


def analyze_quality_issue(issue: str, metta_kb: MettaKnowledgeBase) -> Dict:
    issue_map = {
        "sizing_incorrect": {
            "severity": "high",
            "fix_cost": 200.0,
            "delay_days": 5,
            "requires_approval": True,
            "description": "Garment measurements off by more than 0.5 inches"
        },
        "color_mismatch": {
            "severity": "medium",
            "fix_cost": 150.0,
            "delay_days": 4,
            "requires_approval": True,
            "description": "Color not matching approved PMS standard"
        },
        "loose_stitching": {
            "severity": "low",
            "fix_cost": 50.0,
            "delay_days": 1,
            "requires_approval": False,
            "description": "Inconsistent stitch tension in seams"
        },
        "fabric_defect": {
            "severity": "medium",
            "fix_cost": 300.0,
            "delay_days": 3,
            "requires_approval": True,
            "description": "Fabric pilling or irregularities detected"
        }
    }

    return issue_map.get(issue, {
        "severity": "low",
        "fix_cost": 100.0,
        "delay_days": 2,
        "requires_approval": False,
        "description": "General quality concern"
    })


def perform_checkpoint_inspection(checkpoint: str) -> Dict:
    import random

    inspection_criteria = {
        "week1-inspection": ["fabric_quality", "cutting_accuracy"],
        "week2-inspection": ["assembly_quality", "stitching_consistency"],
        "week3-inspection": ["sizing_accuracy", "finishing_quality"],
        "final-qc": ["complete_inspection", "defect_count", "packaging"]
    }

    criteria = inspection_criteria.get(checkpoint, ["general_inspection"])

    passed = random.random() > 0.1

    return {
        "checkpoint": checkpoint,
        "criteria": criteria,
        "passed": passed,
        "status": "passed" if passed else "corrective_action_needed",
        "timestamp": get_current_timestamp()
    }
