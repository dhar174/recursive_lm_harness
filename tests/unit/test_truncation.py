"""
Unit tests for StdoutTruncator and constant-size feedback formatting.
"""

from recursive_lm.core.truncation import StdoutTruncator, TruncationFeedback


def test_short_stdout_no_truncation():
    truncator = StdoutTruncator(head_limit=50, tail_limit=50, max_untruncated_chars=200)
    raw = "Short stdout output below threshold."
    feedback: TruncationFeedback = truncator.truncate(raw, exit_code=0)

    assert feedback.was_truncated is False
    assert feedback.char_count == len(raw)
    assert feedback.line_count == 1
    assert feedback.exit_code == 0
    assert feedback.formatted_output == raw


def test_long_stdout_truncation():
    truncator = StdoutTruncator(head_limit=20, tail_limit=20, max_untruncated_chars=50)
    raw = "START_1234567890" + ("." * 100) + "END_1234567890"
    feedback: TruncationFeedback = truncator.truncate(raw, exit_code=0)

    assert feedback.was_truncated is True
    assert feedback.char_count == len(raw)
    assert feedback.head == raw[:20]
    assert feedback.tail == raw[-20:]
    assert "[STDOUT TRUNCATED" in feedback.formatted_output
    assert f"chars: {len(raw)}" in feedback.formatted_output
    assert "HEAD: START_1234567890" in feedback.formatted_output
    assert "TAIL: " in feedback.formatted_output


def test_multiline_stdout_line_count():
    truncator = StdoutTruncator(head_limit=10, tail_limit=10, max_untruncated_chars=20)
    raw = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6"
    feedback: TruncationFeedback = truncator.truncate(raw, exit_code=1)

    assert feedback.line_count == 6
    assert feedback.exit_code == 1
    assert "exit: 1" in feedback.formatted_output
