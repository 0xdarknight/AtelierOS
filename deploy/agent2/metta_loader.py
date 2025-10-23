"""
Lightweight MeTTa S-expression parser and query engine
Works without hyperon library - pure Python implementation
"""
from typing import List, Dict, Any, Union
import re
import logging

logger = logging.getLogger(__name__)

# Embedded MeTTa knowledge - suppliers.metta
SUPPLIERS_METTA = """
(supplier EcoKnits-Tirupur
  (location India-Tirupur)
  (moq-standard 300-500)
  (moq-negotiable 200-300)
  (lead-time 35-days)
  (payment-terms (deposit 40) (balance 60))
  (labor-cost-per-minute 0.08 usd)
  (logistics (sea-freight 18-days) (air-freight 5-days))
  (moq-negotiation-success-rate 75-percent)
  (negotiation-strategies
    (multi-style-commitment (reduces-moq-by 40))
    (off-peak-timing (reduces-moq-by 25))
    (payment-terms (reduces-moq-by 20))))

(supplier VietnamTex-HoChiMinh
  (location Vietnam-HoChiMinh)
  (moq-standard 500-800)
  (moq-negotiable 300-500)
  (lead-time 28-days)
  (payment-terms (deposit 30) (balance 70))
  (labor-cost-per-minute 0.06 usd)
  (logistics (sea-freight 15-days) (air-freight 4-days)))

(supplier PortugalPremium-Porto
  (location Portugal-Porto)
  (moq-standard 200-300)
  (moq-negotiable 100-200)
  (lead-time 42-days)
  (payment-terms (deposit 50) (balance 50))
  (labor-cost-per-minute 0.25 usd)
  (logistics (sea-freight 12-days) (air-freight 3-days)))

(supplier ChinaScale-Guangzhou
  (location China-Guangzhou)
  (moq-standard 800-1000)
  (moq-negotiable 600-800)
  (lead-time 25-days)
  (payment-terms (deposit 50) (balance 50))
  (labor-cost-per-minute 0.05 usd)
  (logistics (sea-freight 20-days) (air-freight 6-days)))
"""

SUPPLIER_INTELLIGENCE_METTA = """
(supplier-intelligence EcoKnits-Tirupur
  (relationship-strength high)
  (communication-quality excellent)
  (flexibility-score 8.5)
  (innovation-capability high)
  (sustainability-commitment certified))

(negotiation-window off-peak
  (months (November December January February))
  (moq-flexibility 25-percent)
  (pricing-flexibility 10-percent))

(negotiation-window peak
  (months (August September October))
  (moq-flexibility 5-percent)
  (pricing-flexibility 2-percent))
"""


class MettaKnowledgeBase:
    """Pure Python MeTTa knowledge base - no external dependencies"""

    def __init__(self, knowledge_dir=None):
        """Initialize with embedded MeTTa knowledge"""
        self.knowledge = []
        self.loaded_files = []

    def load_all(self, filenames: List[str]) -> bool:
        """Load MeTTa knowledge from embedded strings"""
        try:
            knowledge_map = {
                "suppliers.metta": SUPPLIERS_METTA,
                "supplier_intelligence.metta": SUPPLIER_INTELLIGENCE_METTA,
            }

            for filename in filenames:
                if filename in knowledge_map:
                    content = knowledge_map[filename]
                    parsed = self._parse_metta(content)
                    self.knowledge.extend(parsed)
                    self.loaded_files.append(filename)
                    logger.info(f"Loaded embedded MeTTa: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error loading MeTTa knowledge: {e}")
            return False

    def _parse_metta(self, content: str) -> List:
        """Parse MeTTa S-expressions into Python structures"""
        expressions = []
        # Remove comments and split by top-level expressions
        lines = [l.strip() for l in content.split('\n') if l.strip() and not l.strip().startswith(';')]
        content_clean = ' '.join(lines)

        # Simple S-expression parser
        stack = []
        current = []
        token = ""

        for char in content_clean:
            if char == '(':
                if token:
                    current.append(token)
                    token = ""
                new_expr = []
                if stack:
                    current.append(new_expr)
                stack.append(current)
                current = new_expr
            elif char == ')':
                if token:
                    current.append(token)
                    token = ""
                if len(stack) > 1:
                    current = stack.pop()
                else:
                    expressions.append(current)
                    stack = []
                    current = []
            elif char in ' \n\t':
                if token:
                    current.append(token)
                    token = ""
            else:
                token += char

        return expressions

    def query(self, query_string: str) -> List[Any]:
        """Execute MeTTa-style query"""
        try:
            # Parse query
            query_parts = query_string.strip().replace('(', '').replace(')', '').split()

            if not query_parts:
                return []

            # Match pattern against knowledge base
            results = []
            for expr in self.knowledge:
                match = self._match_pattern(query_parts, expr)
                if match:
                    results.append(match)

            return results
        except Exception as e:
            logger.error(f"MeTTa query error: {e}")
            return []

    def _match_pattern(self, pattern: List[str], expr: Union[List, str], bindings=None) -> Any:
        """Match query pattern against expression"""
        if bindings is None:
            bindings = {}

        # Convert expr to flat searchable format
        expr_str = self._flatten_expr(expr)

        # Simple pattern matching
        if len(pattern) >= 2:
            pred = pattern[0]
            entity = pattern[1] if len(pattern) > 1 else None

            # Check if this expression matches
            if isinstance(expr, list) and len(expr) > 0:
                if expr[0] == pred:
                    if entity and len(expr) > 1:
                        if expr[1] == entity or entity.startswith('?'):
                            # Found a match - extract requested field
                            if len(pattern) > 2:
                                field = pattern[2].strip('()')
                                return self._extract_field(expr, field)
                            return expr

        return None

    def _flatten_expr(self, expr: Union[List, str]) -> str:
        """Flatten S-expression to string for searching"""
        if isinstance(expr, str):
            return expr
        elif isinstance(expr, list):
            return ' '.join(self._flatten_expr(e) for e in expr)
        return str(expr)

    def _extract_field(self, expr: List, field: str) -> Any:
        """Extract specific field from expression"""
        # Search through expression for field
        for item in expr:
            if isinstance(item, list) and len(item) > 0:
                if item[0] == field:
                    # Return the value(s)
                    if len(item) == 2:
                        return item[1]
                    return item[1:]
        return None

    def get_loaded_files(self) -> List[str]:
        """Return list of loaded knowledge files"""
        return self.loaded_files.copy()
