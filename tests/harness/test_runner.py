"""Tests for `evals/harness/runner.py`.

Covers system-prompt loading from a `SKILL.md` (including the
frontmatter-stripping and its failure mode), `case_config.json`
validation, building `CaseRun`s against a fixture repository (not the
real one, so these tests don't churn when a real case or skill
changes), and that `execute_case_run` calls the provider exactly once
with the full history.

One test does build against the real repository root to confirm the
real `case_config.json` and `evals/behavior-cases.md` are mutually
consistent — every case id configured in case_config.json actually
exists in behavior-cases.md, and every configured skill actually has a
SKILL.md. This is the test most likely to catch a future edit that
renames a case or skill without updating the other file.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "evals" / "harness"))

import runner  # noqa: E402  (path set up above)
from providers import Message, MockProvider  # noqa: E402


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
"""


class FixtureRepoTestCase(unittest.TestCase):
    """Builds a minimal, throwaway repository layout for runner tests."""

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

    def write_config(self, cases: list[dict]) -> None:
        config_path = self.repo_root / "evals" / "harness" / "case_config.json"
        config_path.write_text(json.dumps({"cases": cases}), encoding="utf-8")


class LoadSkillSystemPromptTests(FixtureRepoTestCase):
    def test_loads_and_strips_frontmatter(self) -> None:
        prompt = runner.load_skill_system_prompt(self.repo_root, "dsa-tutor")
        self.assertNotIn("---", prompt)
        self.assertIn("Ask one question at a time.", prompt)

    def test_missing_skill_raises(self) -> None:
        with self.assertRaises(runner.RunnerConfigurationError):
            runner.load_skill_system_prompt(self.repo_root, "does-not-exist")

    def test_missing_frontmatter_raises(self) -> None:
        skill_dir = self.repo_root / "skills" / "no-frontmatter"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# No frontmatter here\n", encoding="utf-8")
        with self.assertRaises(runner.RunnerConfigurationError):
            runner.load_skill_system_prompt(self.repo_root, "no-frontmatter")


class LoadCaseConfigTests(FixtureRepoTestCase):
    def test_missing_config_file_raises(self) -> None:
        with self.assertRaises(runner.RunnerConfigurationError):
            runner.load_case_config(self.repo_root)

    def test_invalid_json_raises(self) -> None:
        config_path = self.repo_root / "evals" / "harness" / "case_config.json"
        config_path.write_text("{not valid json", encoding="utf-8")
        with self.assertRaises(runner.RunnerConfigurationError):
            runner.load_case_config(self.repo_root)

    def test_missing_cases_key_raises(self) -> None:
        config_path = self.repo_root / "evals" / "harness" / "case_config.json"
        config_path.write_text(json.dumps({}), encoding="utf-8")
        with self.assertRaises(runner.RunnerConfigurationError):
            runner.load_case_config(self.repo_root)

    def test_case_entry_missing_required_key_raises(self) -> None:
        self.write_config([{"case_id": "DT-1"}])  # missing "skill"
        with self.assertRaises(runner.RunnerConfigurationError):
            runner.load_case_config(self.repo_root)

    def test_valid_config_loads(self) -> None:
        self.write_config([{"case_id": "DT-1", "skill": "dsa-tutor"}])
        config = runner.load_case_config(self.repo_root)
        self.assertEqual(len(config["cases"]), 1)


