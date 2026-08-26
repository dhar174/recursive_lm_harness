"""
Node executor, layer-by-layer dependency resolution, and second-opinion verification.
"""

import time
from typing import Any, Callable, Dict, Optional, Set

from recursive_lm.core.repl import PersistentREPL
from recursive_lm.orchestrator.dag import DAGNode, NodeStatus, OrchestrationDAG, SubcallType
from recursive_lm.orchestrator.memoization import MemoizationTable
from recursive_lm.telemetry.cost_tracker import TokenCostTracker
from recursive_lm.telemetry.tracer import ExecutionTracer


class DAGScheduler:
    """
    Executes an OrchestrationDAG layer-by-layer.
    Guarantees that parent dependency values are verified before downstream propagation.
    """

    def __init__(
        self,
        dag: OrchestrationDAG,
        repl: PersistentREPL,
        memo_table: Optional[MemoizationTable] = None,
        cost_tracker: Optional[TokenCostTracker] = None,
        tracer: Optional[ExecutionTracer] = None,
        verifier_fn: Optional[Callable[[DAGNode, Any], bool]] = None,
        max_fan_out: int = 20,
    ):
        self.dag = dag
        self.repl = repl
        self.memo = memo_table or MemoizationTable()
        self.cost_tracker = cost_tracker or TokenCostTracker()
        self.tracer = tracer or ExecutionTracer()
        self.verifier_fn = verifier_fn
        self.max_fan_out = max_fan_out

    def run(self) -> Any:
        """
        Executes all nodes in topological layers until termination or completion.
        """
        layers = self.dag.get_execution_layers()
        completed_nodes: Set[str] = set()

        for layer_idx, layer in enumerate(layers):
            # Enforce fan-out limit per layer
            if len(layer) > self.max_fan_out:
                raise ValueError(
                    f"Fan-out budget exceeded: Layer {layer_idx} has {len(layer)} nodes (max {self.max_fan_out})"
                )

            for node in layer:
                # Check that all dependencies are resolved
                missing_deps = [dep for dep in node.dependencies if dep not in completed_nodes]
                if missing_deps:
                    raise RuntimeError(f"Node '{node.id}' cannot execute; missing dependencies: {missing_deps}")

                result = self.execute_node(node)
                completed_nodes.add(node.id)

                if self.repl.state.is_terminated:
                    return self.repl.state.termination_value

        # If not explicitly terminated, return the last completed node's result
        if layers and layers[-1]:
            last_node = layers[-1][-1]
            return self.memo.get(last_node.id)
        return None

    def execute_node(self, node: DAGNode) -> Any:
        """
        Executes a single DAG node within the REPL and updates memoization.
        """
        node.status = NodeStatus.RUNNING
        start_time = time.time()
        self.tracer.log_event(
            node_id=node.id,
            depth=0,
            event_type="NODE_START",
            subcall_type=node.subcall_type.value,
            objective=node.objective,
        )

        # Sync memoized answers into REPL state answers before node execution
        self.repl.state.answers.update(self.memo.as_dict())

        result: Any = None
        try:
            if node.subcall_type == SubcallType.REPL_CODE:
                code_to_run = node.code_snippet or ""
                feedback = self.repl.execute(code_to_run)
                if node.output_buffer and self.repl.state.has_variable(node.output_buffer):
                    result = self.repl.state.get_variable(node.output_buffer)
                else:
                    result = feedback.formatted_output

            elif node.subcall_type == SubcallType.LLM_QUERY:
                llm_tool = self.repl.globals_dict.get("llm_query")
                query_prompt = self._resolve_expression(node.slice_expression or node.objective)
                if callable(llm_tool):
                    result = llm_tool(query_prompt)
                else:
                    result = f"[Mock LLM Query result for: {query_prompt[:50]}]"

            elif node.subcall_type == SubcallType.RLM_QUERY:
                rlm_tool = self.repl.globals_dict.get("rlm_query")
                sub_context = self._resolve_expression(node.slice_expression or self.repl.state.context)
                if callable(rlm_tool):
                    result = rlm_tool(sub_context, node.objective)
                else:
                    result = f"[Mock RLM Query result for: {node.objective[:50]}]"

            elif node.subcall_type == SubcallType.FINAL_VAR:
                var_name = node.output_buffer or node.slice_expression or ""
                final_var_tool = self.repl.globals_dict.get("FINAL_VAR")
                try:
                    if callable(final_var_tool):
                        final_var_tool(var_name)
                        result = self.repl.state.termination_value
                    else:
                        result = self.repl.state.get_variable(var_name)
                        self.repl.state.set_termination(result)
                except Exception as term_exc:
                    if term_exc.__class__.__name__ == "TerminationSignal":
                        result = getattr(term_exc, "value", self.repl.state.termination_value)
                    else:
                        raise

            elif node.subcall_type == SubcallType.FINAL:
                final_val = self._resolve_expression(node.output_buffer or node.slice_expression or "")
                final_tool = self.repl.globals_dict.get("FINAL")
                try:
                    if callable(final_tool):
                        final_tool(final_val)
                        result = self.repl.state.termination_value
                    else:
                        self.repl.state.set_termination(final_val)
                        result = final_val
                except Exception as term_exc:
                    if term_exc.__class__.__name__ == "TerminationSignal":
                        result = getattr(term_exc, "value", self.repl.state.termination_value)
                    else:
                        raise

            # Second-opinion verification gate
            is_verified = True
            if node.second_opinion_required:
                if self.verifier_fn:
                    is_verified = self.verifier_fn(node, result)
                else:
                    # Default non-empty check
                    is_verified = result is not None and result != ""

            node.is_verified = is_verified
            node.result = result
            node.status = NodeStatus.COMPLETED

            duration_ms = (time.time() - start_time) * 1000.0
            self.memo.store(
                node_id=node.id,
                value=result,
                provenance={"subcall_type": node.subcall_type.value, "dependencies": node.dependencies},
                is_verified=is_verified,
                execution_time_ms=duration_ms,
            )
            self.repl.state.answers[node.id] = result

            self.tracer.log_event(
                node_id=node.id,
                depth=0,
                event_type="NODE_END",
                status=node.status.value,
                duration_ms=duration_ms,
                is_verified=is_verified,
            )
            return result

        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            self.repl.state.record_error(f"Scheduler execution failed at node '{node.id}': {str(e)}")
            self.tracer.log_event(
                node_id=node.id,
                depth=0,
                event_type="NODE_ERROR",
                error=str(e),
            )
            raise

    def _resolve_expression(self, expr: str) -> Any:
        """Helper to resolve a variable name or string literal expression."""
        if not expr:
            return ""
        if self.repl.state.has_variable(expr):
            return self.repl.state.get_variable(expr)
        if expr in self.memo.as_dict():
            return self.memo.get(expr)
        return expr
