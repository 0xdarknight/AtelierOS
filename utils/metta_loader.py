from hyperon import MeTTa
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MettaKnowledgeBase:
    def __init__(self, knowledge_dir: Path):
        self.knowledge_dir = knowledge_dir
        self.metta = MeTTa()
        self.loaded_files = []

    def load_file(self, filepath: Path) -> bool:
        try:
            if not filepath.exists():
                logger.error(f"MeTTa file not found: {filepath}")
                return False

            self.metta.load(str(filepath))
            self.loaded_files.append(filepath.name)
            logger.info(f"Loaded MeTTa file: {filepath.name}")
            return True
        except Exception as e:
            logger.error(f"Error loading MeTTa file {filepath}: {e}")
            return False

    def load_all(self, filenames: List[str]) -> bool:
        success = True
        for filename in filenames:
            filepath = self.knowledge_dir / filename
            if not self.load_file(filepath):
                success = False
        return success

    def query(self, query_string: str) -> List[Any]:
        try:
            result = self.metta.query(query_string)
            return result if result else []
        except Exception as e:
            logger.error(f"MeTTa query error: {e}")
            return []

    def query_suppliers(self, category: str, max_moq: int) -> List[Dict]:
        query = f"(find-low-moq-suppliers {category} {max_moq})"
        results = self.query(query)
        return self._parse_supplier_results(results)

    def query_materials(self, style: str, budget: float, min_sustainability: int) -> List[Dict]:
        query = f"(best-material {style} {budget} {min_sustainability})"
        results = self.query(query)
        return self._parse_material_results(results)

    def calculate_total_cost(self, supplier_name: str, units: int) -> float:
        query = f"(calculate-total-supplier-cost {supplier_name} {units})"
        results = self.query(query)
        if results and len(results) > 0:
            return float(results[0])
        return 0.0

    def calculate_shipping_cost(self, supplier_name: str, units: int) -> float:
        query = f"(calculate-shipping-cost {supplier_name} {units})"
        results = self.query(query)
        if results and len(results) > 0:
            return float(results[0])
        return 0.0

    def predict_production_delay(self, stage: str, issues: List[str]) -> int:
        if not issues:
            return 0

        total_delay = 0
        for issue in issues:
            query = f"(predict-delay {stage} {issue})"
            results = self.query(query)
            if results and len(results) > 0:
                total_delay += int(results[0])

        return total_delay

    def calculate_break_even(self, fixed_costs: float, retail_price: float, variable_cost: float) -> int:
        query = f"(break-even-units {fixed_costs} {retail_price} {variable_cost})"
        results = self.query(query)
        if results and len(results) > 0:
            return int(results[0])
        return 0

    def calculate_profit(self, retail_price: float, cogs: float, shipping: float,
                        warehouse: float, packaging: float, marketing: float) -> float:
        query = f"(calculate-profit {retail_price} {cogs} {shipping} {warehouse} {packaging} {marketing})"
        results = self.query(query)
        if results and len(results) > 0:
            return float(results[0])
        return 0.0

    def get_competitor_analysis(self, category: str) -> List[Dict]:
        query = f"(competitor-analysis {category} ?brand ?price ?saturation)"
        results = self.query(query)
        return self._parse_competitor_results(results)

    def get_market_trends(self, year: int = 2025) -> List[Dict]:
        query = f"(market-trend {year} ?trend ?rate ?size)"
        results = self.query(query)
        return self._parse_trend_results(results)

    def _parse_supplier_results(self, results: List) -> List[Dict]:
        suppliers = []
        for result in results:
            if isinstance(result, (list, tuple)) and len(result) >= 3:
                suppliers.append({
                    "name": str(result[0]),
                    "moq": int(result[1]),
                    "cost_per_unit": float(result[2])
                })
        return suppliers

    def _parse_material_results(self, results: List) -> List[Dict]:
        materials = []
        for result in results:
            if isinstance(result, (list, tuple)) and len(result) >= 3:
                materials.append({
                    "name": str(result[0]),
                    "cost_per_meter": float(result[1]),
                    "sustainability_score": int(result[2])
                })
        return materials

    def _parse_competitor_results(self, results: List) -> List[Dict]:
        competitors = []
        for result in results:
            if isinstance(result, (list, tuple)) and len(result) >= 3:
                competitors.append({
                    "brand": str(result[0]),
                    "avg_price": float(result[1]),
                    "saturation": str(result[2])
                })
        return competitors

    def _parse_trend_results(self, results: List) -> List[Dict]:
        trends = []
        for result in results:
            if isinstance(result, (list, tuple)) and len(result) >= 2:
                trends.append({
                    "trend": str(result[0]),
                    "growth_rate": float(result[1])
                })
        return trends

    def get_loaded_files(self) -> List[str]:
        return self.loaded_files.copy()
