"""
Explicit termination handlers and signals for RLM execution loops.
"""

from typing import Any, Callable, Tuple
from recursive_lm.core.state import RLMState


class TerminationSignal(Exception):
    """
    Control flow exception raised by FINAL or FINAL_VAR to cleanly exit
    the REPL execution loop and return terminal output.
    """

    def __init__(self, value: Any, is_variable_name: bool = False):
        self.value = value
        self.is_variable_name = is_variable_name
        super().__init__(f"RLM Termination Triggered: {value}")


def create_termination_tools(state: RLMState) -> Tuple[Callable[[str], None], Callable[[str], None]]:
    """
    Factory creating bound FINAL and FINAL_VAR callable tools for a given RLMState.
    """

    def FINAL(answer: Any) -> None:
        """
        Directly terminates the RLM loop and emits the provided answer string or object.
        """
        state.set_termination(answer)
        raise TerminationSignal(value=answer, is_variable_name=False)

    def FINAL_VAR(var_name: str) -> None:
        """
        Terminates the RLM loop and emits the contents of the designated REPL state variable.
        """
        resolved_val = state.get_variable(var_name)
        state.set_termination(resolved_val)
        raise TerminationSignal(value=resolved_val, is_variable_name=True)

    return FINAL, FINAL_VAR