class BuildCaseRunsTests(FixtureRepoTestCase):
    def test_builds_a_single_turn_case(self) -> None:
        self.write_config([{"case_id": "DT-1", "skill": "dsa-tutor"}])
        runs = runner.build_case_runs(self.repo_root)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].case.case_id, "DT-1")
        self.assertEqual(runs[0].skill, "dsa-tutor")
        self.assertEqual(runs[0].setup_turns, [])
        self.assertIn("Two Sum", runs[0].final_input)

    def test_setup_turns_are_converted_to_messages(self) -> None:
        self.write_config(
            [
                {
                    "case_id": "DT-1",
                    "skill": "dsa-tutor",
                    "setup_turns": [
                        {"role": "user", "content": "hello"},
                        {"role": "assistant", "content": "hi there"},
                    ],
                }
            ]
        )
        runs = runner.build_case_runs(self.repo_root)
        self.assertEqual(len(runs[0].setup_turns), 2)
        self.assertEqual(runs[0].setup_turns[0], Message(role="user", content="hello"))

    def test_input_override_replaces_parsed_input(self) -> None:
        self.write_config(
            [{"case_id": "DT-1", "skill": "dsa-tutor", "input_override": "custom input"}]
        )
        runs = runner.build_case_runs(self.repo_root)
        self.assertEqual(runs[0].final_input, "custom input")

    def test_filtering_by_case_ids(self) -> None:
        self.write_config(
            [
                {"case_id": "DT-1", "skill": "dsa-tutor"},
            ]
        )
        runs = runner.build_case_runs(self.repo_root, case_ids=["DT-1"])
        self.assertEqual(len(runs), 1)

    def test_unknown_requested_case_id_raises(self) -> None:
        self.write_config([{"case_id": "DT-1", "skill": "dsa-tutor"}])
        with self.assertRaises(runner.RunnerConfigurationError):
            runner.build_case_runs(self.repo_root, case_ids=["ZZ-999"])

    def test_config_referencing_nonexistent_case_raises(self) -> None:
        self.write_config([{"case_id": "ZZ-999", "skill": "dsa-tutor"}])
        with self.assertRaises(runner.RunnerConfigurationError):
            runner.build_case_runs(self.repo_root)

    def test_config_referencing_nonexistent_skill_raises(self) -> None:
        self.write_config([{"case_id": "DT-1", "skill": "no-such-skill"}])
        with self.assertRaises(runner.RunnerConfigurationError):
            runner.build_case_runs(self.repo_root)


class ExecuteCaseRunTests(FixtureRepoTestCase):
    def test_provider_called_once_with_full_history(self) -> None:
        self.write_config(
            [
                {
                    "case_id": "DT-1",
                    "skill": "dsa-tutor",
                    "setup_turns": [{"role": "user", "content": "earlier turn"}],
                }
            ]
        )
        runs = runner.build_case_runs(self.repo_root)
        provider = MockProvider(responses=["the reply"])

        transcript, response_text = runner.execute_case_run(runs[0], provider)

        self.assertEqual(response_text, "the reply")
        # setup turn + final input + final response
        self.assertEqual(len(transcript), 3)
        self.assertEqual(transcript[0].content, "earlier turn")
        self.assertIn("Two Sum", transcript[1].content)
        self.assertEqual(transcript[-1], Message(role="assistant", content="the reply"))

    def test_provider_not_called_extra_times_for_setup_turns(self) -> None:
        # A provider scripted with exactly one response must not raise,
        # proving setup turns are replayed as history, not sent to the
        # provider for their own fresh replies.
        self.write_config(
            [
                {
                    "case_id": "DT-1",
                    "skill": "dsa-tutor",
                    "setup_turns": [
                        {"role": "user", "content": "a"},
                        {"role": "assistant", "content": "b"},
                        {"role": "user", "content": "c"},
                        {"role": "assistant", "content": "d"},
                    ],
                }
            ]
        )
        runs = runner.build_case_runs(self.repo_root)
        provider = MockProvider(responses=["only one reply needed"])
        _, response_text = runner.execute_case_run(runs[0], provider)
        self.assertEqual(response_text, "only one reply needed")


class RealRepositoryConsistencyTests(unittest.TestCase):
    """Confirms the real case_config.json and behavior-cases.md agree."""

    def test_real_case_config_builds_against_real_repository(self) -> None:
        config_path = REPO_ROOT / "evals" / "harness" / "case_config.json"
        if not config_path.is_file():
            self.skipTest("evals/harness/case_config.json not present in this checkout")
        runs = runner.build_case_runs(REPO_ROOT)
        self.assertGreater(len(runs), 0)
        for case_run in runs:
            self.assertTrue(case_run.system_prompt)
            self.assertTrue(case_run.final_input)


if __name__ == "__main__":
    unittest.main()
