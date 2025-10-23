import os
from pathlib import Path


class Config:
    PROJECT_ROOT = Path(__file__).parent.parent
    KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"

    AGENT_PORTS = {
        "bom_costing": 8000,
        "moq_negotiation": 8001,
        "production_timeline": 8002,
        "inventory_forecasting": 8003,
        "cash_flow": 8004
    }

    AGENT_SEEDS = {
        "bom_costing": os.getenv("BOM_COSTING_SEED", "atelier_bom_costing_seed_unique_001"),
        "moq_negotiation": os.getenv("MOQ_NEGOTIATION_SEED", "atelier_moq_negotiation_seed_unique_002"),
        "production_timeline": os.getenv("PRODUCTION_TIMELINE_SEED", "atelier_production_timeline_seed_unique_003"),
        "inventory_forecasting": os.getenv("INVENTORY_FORECASTING_SEED", "atelier_inventory_forecasting_seed_unique_004"),
        "cash_flow": os.getenv("CASH_FLOW_SEED", "atelier_cash_flow_seed_unique_005")
    }

    ENDPOINTS = {
        "bom_costing": ["http://localhost:8000/submit"],
        "moq_negotiation": ["http://localhost:8001/submit"],
        "production_timeline": ["http://localhost:8002/submit"],
        "inventory_forecasting": ["http://localhost:8003/submit"],
        "cash_flow": ["http://localhost:8004/submit"]
    }

    METTA_FILES = [
        "materials_database.metta",
        "supplier_intelligence.metta",
        "garment_specs.metta",
        "financial_logistics.metta"
    ]

    @classmethod
    def get_knowledge_dir(cls) -> Path:
        return cls.KNOWLEDGE_DIR

    @classmethod
    def validate_config(cls):
        if not cls.KNOWLEDGE_DIR.exists():
            raise FileNotFoundError(f"Knowledge directory not found: {cls.KNOWLEDGE_DIR}")

        for filename in cls.METTA_FILES:
            filepath = cls.KNOWLEDGE_DIR / filename
            if not filepath.exists():
                raise FileNotFoundError(f"MeTTa file not found: {filepath}")

        return True
