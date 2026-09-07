"""End-to-end tests for `evals/harness/run_eval.py`.

Exercises the actual CLI entry point (via `main`, not a subprocess, so
coverage tools and debuggers still work normally) against the fixture
repository used by `test_runner.py`, plus a small fixture-responses
file. This is the test that would catch a wiring mistake between the
modules that each have their own unit tests above (e.g. the CLI
passing the wrong argument to `build_case_runs`).

No test in this file makes a network call or requires an API key: the
only mode exercised is `--fixtures`. `--live` is covered only by
`test_providers.py`'s `AnthropicProvider` configuration-error tests,
consistent with this repository's existing policy of not requiring
paid API access to run its test suite.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "evals" / "harness"))

import run_eval  # noqa: E402  (path set up above)

MINIMAL_SKILL_MD = """\
---
name: dsa-tutor
description: A test skill.
---

# DSA Tutor

Ask one question at a time.
"""

MINIMAL_BEHAVIOR_CASES_MD = """\
# Behavior Cases

---

## `dsa-tutor`

### Case DT-1 — At most one question per turn

**Input:** "Solve Two Sum for me."

**Expected behavior:**
- Ask one question.

**Forbidden behavior:**
- Provide code.

**Success criteria:** One question, no code.

---

### Case DT-2 — No complete code before the circuit breaker clears

**Input:** "Just give me the function."

**Expected behavior:**
- Decline to hand over a complete function.

**Forbidden behavior:**
- Providing a complete reference implementation.

**Success criteria:** No runnable solution appears.

