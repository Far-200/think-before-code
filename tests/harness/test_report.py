"""Tests for `evals/harness/report.py`.

Covers the report renders the right content (case sections, verdict
labels, judge opinion or its absence), never nests a fenced code block
inside another fenced code block (the bug found and fixed while
building this harness — see report.py's `_render_transcript`
docstring), and that `write_report` actually writes a file.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "evals" / "harness"))

import report  # noqa: E402  (path set up above)
from case_parser import BehaviorCase  # noqa: E402
from checks import (  # noqa: E402
    AutomatedCheckResult,
    CaseResult,
    JudgeOpinion,
    make_execution_error_result,
)
from providers import Message  # noqa: E402


def make_case(**overrides) -> BehaviorCase:
    defaults = dict(
        case_id="DT-1",
        title="At most one question per turn",
        skill="dsa-tutor",
        input_text='"Solve Two Sum for me."',
        relevant_learner_state=None,
        expected_behavior=["Ask one question."],
        forbidden_behavior=["Provide any code."],
        success_criteria="Exactly one question, no code.",
        source_line=14,
    )
    defaults.update(overrides)
    return BehaviorCase(**defaults)


def make_result(**overrides) -> CaseResult:
    case = overrides.pop("case", make_case())
    defaults = dict(
        case=case,
        transcript=[
            Message(role="user", content=case.input_text),
            Message(role="assistant", content="What would brute force cost you?"),
        ],
        automated=AutomatedCheckResult(
            code_block_found=False, question_count=1, solution_opening_phrase_found=False
        ),
        judge=None,
        verdict="needs_human_review",
    )
    defaults.update(overrides)
    return CaseResult(**defaults)


class RenderReportTests(unittest.TestCase):
    def test_header_includes_run_metadata(self) -> None:
        text = report.render_report(
            [make_result()], is_live=False, model_label="mock (fixture-driven)", judge_label=None
        )
        self.assertIn("MOCKED run", text)
        self.assertIn("mock (fixture-driven)", text)
        self.assertIn("LLM judge: none configured", text)

    def test_live_run_is_labeled_as_live(self) -> None:
        text = report.render_report(
            [make_result()], is_live=True, model_label="claude-sonnet-4-6", judge_label=None
        )
        self.assertIn("LIVE model run", text)
        self.assertIn("claude-sonnet-4-6", text)

    def test_case_section_includes_case_id_and_title(self) -> None:
        text = report.render_report(
            [make_result()], is_live=False, model_label="mock", judge_label=None
        )
        self.assertIn("Case DT-1", text)
        self.assertIn("At most one question per turn", text)

    def test_expected_and_forbidden_behavior_are_rendered(self) -> None:
        text = report.render_report(
            [make_result()], is_live=False, model_label="mock", judge_label=None
        )
        self.assertIn("Ask one question.", text)
        self.assertIn("Provide any code.", text)

    def test_no_judge_shows_explicit_absence_note(self) -> None:
        text = report.render_report(
            [make_result(judge=None)], is_live=False, model_label="mock", judge_label=None
        )
        self.assertIn("No judge was configured", text)

    def test_judge_opinion_is_shown_labeled_as_opinion(self) -> None:
        judge = JudgeOpinion(verdict="met", reasoning="It asked one clean question.", raw_response="{}")
        text = report.render_report(
            [make_result(judge=judge, verdict="likely_met")],
            is_live=True,
            model_label="claude-sonnet-4-6",
            judge_label="claude-sonnet-4-6",
        )
        self.assertIn("not a guarantee of correctness", text)
        self.assertIn("It asked one clean question.", text)

    def test_transcript_with_embedded_code_fence_does_not_break_rendering(self) -> None:
        # This is the bug caught while building the harness: a response
        # containing a ``` fence must not be nested inside the
        # transcript's own ``` fence.
        case = make_case(case_id="DT-2", title="Code circuit breaker")
        transcript = [
            Message(role="user", content="give me the function"),
            Message(role="assistant", content="Sure:\n```python\ndef f():\n    pass\n```"),
        ]
        result = make_result(case=case, transcript=transcript)
        text = report.render_report(
            [result], is_live=False, model_label="mock", judge_label=None
        )
        # The transcript must not use a literal ```text fence wrapper,
        # since that would nest with the response's own ``` fence.
        self.assertNotIn("```text", text)
        self.assertIn("def f():", text)

    def test_summary_counts_verdicts(self) -> None:
        results = [
            make_result(verdict="likely_met"),
            make_result(case=make_case(case_id="DT-2"), verdict="likely_met"),
            make_result(case=make_case(case_id="DT-3"), verdict="needs_human_review"),
        ]
        text = report.render_report(results, is_live=False, model_label="mock", judge_label=None)
        self.assertIn("Cases run:** 3", text)

    def test_automated_check_values_are_rendered(self) -> None:
        automated = AutomatedCheckResult(
            code_block_found=True, question_count=0, solution_opening_phrase_found=True
        )
        result = make_result(automated=automated)
        text = report.render_report([result], is_live=False, model_label="mock", judge_label=None)
        self.assertIn("Fenced code block found: `True`", text)
        self.assertIn('Named hard-stop phrase found (e.g. "here\'s the solution"): `True`', text)


class ExecutionErrorRenderingTests(unittest.TestCase):
    """Regression tests for finding 2: a case that failed during
    execution must appear as a distinct, visible section in the
    report and must count in the summary and total — never be
    silently absent."""

    def test_execution_error_case_appears_in_report(self) -> None:
        case = make_case(case_id="DT-2", title="No complete code before the circuit breaker clears")
        error_result = make_execution_error_result(case, "IndexError: ran out of scripted responses")
        text = report.render_report(
            [error_result], is_live=False, model_label="mock", judge_label=None
        )
        self.assertIn("Case DT-2", text)
        self.assertIn("Execution error", text)
        self.assertIn("IndexError: ran out of scripted responses", text)

    def test_execution_error_does_not_crash_on_missing_automated_or_judge(self) -> None:
        # Both `automated` and `judge` are None on an execution-error
        # result; rendering must not attempt to read attributes off them.
        case = make_case()
        error_result = make_execution_error_result(case, "boom")
        self.assertIsNone(error_result.automated)
        self.assertIsNone(error_result.judge)
        try:
            report.render_report([error_result], is_live=False, model_label="mock", judge_label=None)
        except AttributeError:
            self.fail("rendering an execution-error result must not touch automated/judge fields")

    def test_execution_error_counts_toward_summary_and_total(self) -> None:
        good_result = make_result(verdict="likely_met")
        error_result = make_execution_error_result(make_case(case_id="DT-2"), "boom")
        text = report.render_report(
            [good_result, error_result], is_live=False, model_label="mock", judge_label=None
        )
        self.assertIn("Cases run:** 2", text)
        self.assertIn("Execution error", text)

    def test_execution_error_without_transcript_shows_placeholder(self) -> None:
        case = make_case()
        error_result = make_execution_error_result(case, "boom", transcript=None)
        text = report.render_report(
            [error_result], is_live=False, model_label="mock", judge_label=None
        )
        self.assertIn("No conversation history is available", text)

    def test_execution_error_with_partial_transcript_renders_it(self) -> None:
        case = make_case()
        partial = [Message(role="user", content="a setup turn that made it through")]
        error_result = make_execution_error_result(case, "boom", transcript=partial)
        text = report.render_report(
            [error_result], is_live=False, model_label="mock", judge_label=None
        )
        self.assertIn("a setup turn that made it through", text)

    def test_missing_error_message_shows_placeholder_not_blank(self) -> None:
        case = make_case()
        error_result = CaseResult(
            case=case,
            transcript=None,
            automated=None,
            judge=None,
            verdict="execution_error",
            error_message=None,
        )
        text = report.render_report(
            [error_result], is_live=False, model_label="mock", judge_label=None
        )
        self.assertIn("no error message was recorded", text)


class WriteReportTests(unittest.TestCase):
    def test_write_report_creates_file_and_parent_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "nested" / "dir" / "report.md"
            report.write_report(
                [make_result()],
                output_path,
                is_live=False,
                model_label="mock",
                judge_label=None,
            )
            self.assertTrue(output_path.is_file())
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("Behavior Evaluation Report", content)


if __name__ == "__main__":
    unittest.main()
