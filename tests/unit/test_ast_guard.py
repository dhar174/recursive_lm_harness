"""
Unit tests for ASTSafetyGuard static analysis.
"""

from recursive_lm.core.ast_guard import ASTSafetyGuard


def test_valid_code_passes():
    guard = ASTSafetyGuard()
    code = """
import json
import math

records = [json.loads('{"id": 1}'), json.loads('{"id": 2}')]
sum_val = math.sqrt(16)
answers['node_1'] = sum_val
"""
    result = guard.validate_code(code)
    assert result.is_safe is True
    assert result.syntax_valid is True
    assert result.status == "PASS"
    assert len(result.errors) == 0


def test_syntax_error_detection():
    guard = ASTSafetyGuard()
    invalid_code = "def malformed_function(\n    pass"
    result = guard.validate_code(invalid_code)

    assert result.is_safe is False
    assert result.syntax_valid is False
    assert result.status == "BLOCK"
    assert any("SyntaxError" in err for err in result.errors)


def test_prohibited_module_import():
    guard = ASTSafetyGuard()
    code_os = "import os\nos.system('dir')"
    result = guard.validate_code(code_os)

    assert result.is_safe is False
    assert any("Prohibited import: 'os'" in node for node in result.prohibited_nodes)

    code_sub = "from subprocess import Popen"
    result_sub = guard.validate_code(code_sub)
    assert result_sub.is_safe is False
    assert any("Prohibited from-import: 'subprocess'" in node for node in result_sub.prohibited_nodes)


def test_prohibited_calls():
    guard = ASTSafetyGuard()
    code_eval = "x = eval('2 + 2')"
    result = guard.validate_code(code_eval)

    assert result.is_safe is False
    assert any("Prohibited call: 'eval()'" in node for node in result.prohibited_nodes)


def test_prohibited_dunder_attributes():
    guard = ASTSafetyGuard()
    code_dunder = "subclasses = ().__class__.__bases__[0].__subclasses__()"
    result = guard.validate_code(code_dunder)

    assert result.is_safe is False
    assert any("Prohibited attribute access: '__subclasses__'" in node for node in result.prohibited_nodes)


def test_unbounded_while_true_detection():
    guard = ASTSafetyGuard()
    unbounded_code = """
while True:
    print('running forever')
"""
    result = guard.validate_code(unbounded_code)
    assert result.is_safe is False
    assert result.unbounded_loops is True
    assert any("Unbounded loop detected" in err for err in result.errors)


def test_bounded_while_true_with_break():
    guard = ASTSafetyGuard()
    bounded_code = """
count = 0
while True:
    count += 1
    if count > 10:
        break
"""
    result = guard.validate_code(bounded_code)
    assert result.is_safe is True
    assert result.unbounded_loops is False
