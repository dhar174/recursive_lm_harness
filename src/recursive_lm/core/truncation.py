"""
Constant-size stdout truncation handler to prevent context window saturation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TruncationFeedback:
    """
    Standard constant-size execution feedback tuple:
    <char_count, line_count, head, tail, exit_code>
    """
    char_count: int
    line_count: int
    head: str
    tail: str
    exit_code: int
    formatted_output: str
    was_truncated: bool


class StdoutTruncator:
    """
    Intercepts and truncates raw REPL stdout to constant-size metadata feedback.
    """

    def __init__(
        self,
        head_limit: int = 100,
        tail_limit: int = 100,
        max_untruncated_chars: int = 250,
    ):
        self.head_limit = head_limit
        self.tail_limit = tail_limit
        self.max_untruncated_chars = max_untruncated_chars

    def truncate(self, raw_stdout: str, exit_code: int = 0) -> TruncationFeedback:
        """
        Truncates raw stdout to constant-size feedback tuple if exceeding threshold.
        """
        char_count = len(raw_stdout)
        lines = raw_stdout.splitlines()
        line_count = len(lines)

        if char_count <= self.max_untruncated_chars:
            return TruncationFeedback(
                char_count=char_count,
                line_count=line_count,
                head=raw_stdout,
                tail=raw_stdout,
                exit_code=exit_code,
                formatted_output=raw_stdout,
                was_truncated=False,
            )

        head = raw_stdout[: self.head_limit]
        tail = raw_stdout[-self.tail_limit :] if self.tail_limit > 0 else ""
        omitted = char_count - len(head) - len(tail)

        formatted = (
            f"[STDOUT TRUNCATED | chars: {char_count} | lines: {line_count} | exit: {exit_code}]\n"
            f"HEAD: {head}\n"
            f"... [{omitted} chars omitted] ...\n"
            f"TAIL: {tail}"
        )

        return TruncationFeedback(
            char_count=char_count,
            line_count=line_count,
            head=head,
            tail=tail,
            exit_code=exit_code,
            formatted_output=formatted,
            was_truncated=True,
        )
