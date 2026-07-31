"""Tests for `scripts/validate_finder.py`.

The Find Your Coach page is only trustworthy if its route data is:
every path ends somewhere real, no option quietly points at a skill
that was renamed, no dead end pretends to be a recommendation, and
every branch has a routing case behind it. These tests protect those
guarantees, including the failure paths a contributor would otherwise
discover by shipping a broken wizard.

Fixtures are generated into a temporary directory. The one test that
touches the real repository only reads it.
"""

from __future__ import annotations

import contextlib
import copy
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_finder  # noqa: E402  (path set up above)


CASE_HEADER = validate_finder.EXPECTED_CASE_HEADER


def base_routes() -> dict:
    """A small but structurally complete routing tree.

    Two skills, two questions (one nested), and the two honest no-match
    outcomes the real data also carries.
    """
    return {
        "schema_version": 1,
        "skills_base": "../skills",
        "start": "q_start",
        "questions": [
            {
                "id": "q_start",
                "text": "What are you working with?",
                "options": [
                    {"id": "o_go_dsa", "label": "A DSA problem", "next": "q_dsa"},
                    {
                        "id": "o_go_debug",
                        "label": "Failing code",
                        "next": "r_debug_coach",
                    },
                    {
                        "id": "o_go_nowhere",
                        "label": "None of these",
                        "next": "r_no_match_one",
                    },
                    {
                        "id": "o_go_delivery",
                        "label": "Write it for me",
                        "next": "r_no_match_two",
                    },
                ],
            },
            {
                "id": "q_dsa",
                "text": "Where are you right now?",
                "options": [
                    {
                        "id": "o_dsa_tutor",
                        "label": "I need an approach",
                        "next": "r_dsa_tutor",
                    },
                    {
                        "id": "o_dsa_debug",
                        "label": "My code fails",
                        "next": "r_debug_coach",
                    },
                ],
            },
        ],
        "results": [
            {
                "id": "r_dsa_tutor",
                "type": "skill",
                "skill": "dsa-tutor",
                "reason": "Guided end-to-end problem solving is what is missing.",
                "starter_prompt": "Ask me one question at a time.",
                "handoff": {"skill": "debug-coach", "note": "once code fails."},
            },
            {
                "id": "r_debug_coach",
                "type": "skill",
                "skill": "debug-coach",
                "reason": "A concrete failure has been observed.",
                "starter_prompt": "Help me isolate the bug without rewriting it.",
            },
            {
                "id": "r_no_match_one",
                "type": "no_match",
                "headline": "No coaching mode fits this",
                "reason": "The work is not something this suite coaches.",
                "explanation": "Think Before Code provides coaching modes only.",
            },
            {
                "id": "r_no_match_two",
                "type": "no_match",
                "headline": "No coaching mode fits this",
                "reason": "A finished rewrite is wanted, not review judgment.",
                "explanation": "Think Before Code does not deliver rewrites.",
                "closest_skill": {
                    "skill": "debug-coach",
                    "note": "if a concrete failure shows up instead.",
                },
            },
        ],
    }


BASE_CASES = [
    ["C001", "o_go_dsa>o_dsa_tutor", "r_dsa_tutor", "Approach missing."],
    ["C002", "o_go_dsa>o_dsa_debug", "r_debug_coach", "Observed failure."],
    ["C003", "o_go_debug", "r_debug_coach", "Straight to debugging."],
    ["C004", "o_go_nowhere", "r_no_match_one", "Honest dead end."],
    ["C005", "o_go_delivery", "r_no_match_two", "Delivery is out of scope."],
]