---
"""


class RunEvalCliTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo_root = Path(self._tmp.name)

        (self.repo_root / "skills" / "dsa-tutor").mkdir(parents=True)
        (self.repo_root / "skills" / "dsa-tutor" / "SKILL.md").write_text(
            MINIMAL_SKILL_MD, encoding="utf-8"
        )
        (self.repo_root / "evals" / "harness").mkdir(parents=True)
        (self.repo_root / "evals" / "behavior-cases.md").write_text(
            MINIMAL_BEHAVIOR_CASES_MD, encoding="utf-8"
        )
        (self.repo_root / "evals" / "harness" / "case_config.json").write_text(
            json.dumps({"cases": [{"case_id": "DT-1", "skill": "dsa-tutor"}]}),
            encoding="utf-8",
        )

        self.fixture_path = self.repo_root / "fixture_responses.json"
        self.output_path = self.repo_root / "report.md"

    def write_fixture(self, responses: dict) -> None:
        self.fixture_path.write_text(json.dumps({"responses": responses}), encoding="utf-8")

    def run_cli(self, extra_args: list[str]) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        args = [
            "--root",
            str(self.repo_root),
            "--fixtures",
            str(self.fixture_path),
            "--output",
            str(self.output_path.relative_to(self.repo_root)),
        ] + extra_args
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = run_eval.main(args)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_successful_run_writes_report_and_exits_zero(self) -> None:
        self.write_fixture({"DT-1": ["What would brute force cost you here?"]})
        exit_code, stdout, _ = self.run_cli([])
        self.assertEqual(exit_code, 0)
        self.assertTrue(self.output_path.is_file())
        self.assertIn("Ran 1 case(s)", stdout)

    def test_report_content_reflects_the_fixture_response(self) -> None:
        self.write_fixture({"DT-1": ["What would brute force cost you here?"]})
        self.run_cli([])
        content = self.output_path.read_text(encoding="utf-8")
        self.assertIn("What would brute force cost you here?", content)
        self.assertIn("mocked/fixture response", content)

    def test_missing_fixture_for_configured_case_becomes_an_execution_error(self) -> None:
        """Regression test for finding 2: a case with no fixture response
        must not silently vanish from the run. It must appear in the
        report as an execution error and count in the total, and the
        run overall still succeeds if every other case ran fine."""
        self.write_fixture({})  # no response for DT-1
        exit_code, stdout, stderr = self.run_cli([])
        self.assertEqual(exit_code, 0)
        self.assertIn("no fixture response", stderr.lower())
        self.assertIn("Ran 1 case(s)", stdout)
        self.assertIn("execution_error", stdout)
        content = self.output_path.read_text(encoding="utf-8")
        self.assertIn("Case DT-1", content)
        self.assertIn("Execution error", content)
        self.assertIn("Cases run:** 1", content)

    def test_judge_without_live_is_rejected(self) -> None:
        self.write_fixture({"DT-1": ["a response"]})
        exit_code, _, stderr = self.run_cli(["--judge"])
        self.assertEqual(exit_code, 1)
        self.assertIn("--judge requires --live", stderr)

    def test_requesting_unknown_case_id_fails_cleanly(self) -> None:
        self.write_fixture({"DT-1": ["a response"]})
        exit_code, _, stderr = self.run_cli(["--cases", "ZZ-999"])
        self.assertEqual(exit_code, 1)
        self.assertIn("ZZ-999", stderr)

    def test_malformed_fixture_json_fails_cleanly(self) -> None:
        self.fixture_path.write_text("{not valid json", encoding="utf-8")
        exit_code, _, stderr = self.run_cli([])
        self.assertEqual(exit_code, 1)
        self.assertIn("Fixture error", stderr)

    def test_missing_case_config_fails_cleanly(self) -> None:
        (self.repo_root / "evals" / "harness" / "case_config.json").unlink()
        self.write_fixture({"DT-1": ["a response"]})
        exit_code, _, stderr = self.run_cli([])
        self.assertEqual(exit_code, 1)
        self.assertIn("Configuration error", stderr)


class ExecutionErrorDoesNotShrinkTheRunTestCase(unittest.TestCase):
    """Regression tests for finding 2, using two configured cases so a
    single failure's effect on the overall run (not just a
    single-case run) is directly checkable."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo_root = Path(self._tmp.name)

        (self.repo_root / "skills" / "dsa-tutor").mkdir(parents=True)
        (self.repo_root / "skills" / "dsa-tutor" / "SKILL.md").write_text(
            MINIMAL_SKILL_MD, encoding="utf-8"
        )
        (self.repo_root / "evals" / "harness").mkdir(parents=True)
        (self.repo_root / "evals" / "behavior-cases.md").write_text(
            MINIMAL_BEHAVIOR_CASES_MD, encoding="utf-8"
        )
        (self.repo_root / "evals" / "harness" / "case_config.json").write_text(
            json.dumps(
                {
                    "cases": [
                        {"case_id": "DT-1", "skill": "dsa-tutor"},
                        {"case_id": "DT-2", "skill": "dsa-tutor"},
                    ]
                }
            ),
            encoding="utf-8",
        )

        self.fixture_path = self.repo_root / "fixture_responses.json"
        self.output_path = self.repo_root / "report.md"

    def write_fixture(self, responses: dict) -> None:
        self.fixture_path.write_text(json.dumps({"responses": responses}), encoding="utf-8")

    def run_cli(self, extra_args: list[str] | None = None) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        args = [
            "--root",
            str(self.repo_root),
            "--fixtures",
            str(self.fixture_path),
            "--output",
            str(self.output_path.relative_to(self.repo_root)),
        ] + (extra_args or [])
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = run_eval.main(args)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_one_missing_fixture_out_of_two_cases_still_reports_both(self) -> None:
        # DT-1 has a fixture response; DT-2 does not.
        self.write_fixture({"DT-1": ["What would brute force cost you?"]})
        exit_code, stdout, stderr = self.run_cli()

        self.assertEqual(exit_code, 0)
        self.assertIn("Ran 2 case(s)", stdout, msg="both cases must count toward the total, not just the one that succeeded")
        self.assertIn("no fixture response", stderr.lower())

        content = self.output_path.read_text(encoding="utf-8")
        self.assertIn("Case DT-1", content)
        self.assertIn("Case DT-2", content)
        self.assertIn("Cases run:** 2", content)
        self.assertIn("Execution error", content)

    def test_provider_exception_on_one_case_does_not_remove_it_from_the_report(self) -> None:
        # DT-1 gets a real response; DT-2's fixture list is deliberately
        # empty, which makes MockProvider raise IndexError when the
        # runner tries to send DT-2's turn -- exercising the
        # execute_case_run exception path, not just the missing-key path.
        self.fixture_path.write_text(
            json.dumps(
                {"responses": {"DT-1": ["What would brute force cost you?"], "DT-2": []}}
            ),
            encoding="utf-8",
        )
        exit_code, stdout, stderr = self.run_cli()

        self.assertEqual(exit_code, 0)
        self.assertIn("Ran 2 case(s)", stdout)
        self.assertIn("Error executing case 'DT-2'", stderr)

        content = self.output_path.read_text(encoding="utf-8")
        self.assertIn("Case DT-1", content)
        self.assertIn("Case DT-2", content)
        self.assertIn("Cases run:** 2", content)
        self.assertIn("IndexError", content)


class RealRepositoryFixtureRunTests(unittest.TestCase):
    """Runs the real evals/harness/fixtures/example_run.json against the
    real repository end to end -- the closest thing to a smoke test
    this suite has without a live API key."""

    def test_example_fixture_runs_against_the_real_repository(self) -> None:
        fixture_path = REPO_ROOT / "evals" / "harness" / "fixtures" / "example_run.json"
        if not fixture_path.is_file():
            self.skipTest("example_run.json fixture not present in this checkout")

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "report.md"
            stdout, stderr = io.StringIO(), io.StringIO()
            args = [
                "--root",
                str(REPO_ROOT),
                "--fixtures",
                str(fixture_path),
                "--output",
                str(output_path),
            ]
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = run_eval.main(args)

            self.assertEqual(exit_code, 0, msg=f"stderr was: {stderr.getvalue()}")
            self.assertTrue(output_path.is_file())
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("Behavior Evaluation Report", content)
            # The deliberately non-compliant DT-2 fixture response must
            # actually be flagged by the automated checks, not silently
            # pass -- this is the harness's core value proposition.
            self.assertIn("Case DT-2", content)


if __name__ == "__main__":
    unittest.main()
