import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools.calculator import CalculatorTool

def test_calculator_valid_expressions():
    calc = CalculatorTool()

    res1 = calc.execute({"expression": "25 * 4"})
    assert res1.status == "success"
    assert res1.data["result"] == 100.0

    res2 = calc.execute({"expression": "(10 + 5) / 3"})
    assert res2.status == "success"
    assert res2.data["result"] == 5.0

    res3 = calc.execute({"expression": "2 ** 4"})
    assert res3.status == "success"
    assert res3.data["result"] == 16.0

def test_calculator_division_by_zero():
    calc = CalculatorTool()
    res = calc.execute({"expression": "100 / 0"})
    assert res.status == "error"
    assert "Division by zero" in res.error_message

def test_calculator_rejection_of_unsafe_code():
    calc = CalculatorTool()

    # Rejects __import__
    res1 = calc.execute({"expression": "__import__('os').system('dir')"})
    assert res1.status == "error"
    assert "Unsafe AST node" in res1.error_message or "Invalid" in res1.error_message

    # Rejects function calls
    res2 = calc.execute({"expression": "eval('2+2')"})
    assert res2.status == "error"

    # Rejects string attribute access
    res3 = calc.execute({"expression": "'abc'.upper()"})
    assert res3.status == "error"
