"""Tests for `scripts/validate_evals.py`.

These protect the guarantees that used to live inline in
`.github/workflows/validate-skills.yml`: the activation CSV keeps its
shape, its ids stay unique, every `target_skill` names a skill that
actually exists, and — the rule with real teeth — every skill keeps
both a positive and a negative activation case, so no skill ships with
an untested activation boundary.

Fixtures are generated into a temporary directory. The one test that
touches the real repository only reads it.
"""

from __future__ import annotations

import contextlib
import csv
import io
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_evals  # noqa: E402  (path set up above)


HEADER = validate_evals.EXPECTED_HEADER

# A minimal but realistic pair of rows: one positive, one negative.
BASE_ROWS = [
    [
        "A001",
        "dsa-tutor",
        "true",
        "Help me solve Two Sum, but ask me questions instead of answering.",
        "Guided problem solving without an immediate solution.",
    ],
    [
        "A002",
        "dsa-tutor",
        "false",
        "Just paste the finished Python solution for Merge Intervals.",
        "Learner opts out of the learning process this skill protects.",
    ],
]


class EvalFixtureTestCase(unittest.TestCase):
    """Base case providing a throwaway repository root."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo_root = Path(self._tmp.name)
        self.skills_dir = self.repo_root / "skills"
        self.evals_dir = self.repo_root / "evals"
        self.evals_dir.mkdir()
        self.csv_path = self.evals_dir / "activation-prompts.csv"

    def add_skill(self, name: str, *, with_skill_md: bool = True) -> Path:
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        if with_skill_md:
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: Coaches.\n---\n", encoding="utf-8"
            )
        return skill_dir

    def write_csv(self, rows: list[list[str]], *, header: list[str] | None = None):
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if header is not None:
                writer.writerow(header)
            writer.writerows(rows)

    def validate(self) -> list[str]:
        return validate_evals.validate_activation_prompts(
            self.csv_path, self.skills_dir
        )

    def assertNoErrors(self, errors: list[str]) -> None:
        self.assertEqual(errors, [], f"expected no errors, got: {errors}")

    def assertErrorMentions(self, errors: list[str], *fragments: str) -> None:
        self.assertTrue(errors, "expected at least one error, got none")
        joined = "\n".join(errors)
        for fragment in fragments:
            self.assertIn(fragment, joined)


class ValidSpecificationTests(EvalFixtureTestCase):
    def test_minimal_valid_csv_passes(self):
        self.add_skill("dsa-tutor")
        self.write_csv(BASE_ROWS, header=HEADER)
        self.assertNoErrors(self.validate())

    def test_every_skill_with_both_polarities_passes(self):
        self.add_skill("dsa-tutor")
        self.add_skill("debug-coach")
        rows = BASE_ROWS + [
            ["A003", "debug-coach", "true", "My loop returns 4, expected 5.", "Concrete observed failure."],
            ["A004", "debug-coach", "false", "What is a hash map?", "Generic concept question."],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertNoErrors(self.validate())

    def test_none_target_rows_are_accepted(self):
        self.add_skill("dsa-tutor")
        rows = BASE_ROWS + [
            ["A003", "none", "false", "What time is it in Tokyo?", "No skill here should engage."],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertNoErrors(self.validate())

    def test_quoted_fields_with_commas_are_parsed(self):
        self.add_skill("dsa-tutor")
        rows = [
            ["A001", "dsa-tutor", "true", "Walk me through it, slowly, step by step.", "Guided, incremental request."],
            BASE_ROWS[1],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertNoErrors(self.validate())


class FileAndHeaderTests(EvalFixtureTestCase):
    def test_missing_csv_fails(self):
        self.add_skill("dsa-tutor")
        self.assertErrorMentions(self.validate(), "does not exist")

    def test_empty_csv_fails(self):
        self.add_skill("dsa-tutor")
        self.csv_path.write_text("", encoding="utf-8")
        self.assertErrorMentions(self.validate(), "file is empty")

    def test_missing_required_column_fails(self):
        self.add_skill("dsa-tutor")
        short_header = [c for c in HEADER if c != "reason"]
        self.write_csv([row[:-1] for row in BASE_ROWS], header=short_header)
        self.assertErrorMentions(self.validate(), "unexpected header")

    def test_reordered_columns_fail(self):
        self.add_skill("dsa-tutor")
        self.write_csv(BASE_ROWS, header=["target_skill", "id", "should_activate", "prompt", "reason"])
        self.assertErrorMentions(self.validate(), "unexpected header")

    def test_renamed_column_fails(self):
        self.add_skill("dsa-tutor")
        self.write_csv(BASE_ROWS, header=["id", "skill", "should_activate", "prompt", "reason"])
        self.assertErrorMentions(self.validate(), "unexpected header")

    def test_missing_skills_directory_fails(self):
        self.write_csv(BASE_ROWS, header=HEADER)
        self.assertErrorMentions(self.validate(), "does not exist", "coverage")


class MalformedRowTests(EvalFixtureTestCase):
    def test_row_with_too_few_columns_fails_with_a_line_number(self):
        self.add_skill("dsa-tutor")
        self.write_csv(BASE_ROWS + [["A003", "dsa-tutor", "true"]], header=HEADER)
        self.assertErrorMentions(self.validate(), "line 4", "3 column(s)")

    def test_row_with_too_many_columns_fails(self):
        self.add_skill("dsa-tutor")
        self.write_csv(BASE_ROWS + [["A003", "dsa-tutor", "true", "p", "r", "extra"]], header=HEADER)
        self.assertErrorMentions(self.validate(), "6 column(s)")

    def test_malformed_row_does_not_mask_later_rows(self):
        """A short row is reported, and validation still reaches row 4."""
        self.add_skill("dsa-tutor")
        rows = BASE_ROWS + [
            ["A003", "dsa-tutor"],
            ["A004", "made-up-skill", "true", "prompt", "reason"],
        ]
        self.write_csv(rows, header=HEADER)
        errors = self.validate()
        self.assertErrorMentions(errors, "line 4", "line 5", "made-up-skill")


class IdentifierTests(EvalFixtureTestCase):
    def test_duplicate_id_fails_and_names_both_lines(self):
        self.add_skill("dsa-tutor")
        rows = BASE_ROWS + [
            ["A001", "dsa-tutor", "true", "Another prompt.", "Another reason."],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertErrorMentions(
            self.validate(), "duplicate id 'A001'", "line 4", "first used at line 2"
        )

    def test_empty_id_fails(self):
        self.add_skill("dsa-tutor")
        rows = BASE_ROWS + [
            ["", "dsa-tutor", "true", "Prompt without an id.", "Reason."],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertErrorMentions(self.validate(), "line 4", "empty id")

    def test_whitespace_only_id_fails(self):
        self.add_skill("dsa-tutor")
        rows = BASE_ROWS + [
            ["   ", "dsa-tutor", "true", "Prompt with a blank id.", "Reason."],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertErrorMentions(self.validate(), "empty id")

    def test_non_contiguous_ids_are_allowed(self):
        """Continuity was never enforced in CI and is not enforced here."""
        self.add_skill("dsa-tutor")
        rows = [
            ["A001", *BASE_ROWS[0][1:]],
            ["A999", *BASE_ROWS[1][1:]],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertNoErrors(self.validate())


class FieldValueTests(EvalFixtureTestCase):
    def test_unknown_target_skill_fails(self):
        self.add_skill("dsa-tutor")
        rows = BASE_ROWS + [
            ["A003", "typo-coach", "true", "Prompt.", "Reason."],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertErrorMentions(self.validate(), "'typo-coach'", "not a skill directory")

    def test_directory_without_skill_md_is_not_a_valid_target(self):
        self.add_skill("dsa-tutor")
        self.add_skill("draft-coach", with_skill_md=False)
        rows = BASE_ROWS + [
            ["A003", "draft-coach", "true", "Prompt.", "Reason."],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertErrorMentions(self.validate(), "'draft-coach'")

    def test_invalid_should_activate_value_fails(self):
        self.add_skill("dsa-tutor")
        rows = BASE_ROWS + [
            ["A003", "dsa-tutor", "TRUE", "Prompt.", "Reason."],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertErrorMentions(self.validate(), "invalid should_activate", "'TRUE'")

    def test_empty_should_activate_fails(self):
        self.add_skill("dsa-tutor")
        rows = BASE_ROWS + [
            ["A003", "dsa-tutor", "", "Prompt.", "Reason."],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertErrorMentions(self.validate(), "invalid should_activate")

    def test_empty_prompt_fails(self):
        self.add_skill("dsa-tutor")
        rows = BASE_ROWS + [
            ["A003", "dsa-tutor", "true", "   ", "Reason."],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertErrorMentions(self.validate(), "line 4", "empty prompt")

    def test_empty_reason_fails(self):
        self.add_skill("dsa-tutor")
        rows = BASE_ROWS + [
            ["A003", "dsa-tutor", "true", "Prompt.", ""],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertErrorMentions(self.validate(), "line 4", "empty reason")


class CoverageTests(EvalFixtureTestCase):
    def test_skill_without_a_positive_row_fails(self):
        self.add_skill("dsa-tutor")
        self.write_csv([BASE_ROWS[1]], header=HEADER)
        self.assertErrorMentions(
            self.validate(), "'dsa-tutor'", "no positive activation case"
        )

    def test_skill_without_a_negative_row_fails(self):
        self.add_skill("dsa-tutor")
        self.write_csv([BASE_ROWS[0]], header=HEADER)
        self.assertErrorMentions(
            self.validate(), "'dsa-tutor'", "no negative activation case"
        )

    def test_skill_with_no_rows_at_all_fails_both_ways(self):
        self.add_skill("dsa-tutor")
        self.add_skill("debug-coach")
        self.write_csv(BASE_ROWS, header=HEADER)
        errors = self.validate()
        self.assertErrorMentions(
            errors, "'debug-coach'", "no positive activation case", "no negative activation case"
        )
        self.assertEqual(len(errors), 2, f"expected exactly two coverage errors: {errors}")

    def test_none_rows_do_not_count_toward_coverage(self):
        self.add_skill("dsa-tutor")
        rows = [
            BASE_ROWS[0],
            ["A002", "none", "false", "Unrelated question.", "No skill should engage."],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertErrorMentions(self.validate(), "no negative activation case")

    def test_invalid_polarity_does_not_satisfy_coverage(self):
        """A row with a bad should_activate value can't fill a coverage gap."""
        self.add_skill("dsa-tutor")
        rows = [
            BASE_ROWS[0],
            ["A002", "dsa-tutor", "False", "Prompt.", "Reason."],
        ]
        self.write_csv(rows, header=HEADER)
        self.assertErrorMentions(
            self.validate(), "invalid should_activate", "no negative activation case"
        )


