"""
Pre-execution Python AST static analyzer and safety gatekeeper.
"""

import ast
from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class ASTGuardResult:
    """Represents the static verification status of candidate Python code."""
    is_safe: bool
    syntax_valid: bool
    errors: List[str] = field(default_factory=list)
    prohibited_nodes: List[str] = field(default_factory=list)
    unbounded_loops: bool = False

    @property
    def status(self) -> str:
        return "PASS" if self.is_safe else "BLOCK"


class ASTSafetyGuard:
    """
    Validates Python code before execution in the persistent REPL sandbox.
    Prevents syntax crashes, unauthorized modules, and unbounded loops.
    """

    PROHIBITED_CALLS: Set[str] = {"eval", "exec", "compile", "__import__"}
    PROHIBITED_MODULES: Set[str] = {"os", "subprocess", "shutil", "socket", "ctypes", "pty"}
    PROHIBITED_ATTRIBUTES: Set[str] = {"__subclasses__", "__globals__", "__builtins__"}
    MAX_LOOP_ITERATIONS: int = 1000

    def __init__(
        self,
        allowed_modules: Optional[Set[str]] = None,
        disallow_loops_without_break: bool = True,
    ):
        self.allowed_modules = allowed_modules or {"json", "re", "math", "collections", "itertools", "typing", "dataclasses", "datetime"}
        self.disallow_loops_without_break = disallow_loops_without_break

    def validate_code(self, code_str: str) -> ASTGuardResult:
        """
        Statically parses and validates Python source code.
        """
        # 1. Parse AST
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            return ASTGuardResult(
                is_safe=False,
                syntax_valid=False,
                errors=[f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}"],
            )
        except Exception as e:
            return ASTGuardResult(
                is_safe=False,
                syntax_valid=False,
                errors=[f"Parse failure: {str(e)}"],
            )

        result = ASTGuardResult(is_safe=True, syntax_valid=True)

        # 2. Check for prohibited nodes, calls, and modules
        self._check_nodes(tree, result)

        # 3. Check for unbounded loops
        if self.disallow_loops_without_break:
            self._check_loops(tree, result)

        if result.errors or result.prohibited_nodes or result.unbounded_loops:
            result.is_safe = False

        return result

    def _check_nodes(self, tree: ast.AST, result: ASTGuardResult) -> None:
        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod in self.PROHIBITED_MODULES:
                        result.prohibited_nodes.append(f"Prohibited import: '{alias.name}' at line {node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if root_mod in self.PROHIBITED_MODULES:
                        result.prohibited_nodes.append(f"Prohibited from-import: '{node.module}' at line {node.lineno}")

            # Prohibited calls (eval, exec, __import__)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in self.PROHIBITED_CALLS:
                    result.prohibited_nodes.append(f"Prohibited call: '{node.func.id}()' at line {node.lineno}")

            # Prohibited dunder attributes
            elif isinstance(node, ast.Attribute):
                if node.attr in self.PROHIBITED_ATTRIBUTES:
                    result.prohibited_nodes.append(f"Prohibited attribute access: '{node.attr}' at line {node.lineno}")

    def _check_loops(self, tree: ast.AST, result: ASTGuardResult) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                # Check for constant true test: while True / while 1
                is_constant_true = False
                if isinstance(node.test, ast.Constant) and bool(node.test.value) is True:
                    is_constant_true = True
                elif isinstance(node.test, ast.NameConstant) and node.test.value is True:  # Python <=3.7 compat
                    is_constant_true = True

                if is_constant_true:
                    # Check if body contains any break or return
                    has_exit = any(
                        isinstance(child, (ast.Break, ast.Return, ast.Raise))
                        for child in ast.walk(node)
                    )
                    if not has_exit:
                        result.unbounded_loops = True
                        result.errors.append(
                            f"Unbounded loop detected: 'while True' lacking break/return condition at line {node.lineno}"
                        )
