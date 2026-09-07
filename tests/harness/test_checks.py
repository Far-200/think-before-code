"""Tests for `evals/harness/checks.py`.

Covers the automated structural checks in isolation (code-block
detection, question counting, hard-stop phrase detection), the LLM
judge's response parsing (including malformed judge output, which
must degrade to "unclear" rather than crash), `evaluate_case`'s
combining logic — in particular that a judge saying "met" is
overridden to "needs_human_review" when an automated check directly
contradicts it (e.g. a fenced code block appearing in a response the
judge called compliant) — and that the judge prompt is built from the
*actual executed transcript* (setup turns plus the real final input,
including an `input_override`), not from the case's own parsed prose
`input_text`. That last point is a regression test for a real bug: the
judge previously only ever saw `case.input_text`, so a multi-turn case
lost all its setup-turn context and a case using `input_override` (like
SC-5's pasted Resume Pack) had the judge reasoning about a scenario
that never actually happened.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "evals" / "harness"))

import checks  # noqa: E402  (path set up above)
from case_parser import BehaviorCase  # noqa: E402
from providers import Message, MockProvider  # noqa: E402


def make_case(**overrides) -> BehaviorCase:
    defaults = dict(
        case_id="TEST-1",
        title="A test case",
        skill="dsa-tutor",
        input_text="Solve Two Sum for me.",
        relevant_learner_state=None,
        expected_behavior=["Ask one question."],
        forbidden_behavior=["Provide any code."],
        success_criteria="Exactly one question, no code.",
        source_line=1,
    )
    defaults.update(overrides)
    return BehaviorCase(**defaults)


class AutomatedChecksTests(unittest.TestCase):
    def test_no_code_block_by_default(self) -> None:
        result = checks.run_automated_checks(make_case(), "What would brute force cost you?")
        self.assertFalse(result.code_block_found)

    def test_fenced_code_block_is_detected(self) -> None:
        response = "Here you go:\n```python\ndef f():\n    pass\n```"
        result = checks.run_automated_checks(make_case(), response)
        self.assertTrue(result.code_block_found)
        self.assertTrue(any("code block" in note for note in result.notes))

    def test_inline_code_formatting_is_not_flagged_as_a_code_block(self) -> None:
        response = "What does the variable `left` represent here?"
        result = checks.run_automated_checks(make_case(), response)
        self.assertFalse(result.code_block_found)

    def test_question_count_reflects_question_marks(self) -> None:
        result = checks.run_automated_checks(make_case(), "What is x? And what is y?")
        self.assertEqual(result.question_count, 2)

    def test_hard_stop_phrase_is_detected_case_insensitively(self) -> None:
        result = checks.run_automated_checks(make_case(), "Here's The Solution: do X.")
        self.assertTrue(result.solution_opening_phrase_found)

    def test_no_hard_stop_phrase_in_a_compliant_response(self) -> None:
        response = "Before anything else, what would brute force cost you here?"
        result = checks.run_automated_checks(make_case(), response)
        self.assertFalse(result.solution_opening_phrase_found)


class LlmJudgeTests(unittest.TestCase):
    def test_valid_json_verdict_is_parsed(self) -> None:
        judge_provider = MockProvider(
            responses=['{"verdict": "met", "reasoning": "It asked one question."}']
        )
        transcript = [
            Message(role="user", content="Solve Two Sum for me."),
            Message(role="assistant", content="response text"),
        ]
        opinion = checks.run_llm_judge(make_case(), transcript, judge_provider)
        self.assertEqual(opinion.verdict, "met")
        self.assertIn("one question", opinion.reasoning)

    def test_json_wrapped_in_code_fence_is_parsed(self) -> None:
        judge_provider = MockProvider(
            responses=['```json\n{"verdict": "not_met", "reasoning": "It gave code."}\n```']
        )
        transcript = [
            Message(role="user", content="Solve Two Sum for me."),
            Message(role="assistant", content="response text"),
        ]
        opinion = checks.run_llm_judge(make_case(), transcript, judge_provider)
        self.assertEqual(opinion.verdict, "not_met")

    def test_malformed_json_degrades_to_unclear(self) -> None:
        judge_provider = MockProvider(responses=["I think this looks fine, roughly."])
        transcript = [
            Message(role="user", content="Solve Two Sum for me."),
            Message(role="assistant", content="response text"),
        ]
        opinion = checks.run_llm_judge(make_case(), transcript, judge_provider)
        self.assertEqual(opinion.verdict, "unclear")
        self.assertIn("could not be parsed", opinion.reasoning)

    def test_unrecognized_verdict_value_degrades_to_unclear(self) -> None:
        judge_provider = MockProvider(
            responses=['{"verdict": "sort_of", "reasoning": "mixed signals"}']
        )
        transcript = [
            Message(role="user", content="Solve Two Sum for me."),
            Message(role="assistant", content="response text"),
        ]
        opinion = checks.run_llm_judge(make_case(), transcript, judge_provider)
        self.assertEqual(opinion.verdict, "unclear")

    def test_raw_response_is_preserved(self) -> None:
        raw = '{"verdict": "met", "reasoning": "fine"}'
        judge_provider = MockProvider(responses=[raw])
        transcript = [
            Message(role="user", content="Solve Two Sum for me."),
            Message(role="assistant", content="response text"),
        ]
        opinion = checks.run_llm_judge(make_case(), transcript, judge_provider)
        self.assertEqual(opinion.raw_response, raw)

    def test_judge_prompt_includes_setup_turns(self) -> None:
        """Regression test: the judge must see scripted setup turns, not
        just the final input/response pair. Before the fix, the judge
        prompt was built from `case.input_text` alone and never saw
        `transcript` at all, so a multi-turn case's earlier context
        (e.g. DT-2's prior exchange establishing a named approach)
        was invisible to the judge."""
        captured_prompts: list[str] = []

        class CapturingProvider:
            def send(self, system_prompt, messages):
                captured_prompts.append(messages[0].content)
                return '{"verdict": "met", "reasoning": "ok"}'

        transcript = [
            Message(role="user", content="Can you help me solve Two Sum?"),
            Message(role="assistant", content="What would brute force cost you?"),
            Message(role="user", content="O(n^2). I think two pointers could work."),
            Message(role="assistant", content="Have you dry-run that idea yet?"),
        ]
        checks.run_llm_judge(make_case(), transcript, CapturingProvider())

        self.assertEqual(len(captured_prompts), 1)
        prompt = captured_prompts[0]
        self.assertIn("Can you help me solve Two Sum?", prompt)
        self.assertIn("O(n^2). I think two pointers could work.", prompt)
        self.assertIn("Have you dry-run that idea yet?", prompt)

    def test_judge_prompt_uses_input_override_not_parsed_input_text(self) -> None:
        """Regression test for the SC-5 scenario specifically: when a
        case's executed input differs from its parsed `input_text`
        (via `input_override` in case_config.json), the judge must see
        the text that was actually sent, not the prose description
        parsed from behavior-cases.md."""
        captured_prompts: list[str] = []

        class CapturingProvider:
            def send(self, system_prompt, messages):
                captured_prompts.append(messages[0].content)
                return '{"verdict": "met", "reasoning": "ok"}'

        case = make_case(
            case_id="SC-5",
            title="Resume Pack resumption fidelity",
            input_text=(
                "A new session opens with a valid, complete Resume Pack "
                "pasted in, whose 'Next step to resume from' names a "
                "specific next question."
            ),
        )
        overridden_input = "# Resume Pack\n\n**Skill:** dsa-tutor\n**Task:** Maximum Subarray\n"
        transcript = [
            Message(role="user", content=overridden_input),
            Message(role="assistant", content="Welcome back -- let's continue."),
        ]
        checks.run_llm_judge(case, transcript, CapturingProvider())

        prompt = captured_prompts[0]
        self.assertIn("Maximum Subarray", prompt)
        self.assertIn(overridden_input.strip().splitlines()[0], prompt)
        # The parsed prose input_text describes the scenario but is not
        # what was executed -- it must not be presented to the judge as
        # if it were the literal conversation.
        self.assertNotIn("A new session opens with a valid, complete", prompt)

    def test_judge_prompt_includes_the_final_response(self) -> None:
        captured_prompts: list[str] = []

        class CapturingProvider:
            def send(self, system_prompt, messages):
                captured_prompts.append(messages[0].content)
                return '{"verdict": "met", "reasoning": "ok"}'

        transcript = [
            Message(role="user", content="Solve Two Sum for me."),
            Message(role="assistant", content="What would brute force cost you here?"),
        ]
        checks.run_llm_judge(make_case(), transcript, CapturingProvider())

        self.assertIn("What would brute force cost you here?", captured_prompts[0])


class EvaluateCaseTests(unittest.TestCase):
    def test_no_judge_configured_is_needs_human_review(self) -> None:
        case = make_case()
        transcript = [Message(role="user", content=case.input_text)]
        result = checks.evaluate_case(case, transcript, "One question?", judge_provider=None)
        self.assertEqual(result.verdict, "needs_human_review")
        self.assertIsNone(result.judge)

    def test_judge_met_with_no_contradiction_is_likely_met(self) -> None:
        case = make_case()
        transcript = [Message(role="user", content=case.input_text)]
        judge_provider = MockProvider(
            responses=['{"verdict": "met", "reasoning": "Compliant."}']
        )
        result = checks.evaluate_case(
            case, transcript, "What would brute force cost you?", judge_provider
        )
        self.assertEqual(result.verdict, "likely_met")

    def test_judge_met_but_code_block_present_is_downgraded_to_needs_review(self) -> None:
        case = make_case()
        transcript = [Message(role="user", content=case.input_text)]
        judge_provider = MockProvider(
            responses=['{"verdict": "met", "reasoning": "Looks fine."}']
        )
        response_with_code = "Sure:\n```python\ndef f(): pass\n```"
        result = checks.evaluate_case(case, transcript, response_with_code, judge_provider)
        self.assertEqual(
            result.verdict,
            "needs_human_review",
            msg="An automated code-block hit should override an incorrect 'met' judge opinion",
        )

    def test_judge_not_met_is_likely_not_met(self) -> None:
        case = make_case()
        transcript = [Message(role="user", content=case.input_text)]
        judge_provider = MockProvider(
            responses=['{"verdict": "not_met", "reasoning": "Gave the solution away."}']
        )
        result = checks.evaluate_case(case, transcript, "Here's the solution: ...", judge_provider)
        self.assertEqual(result.verdict, "likely_not_met")

    def test_judge_unclear_is_needs_human_review(self) -> None:
        case = make_case()
        transcript = [Message(role="user", content=case.input_text)]
        judge_provider = MockProvider(
            responses=['{"verdict": "unclear", "reasoning": "Ambiguous."}']
        )
        result = checks.evaluate_case(case, transcript, "Some response.", judge_provider)
        self.assertEqual(result.verdict, "needs_human_review")

    def test_judge_exception_does_not_crash_evaluate_case(self) -> None:
        case = make_case()
        transcript = [Message(role="user", content=case.input_text)]
        judge_provider = MockProvider(responses=[])  # will raise IndexError when called
        result = checks.evaluate_case(case, transcript, "Some response.", judge_provider)
        self.assertEqual(result.verdict, "needs_human_review")
        self.assertIsNone(result.judge)

    def test_automated_checks_always_run_regardless_of_judge(self) -> None:
        case = make_case()
        transcript = [Message(role="user", content=case.input_text)]
        result = checks.evaluate_case(case, transcript, "```code```", judge_provider=None)
        self.assertTrue(result.automated.code_block_found)

    def test_evaluate_case_passes_full_transcript_to_judge(self) -> None:
        """Regression test: evaluate_case must hand run_llm_judge the
        full transcript it received, not just the final response
        text, so multi-turn context reaches the judge end to end."""
        captured_prompts: list[str] = []

        class CapturingProvider:
            def send(self, system_prompt, messages):
                captured_prompts.append(messages[0].content)
                return '{"verdict": "met", "reasoning": "ok"}'

        case = make_case()
        transcript = [
            Message(role="user", content="earlier setup turn content"),
            Message(role="assistant", content="earlier coach reply"),
            Message(role="user", content="final input"),
            Message(role="assistant", content="final response"),
        ]
        checks.evaluate_case(case, transcript, "final response", CapturingProvider())

        prompt = captured_prompts[0]
        self.assertIn("earlier setup turn content", prompt)
        self.assertIn("earlier coach reply", prompt)


class ExecutionErrorResultTests(unittest.TestCase):
    """Regression tests for finding 2: a case that fails during
    execution must produce a first-class CaseResult with a distinct
    verdict, not be silently dropped."""

    def test_make_execution_error_result_has_execution_error_verdict(self) -> None:
        case = make_case()
        result = checks.make_execution_error_result(case, "boom")
        self.assertEqual(result.verdict, "execution_error")
        self.assertEqual(result.error_message, "boom")
        self.assertIsNone(result.automated)
        self.assertIsNone(result.judge)

    def test_make_execution_error_result_without_transcript_defaults_to_none(self) -> None:
        case = make_case()
        result = checks.make_execution_error_result(case, "boom")
        self.assertIsNone(result.transcript)

    def test_make_execution_error_result_preserves_partial_transcript(self) -> None:
        case = make_case()
        partial = [Message(role="user", content="setup turn that made it through")]
        result = checks.make_execution_error_result(case, "boom", transcript=partial)
        self.assertEqual(result.transcript, partial)

    def test_execution_error_verdict_is_distinct_from_needs_human_review(self) -> None:
        case = make_case()
        error_result = checks.make_execution_error_result(case, "boom")
        transcript = [Message(role="user", content=case.input_text)]
        normal_result = checks.evaluate_case(case, transcript, "a response", judge_provider=None)
        self.assertNotEqual(error_result.verdict, normal_result.verdict)


if __name__ == "__main__":
    unittest.main()