class EntryPointTests(EvalFixtureTestCase):
    """Exercise the repo-level wiring and `main()`, quietly."""

    def setUp(self) -> None:
        super().setUp()
        quiet = contextlib.ExitStack()
        quiet.enter_context(contextlib.redirect_stdout(io.StringIO()))
        quiet.enter_context(contextlib.redirect_stderr(io.StringIO()))
        self.addCleanup(quiet.close)

    def test_validate_evals_resolves_the_conventional_paths(self):
        self.add_skill("dsa-tutor")
        self.write_csv(BASE_ROWS, header=HEADER)
        self.assertNoErrors(validate_evals.validate_evals(self.repo_root))

    def test_main_returns_zero_for_a_valid_repository(self):
        self.add_skill("dsa-tutor")
        self.write_csv(BASE_ROWS, header=HEADER)
        self.assertEqual(
            validate_evals.main(["--root", str(self.repo_root)]), 0
        )

    def test_main_returns_one_for_an_invalid_repository(self):
        self.add_skill("dsa-tutor")
        self.write_csv([BASE_ROWS[0]], header=HEADER)
        self.assertEqual(
            validate_evals.main(["--root", str(self.repo_root)]), 1
        )

    def test_main_reports_every_problem_not_just_the_first(self):
        self.add_skill("dsa-tutor")
        rows = [
            ["A001", "dsa-tutor", "maybe", "", "Reason."],
        ]
        self.write_csv(rows, header=HEADER)
        errors = validate_evals.validate_evals(self.repo_root)
        self.assertGreaterEqual(len(errors), 3, f"expected several errors: {errors}")


class RealRepositoryTests(unittest.TestCase):
    """Read-only smoke test: the committed specification must validate."""

    def test_repository_activation_prompts_validate(self):
        self.assertNoErrorsIn(validate_evals.validate_evals(REPO_ROOT))

    def assertNoErrorsIn(self, errors: list[str]) -> None:
        self.assertEqual(
            errors, [], f"evals/activation-prompts.csv does not validate: {errors}"
        )


if __name__ == "__main__":
    unittest.main()
