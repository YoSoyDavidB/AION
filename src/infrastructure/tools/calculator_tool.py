"""
Calculator tool for mathematical operations.
"""

from typing import Any

from src.domain.entities.tool import BaseTool, ToolParameter
from src.shared.logging import LoggerMixin


class CalculatorTool(BaseTool, LoggerMixin):
    """
    Calculator tool for performing mathematical calculations.

    Supports basic arithmetic operations and more complex expressions.
    Uses Python's eval with restricted scope for safety.
    """

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return """Performs mathematical calculations and evaluates mathematical expressions.
Supports:
- Basic operations: +, -, *, /, **, %
- Functions: abs, round, min, max, sum
- Constants: pi, e
Examples:
- "2 + 2"
- "sqrt(16)"
- "10 ** 2"
- "abs(-5)"
Use this tool whenever you need to perform calculations or solve mathematical problems."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="expression",
                type="string",
                description="Mathematical expression to evaluate (e.g., '2+2', 'sqrt(16)', '10**2')",
                required=True,
            )
        ]

    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute mathematical calculation.

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            Result of the calculation

        Raises:
            ValueError: If expression is invalid
            Exception: If calculation fails
        """
        expression = kwargs.get("expression")

        if not expression:
            raise ValueError("Missing required parameter: expression")

        self.logger.info("calculator_tool_executing", expression=expression)

        try:
            # Safe math environment with limited functions
            import math

            safe_dict = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "sqrt": math.sqrt,
                "pow": pow,
                "pi": math.pi,
                "e": math.e,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "floor": math.floor,
                "ceil": math.ceil,
                # Prevent dangerous operations
                "__builtins__": {},
            }

            # Evaluate expression in safe environment
            result = eval(expression, safe_dict, {})

            self.logger.info(
                "calculator_tool_success", expression=expression, result=result
            )

            return result

        except SyntaxError as e:
            self.logger.error(
                "calculator_tool_syntax_error", expression=expression, error=str(e)
            )
            raise ValueError(f"Invalid mathematical expression: {str(e)}") from e

        except Exception as e:
            self.logger.error(
                "calculator_tool_error", expression=expression, error=str(e)
            )
            raise Exception(f"Calculation failed: {str(e)}") from e