class FinderFixtureTestCase(unittest.TestCase):
    """Base case providing a throwaway repository root."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo_root = Path(self._tmp.name)
        self.skills_dir = self.repo_root / "skills"
        self.finder_dir = self.repo_root / "find-your-coach"
        self.finder_dir.mkdir()
        self.evals_dir = self.repo_root / "evals"
        self.evals_dir.mkdir()
        self.routes_path = self.finder_dir / "routes.json"
        self.cases_path = self.evals_dir / "finder-cases.csv"

        self.add_skill("dsa-tutor")
        self.add_skill("debug-coach")
        self.write_assets()

    # -- fixture helpers ------------------------------------------------

    def add_skill(self, name: str, *, with_skill_md: bool = True) -> Path:
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        if with_skill_md:
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: Coaches.\n---\n",
                encoding="utf-8",
            )
        return skill_dir

    def write_assets(self) -> None:
        """Write the static files the page is served from."""
        for asset in validate_finder.FINDER_ASSETS:
            if asset == "routes.json":
                continue
            (self.finder_dir / asset).write_text("", encoding="utf-8")

    def write_routes(self, data: dict | str) -> None:
        text = data if isinstance(data, str) else json.dumps(data, indent=2)
        self.routes_path.write_text(text + "\n", encoding="utf-8")

    def write_cases(
        self,
        rows: list[list[str]] | None = None,
        *,
        header: list[str] | None = CASE_HEADER,
    ) -> None:
        rows = BASE_CASES if rows is None else rows
        with self.cases_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if header is not None:
                writer.writerow(header)
            writer.writerows(rows)

    def write_valid_fixture(self) -> dict:
        data = base_routes()
        self.write_routes(data)
        self.write_cases()
        return data

    # -- entry points under test ---------------------------------------

    def validate_routes(self) -> list[str]:
        _, errors = validate_finder.validate_routes(
            self.routes_path, self.skills_dir
        )
        return errors

    def validate_all(self) -> list[str]:
        return validate_finder.validate_finder(self.repo_root)

    # -- assertions -----------------------------------------------------

    def assertNoErrors(self, errors: list[str]) -> None:
        self.assertEqual(errors, [], f"expected no errors, got: {errors}")

    def assertErrorMentions(self, errors: list[str], *fragments: str) -> None:
        self.assertTrue(errors, "expected at least one error, got none")
        joined = "\n".join(errors)
        for fragment in fragments:
            self.assertIn(fragment, joined)


class ValidRouteDataTests(FinderFixtureTestCase):
    def test_minimal_valid_fixture_passes(self):
        self.write_valid_fixture()
        self.assertNoErrors(self.validate_all())

    def test_optional_handoff_and_closest_skill_are_accepted(self):
        data = base_routes()
        self.write_routes(data)
        self.write_cases()
        errors = self.validate_routes()
        self.assertNoErrors(errors)

    def test_results_without_a_handoff_are_accepted(self):
        data = base_routes()
        del data["results"][0]["handoff"]
        self.write_routes(data)
        self.write_cases()
        self.assertNoErrors(self.validate_all())

    def test_absent_skills_base_falls_back_to_the_default(self):
        data = base_routes()
        del data["skills_base"]
        self.write_routes(data)
        self.write_cases()
        self.assertNoErrors(self.validate_all())


class FileAndShapeTests(FinderFixtureTestCase):
    def test_missing_routes_file_fails(self):
        self.write_cases()
        self.assertErrorMentions(self.validate_all(), "does not exist")

    def test_invalid_json_fails(self):
        self.write_routes("{ not json")
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "not valid JSON")

    def test_top_level_array_fails(self):
        self.write_routes("[]")
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "must be a JSON object")

    def test_missing_start_key_fails(self):
        data = base_routes()
        del data["start"]
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "missing required", "'start'")

    def test_questions_must_be_a_list(self):
        data = base_routes()
        data["questions"] = {"q_start": {}}
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "'questions' must be a list")

    def test_empty_results_list_fails(self):
        data = base_routes()
        data["results"] = []
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "'results' is empty")

    def test_missing_static_asset_fails(self):
        self.write_valid_fixture()
        (self.finder_dir / "styles.css").unlink()
        self.assertErrorMentions(self.validate_all(), "missing finder asset")


class IdentifierTests(FinderFixtureTestCase):
    def test_duplicate_question_id_fails(self):
        data = base_routes()
        data["questions"].append(copy.deepcopy(data["questions"][1]))
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "duplicate question id", "q_dsa")

    def test_duplicate_result_id_fails(self):
        data = base_routes()
        data["results"].append(copy.deepcopy(data["results"][0]))
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "duplicate result id")

    def test_id_shared_by_question_and_result_fails(self):
        data = base_routes()
        data["results"][0]["id"] = "q_dsa"
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(
            self.validate_routes(), "is used by both a question and a result"
        )

    def test_duplicate_option_id_across_questions_fails(self):
        data = base_routes()
        data["questions"][1]["options"][0]["id"] = "o_go_debug"
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "duplicate option id")

    def test_empty_option_id_fails(self):
        data = base_routes()
        data["questions"][0]["options"][0]["id"] = "  "
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "missing or empty id")

    def test_empty_option_label_fails(self):
        data = base_routes()
        data["questions"][0]["options"][0]["label"] = ""
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "missing or empty label")

    def test_empty_question_text_fails(self):
        data = base_routes()
        data["questions"][0]["text"] = "   "
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "missing or empty text")


class OptionCountTests(FinderFixtureTestCase):
    def test_single_option_question_fails(self):
        data = base_routes()
        data["questions"][1]["options"] = data["questions"][1]["options"][:1]
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "1 option(s)", "expected between")

    def test_too_many_options_fail(self):
        data = base_routes()
        extra = [
            {"id": f"o_extra_{index}", "label": f"Extra {index}", "next": "r_debug_coach"}
            for index in range(4)
        ]
        data["questions"][0]["options"].extend(extra)
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "8 option(s)")


class EdgeAndTraversalTests(FinderFixtureTestCase):
    def test_option_pointing_at_an_unknown_node_fails(self):
        data = base_routes()
        data["questions"][0]["options"][1]["next"] = "r_typo_coach"
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(
            self.validate_routes(), "r_typo_coach", "neither a question nor a result"
        )

    def test_start_naming_a_result_fails(self):
        data = base_routes()
        data["start"] = "r_dsa_tutor"
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "which is not a question")

    def test_cycle_is_rejected(self):
        data = base_routes()
        data["questions"][1]["options"][0]["next"] = "q_start"
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "routing cycle detected")

    def test_unreachable_question_is_reported(self):
        data = base_routes()
        data["questions"].append(
            {
                "id": "q_orphan",
                "text": "Nobody can get here.",
                "options": [
                    {"id": "o_orphan_a", "label": "A", "next": "r_debug_coach"},
                    {"id": "o_orphan_b", "label": "B", "next": "r_dsa_tutor"},
                ],
            }
        )
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "q_orphan", "unreachable")

    def test_unreachable_result_is_reported(self):
        data = base_routes()
        data["results"].append(
            {
                "id": "r_orphan",
                "type": "no_match",
                "reason": "Nobody can get here.",
                "explanation": "Unreachable by construction.",
            }
        )
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "r_orphan", "unreachable")

    def test_question_with_no_options_cannot_reach_a_result(self):
        data = base_routes()
        data["questions"][1]["options"] = []
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "can never reach a result")


class SkillResultTests(FinderFixtureTestCase):
    def test_result_naming_a_nonexistent_skill_fails(self):
        data = base_routes()
        data["results"][0]["skill"] = "typo-coach"
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "typo-coach", "not a directory")

    def test_directory_without_skill_md_is_not_a_skill(self):
        self.add_skill("draft-coach", with_skill_md=False)
        data = base_routes()
        data["results"][0]["skill"] = "draft-coach"
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "draft-coach")

    def test_missing_starter_prompt_fails(self):
        data = base_routes()
        del data["results"][1]["starter_prompt"]
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(
            self.validate_routes(), "r_debug_coach", "starter_prompt"
        )

    def test_empty_reason_fails(self):
        data = base_routes()
        data["results"][1]["reason"] = "   "
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "r_debug_coach", "reason")

    def test_skill_missing_from_every_result_fails(self):
        self.add_skill("complexity-coach")
        self.write_valid_fixture()
        self.assertErrorMentions(
            self.validate_routes(),
            "complexity-coach",
            "never reachable as a primary finder result",
        )

    def test_handoff_naming_a_fake_skill_fails(self):
        data = base_routes()
        data["results"][0]["handoff"]["skill"] = "ghost-coach"
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(
            self.validate_routes(), "handoff", "ghost-coach", "not a real skill"
        )

    def test_skill_link_that_would_not_resolve_fails(self):
        data = base_routes()
        data["skills_base"] = "../not-here"
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "does not resolve")

    def test_unknown_result_type_fails(self):
        data = base_routes()
        data["results"][0]["type"] = "recommendation"
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "'recommendation'", "expected one of")


class NoMatchResultTests(FinderFixtureTestCase):
    def test_fewer_than_two_no_match_results_fails(self):
        data = base_routes()
        data["results"][3] = {
            "id": "r_no_match_two",
            "type": "skill",
            "skill": "debug-coach",
            "reason": "Reused as a skill result.",
            "starter_prompt": "Prompt.",
        }
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(
            self.validate_routes(), "result(s) of type 'no_match'", "at least"
        )

    def test_no_match_result_carrying_a_skill_fails(self):
        data = base_routes()
        data["results"][2]["skill"] = "dsa-tutor"
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(
            self.validate_routes(),
            "r_no_match_one",
            "must not present itself as a skill recommendation",
        )

    def test_no_match_result_carrying_a_starter_prompt_fails(self):
        data = base_routes()
        data["results"][2]["starter_prompt"] = "Write the whole thing for me."
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(self.validate_routes(), "starter_prompt")

    def test_no_match_result_without_an_explanation_fails(self):
        data = base_routes()
        data["results"][2]["explanation"] = ""
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(
            self.validate_routes(), "r_no_match_one", "empty explanation"
        )

    def test_closest_skill_naming_a_fake_skill_fails(self):
        data = base_routes()
        data["results"][3]["closest_skill"]["skill"] = "ghost-coach"
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(
            self.validate_routes(), "closest_skill", "not a real skill"
        )


class FinderCaseTests(FinderFixtureTestCase):
    def test_valid_cases_pass(self):
        self.write_valid_fixture()
        self.assertNoErrors(self.validate_all())

    def test_missing_cases_file_fails(self):
        self.write_routes(base_routes())
        self.assertErrorMentions(self.validate_all(), "finder-cases.csv", "does not exist")

    def test_unexpected_header_fails(self):
        self.write_routes(base_routes())
        self.write_cases(header=["id", "route", "expected_result", "reason"])
        self.assertErrorMentions(self.validate_all(), "unexpected header")

    def test_wrong_column_count_fails(self):
        self.write_routes(base_routes())
        self.write_cases(BASE_CASES + [["C006", "o_go_debug", "r_debug_coach"]])
        self.assertErrorMentions(self.validate_all(), "3 column(s)")

    def test_duplicate_case_id_fails(self):
        self.write_routes(base_routes())
        self.write_cases(BASE_CASES + [["C001", "o_go_debug", "r_debug_coach", "Dup."]])
        self.assertErrorMentions(self.validate_all(), "duplicate id 'C001'")

    def test_empty_reason_fails(self):
        self.write_routes(base_routes())
        self.write_cases(BASE_CASES + [["C006", "o_go_debug", "r_debug_coach", "  "]])
        self.assertErrorMentions(self.validate_all(), "empty reason")

    def test_empty_path_fails(self):
        self.write_routes(base_routes())
        self.write_cases(BASE_CASES + [["C006", "", "r_debug_coach", "No path."]])
        self.assertErrorMentions(self.validate_all(), "empty path")

    def test_unknown_option_in_path_fails(self):
        self.write_routes(base_routes())
        self.write_cases(
            BASE_CASES + [["C006", "o_go_dsa>o_ghost", "r_dsa_tutor", "Typo."]]
        )
        self.assertErrorMentions(self.validate_all(), "o_ghost", "is not an option")

    def test_path_stopping_on_a_question_fails(self):
        self.write_routes(base_routes())
        self.write_cases(BASE_CASES + [["C006", "o_go_dsa", "r_dsa_tutor", "Too short."]])
        self.assertErrorMentions(self.validate_all(), "stops on question 'q_dsa'")

    def test_path_continuing_past_a_result_fails(self):
        self.write_routes(base_routes())
        self.write_cases(
            BASE_CASES
            + [["C006", "o_go_debug>o_dsa_tutor", "r_dsa_tutor", "Too long."]]
        )
        self.assertErrorMentions(self.validate_all(), "already reached result")

    def test_path_reaching_the_wrong_result_fails(self):
        self.write_routes(base_routes())
        cases = copy.deepcopy(BASE_CASES)
        cases[0][2] = "r_debug_coach"
        self.write_cases(cases)
        self.assertErrorMentions(
            self.validate_all(), "path reaches 'r_dsa_tutor'", "expected_result is"
        )

    def test_expected_result_that_does_not_exist_fails(self):
        self.write_routes(base_routes())
        cases = copy.deepcopy(BASE_CASES)
        cases[0][2] = "r_imaginary"
        self.write_cases(cases)
        self.assertErrorMentions(self.validate_all(), "r_imaginary", "does not exist")

    def test_uncovered_result_fails(self):
        self.write_routes(base_routes())
        self.write_cases(BASE_CASES[:-1])
        self.assertErrorMentions(
            self.validate_all(), "r_no_match_two", "no routing case reaching it"
        )

    def test_uncovered_option_fails(self):
        data = base_routes()
        data["questions"][1]["options"].append(
            {"id": "o_dsa_new", "label": "Something new", "next": "r_debug_coach"}
        )
        self.write_routes(data)
        self.write_cases()
        self.assertErrorMentions(
            self.validate_all(), "o_dsa_new", "not exercised by any routing case"
        )

    def test_every_problem_is_reported_not_just_the_first(self):
        self.write_routes(base_routes())
        self.write_cases(
            [
                ["", "o_go_dsa>o_ghost", "r_imaginary", ""],
            ]
        )
        errors = self.validate_all()
        self.assertGreaterEqual(len(errors), 4, f"expected several errors: {errors}")


class EntryPointTests(FinderFixtureTestCase):
    """Exercise the repo-level wiring and `main()`, quietly."""

    def setUp(self) -> None:
        super().setUp()
        quiet = contextlib.ExitStack()
        quiet.enter_context(contextlib.redirect_stdout(io.StringIO()))
        quiet.enter_context(contextlib.redirect_stderr(io.StringIO()))
        self.addCleanup(quiet.close)

    def test_main_returns_zero_for_a_valid_repository(self):
        self.write_valid_fixture()
        self.assertEqual(
            validate_finder.main(["--root", str(self.repo_root)]), 0
        )

    def test_main_returns_one_for_an_invalid_repository(self):
        data = base_routes()
        data["questions"][0]["options"][0]["next"] = "r_missing"
        self.write_routes(data)
        self.write_cases()
        self.assertEqual(
            validate_finder.main(["--root", str(self.repo_root)]), 1
        )

    def test_count_cases_counts_records_without_the_header(self):
        self.write_valid_fixture()
        self.assertEqual(
            validate_finder.count_cases(self.cases_path), len(BASE_CASES)
        )


class RealRepositoryTests(unittest.TestCase):
    """Read-only smoke test: the committed finder data must validate."""

    def test_repository_finder_data_validates(self):
        errors = validate_finder.validate_finder(REPO_ROOT)
        self.assertEqual(
            errors, [], f"the committed finder data does not validate: {errors}"
        )

    def test_every_repository_skill_is_reachable_as_a_result(self):
        data, _ = validate_finder.load_routes(
            REPO_ROOT / validate_finder.ROUTES_RELPATH
        )
        self.assertIsNotNone(data)
        recommended = {
            result.get("skill")
            for result in data["results"]
            if result.get("type") == validate_finder.RESULT_TYPE_SKILL
        }
        self.assertEqual(
            recommended,
            validate_finder.discover_skills(
                REPO_ROOT / validate_finder.SKILLS_RELPATH
            ),
        )


if __name__ == "__main__":
    unittest.main()
