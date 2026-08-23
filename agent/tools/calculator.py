import ast
import operator
import re
from typing import Dict, Any, Optional
from agent.tools.base import BaseTool
from agent.models import ToolResult


class SafeCalculatorVisitor(ast.NodeVisitor):
    """AST Node Visitor that safely evaluates math expressions without code execution risks."""

    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def visit_Expression(self, node: ast.Expression):
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    def visit_Num(self, node: ast.Num):  # Python < 3.8 fallback compatibility
        return node.n

    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_type = type(node.op)

        if op_type not in self.ALLOWED_OPERATORS:
            raise ValueError(f"Operator '{op_type.__name__}' is not allowed.")

        if op_type == ast.Div and right == 0:
            raise ZeroDivisionError("Division by zero is not allowed.")

        if op_type == ast.Pow and right > 100:
            raise ValueError("Exponentiation power higher than 100 is prohibited for safety.")

        return self.ALLOWED_OPERATORS[op_type](left, right)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        operand = self.visit(node.operand)
        op_type = type(node.op)

        if op_type not in self.ALLOWED_OPERATORS:
            raise ValueError(f"Unary operator '{op_type.__name__}' is not allowed.")

        return self.ALLOWED_OPERATORS[op_type](operand)

    def generic_visit(self, node):
        raise ValueError(f"Unsafe AST node type '{type(node).__name__}' rejected.")

class CalculatorTool(BaseTool):
    """Safe mathematical expression calculator using AST evaluation."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Evaluates mathematical expressions safely (addition, subtraction, multiplication, division, powers)."

    @property
    def permissions(self) -> Dict[str, bool]:
        return {
            "read_documents": False,
            "internet_access": False,
            "calculation": True,
            "database_access": False
        }

    def execute(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        expression = input_data.get("expression") or input_data.get("query", "")
        if not expression:
            return ToolResult(tool_name=self.name, status="error", error_message="Expression parameter is required.")

        clean_expr = str(expression).strip().replace("=", "").replace("%", " / 100 ")
        clean_expr = re.sub(r'^(?:calculate|compute|what is|find|evaluate)\s*', '', clean_expr, flags=re.IGNORECASE).strip()


        try:
            try:
                parsed_ast = ast.parse(clean_expr, mode='eval')
            except SyntaxError:
                # If natural language text surrounds expression (e.g. "What is 15 * 6?"), extract math substring
                math_match = re.search(r'\(?\s*\d+(?:\s*[\+\-\*\/\^%]+\s*\d+)+\s*\)?', clean_expr)
                if math_match:
                    clean_expr = math_match.group(0).strip()
                    parsed_ast = ast.parse(clean_expr, mode='eval')
                else:
                    raise

            visitor = SafeCalculatorVisitor()
            result = visitor.visit(parsed_ast)

            return ToolResult(
                tool_name=self.name,
                status="success",
                data={
                    "expression": clean_expr,
                    "result": float(result) if isinstance(result, (int, float)) else str(result)
                }
            )

        except ZeroDivisionError as e:
            return ToolResult(tool_name=self.name, status="error", error_message=str(e))
        except (SyntaxError, ValueError, TypeError) as e:
            return ToolResult(tool_name=self.name, status="error", error_message=f"Invalid mathematical expression: {str(e)}")
        except Exception as e:
            return ToolResult(tool_name=self.name, status="error", error_message=f"Calculation error: {str(e)}")
