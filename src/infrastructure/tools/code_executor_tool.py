"""
Code Executor tool for running Python code in a sandboxed environment.
"""

import asyncio
import sys
from io import StringIO
from typing import Any

from src.domain.entities.tool import BaseTool, ToolParameter
from src.shared.logging import LoggerMixin


class CodeExecutorTool(BaseTool, LoggerMixin):
    """
    Code Executor tool for running Python code safely.

    Executes Python code in a restricted environment with:
    - Timeout limits
    - No file system access
    - Limited imports
    - Captured stdout/stderr
    """

    @property
    def name(self) -> str:
        return "code_executor"

    @property
    def description(self) -> str:
        return """Execute Python code in a safe sandboxed environment.
Use this tool to:
- Perform complex calculations or data transformations
- Generate sequences, lists, or data structures
- Run algorithms or simulations
- Process or analyze data programmatically

The code runs with limited permissions:
- No file system access
- No network access
- 10 second timeout
- Limited imports (math, datetime, json, re, collections, itertools)

Returns the output (stdout) and any errors."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="code",
                type="string",
                description="Python code to execute (can use print() for output)",
                required=True,
            ),
        ]

    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute Python code in sandbox.

        Args:
            code: Python code to execute

        Returns:
            Dictionary with output, error, and execution status

        Raises:
            ValueError: If code is missing
        """
        code = kwargs.get("code")

        if not code:
            raise ValueError("Missing required parameter: code")

        self.logger.info(
            "code_executor_tool_executing",
            code_length=len(code),
        )

        try:
            # Run code with timeout
            result = await asyncio.wait_for(
                self._execute_code(code), timeout=10.0
            )

            self.logger.info(
                "code_executor_tool_success",
                output_length=len(result.get("output", "")),
                has_error=bool(result.get("error")),
            )

            return result

        except asyncio.TimeoutError:
            self.logger.error("code_executor_tool_timeout", code_length=len(code))
            return {
                "success": False,
                "output": "",
                "error": "Code execution timed out (10 second limit)",
            }

        except Exception as e:
            self.logger.error(
                "code_executor_tool_error", error=str(e)
            )
            return {
                "success": False,
                "output": "",
                "error": f"Execution failed: {str(e)}",
            }

    async def _execute_code(self, code: str) -> dict[str, Any]:
        """
        Execute code in restricted environment.

        Args:
            code: Python code to execute

        Returns:
            Dictionary with output and error
        """
        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        stdout_capture = StringIO()
        stderr_capture = StringIO()

        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            # Create restricted globals
            import collections
            import datetime
            import itertools
            import json
            import math
            import re

            safe_globals = {
                # Safe built-ins
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "len": len,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "sorted": sorted,
                "reversed": reversed,
                "map": map,
                "filter": filter,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "print": print,
                # Safe modules
                "math": math,
                "datetime": datetime,
                "json": json,
                "re": re,
                "collections": collections,
                "itertools": itertools,
                # Prevent dangerous operations
                "__builtins__": {},
            }

            # Execute code
            exec(code, safe_globals, {})

            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()

            return {
                "success": not bool(error),
                "output": output,
                "error": error if error else None,
            }

        except Exception as e:
            return {
                "success": False,
                "output": stdout_capture.getvalue(),
                "error": str(e),
            }

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
