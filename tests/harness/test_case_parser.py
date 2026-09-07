"""Tests for `evals/harness/case_parser.py`.

These protect the parser's ability to turn `evals/behavior-cases.md`'s
Markdown shape into structured cases without silently mis-parsing it —
including the real quirks found in that file (a wrapped parenthetical
annotation on a field label, `specification-coach` cases nested under
the `concept-coach` heading, and the paired `Input A`/`Input B` shape
used by several cross-skill regression cases).

Fixtures are synthetic Markdown strings written to a temporary
directory. One test parses the real `evals/behavior-cases.md` to catch
drift between this parser and the file it's meant to read, but only
checks structural properties (case count, no duplicate ids, every case
has required fields) rather than hard-coding the current case count,
so it doesn't need updating every time a case is added.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "evals" / "harness"))

import case_parser  # noqa: E402  (path set up above)


MINIMAL_VALID_FILE = """\
# Behavior Cases

---

## `dsa-tutor`

### Case DT-1 — At most one question per turn

**Input:** "Solve Two Sum for me."

**Relevant learner state:** No prior approach offered.

**Expected behavior:**
- A single response with at most one question.
- The question targets the earliest missing piece.

**Forbidden behavior:**
- Naming the pattern immediately.
- Providing any code.

**Success criteria:** The response is short and asks one question.

---

## `problem-decoder`

### Case PD-1 — Never names an approach

**Input:** A pasted problem statement.

**Expected behavior:**
- Ask for input and output first.

**Forbidden behavior:**
- Naming a pattern.

**Success criteria:** No pattern is named.

---
"""


class ParseBehaviorCasesTestCase(unittest.TestCase):
    """Base case providing a throwaway file to parse."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)

    def write_and_parse(self, text: str) -> list[case_parser.BehaviorCase]:
        path = self.tmp_path / "behavior-cases.md"
        path.write_text(text, encoding="utf-8")
        return case_parser.parse_behavior_cases(path)


class BasicParsingTests(ParseBehaviorCasesTestCase):
    def test_parses_expected_case_count(self) -> None:
        cases = self.write_and_parse(MINIMAL_VALID_FILE)
        self.assertEqual(len(cases), 2)

    def test_case_fields_are_captured(self) -> None:
        cases = self.write_and_parse(MINIMAL_VALID_FILE)
        dt1 = next(c for c in cases if c.case_id == "DT-1")
        self.assertEqual(dt1.skill, "dsa-tutor")
        self.assertEqual(dt1.title, "At most one question per turn")
        self.assertIn("Two Sum", dt1.input_text)
        self.assertEqual(dt1.relevant_learner_state, "No prior approach offered.")
        self.assertEqual(
            dt1.expected_behavior,
            [
                "A single response with at most one question.",
                "The question targets the earliest missing piece.",
            ],
        )
        self.assertEqual(
            dt1.forbidden_behavior,
            ["Naming the pattern immediately.", "Providing any code."],
        )
        self.assertEqual(dt1.success_criteria, "The response is short and asks one question.")

    def test_relevant_learner_state_is_optional(self) -> None:
        cases = self.write_and_parse(MINIMAL_VALID_FILE)
        pd1 = next(c for c in cases if c.case_id == "PD-1")
        self.assertIsNone(pd1.relevant_learner_state)

    def test_missing_file_raises(self) -> None:
        missing_path = self.tmp_path / "does-not-exist.md"
        with self.assertRaises(case_parser.BehaviorCaseParseError):
            case_parser.parse_behavior_cases(missing_path)

    def test_empty_file_raises(self) -> None:
        with self.assertRaises(case_parser.BehaviorCaseParseError):
            self.write_and_parse("# Behavior Cases\n\nNo cases here.\n")

    def test_case_before_any_skill_heading_raises(self) -> None:
        broken = '### Case DT-1 — Orphan case\n\n**Input:** x\n\n**Expected behavior:**\n- a\n\n**Forbidden behavior:**\n- b\n\n**Success criteria:** c\n'
        with self.assertRaises(case_parser.BehaviorCaseParseError):
            self.write_and_parse(broken)

    def test_case_missing_required_field_raises(self) -> None:
        broken = MINIMAL_VALID_FILE.replace(
            "**Success criteria:** The response is short and asks one question.\n", ""
        )
        with self.assertRaises(case_parser.BehaviorCaseParseError):
            self.write_and_parse(broken)

    def test_duplicate_case_id_raises(self) -> None:
        duplicated = MINIMAL_VALID_FILE + "\n## `dry-run-coach`\n\n### Case DT-1 — Duplicate id\n\n**Input:** y\n\n**Expected behavior:**\n- a\n\n**Forbidden behavior:**\n- b\n\n**Success criteria:** c\n\n---\n"
        with self.assertRaises(case_parser.BehaviorCaseParseError):
            self.write_and_parse(duplicated)


class ParentheticalAnnotationTests(ParseBehaviorCasesTestCase):
    """Covers the '**Input (mid-session):**'-style annotation, including
    the real file's case where the annotation wraps onto a second
    physical line before it closes."""

    def test_single_line_annotation_is_kept_as_context(self) -> None:
        text = """\
## `dsa-tutor`

### Case DT-3 — Genuine struggle

**Input (after several exchanges):** Learner is stuck.

**Expected behavior:**
- Reveal the next step.

**Forbidden behavior:**
- Reveal the full solution.

**Success criteria:** Forward progress happens.
"""
        cases = self.write_and_parse(text)
        self.assertEqual(len(cases), 1)
        self.assertIn("after several exchanges", cases[0].input_text)
        self.assertIn("Learner is stuck.", cases[0].input_text)

    def test_wrapped_annotation_across_two_lines_is_rejoined(self) -> None:
        text = """\
## `complexity-coach`

### Case XB-15 — No session-continuity behavior

**Input (mid-`complexity-coach`-session, derivation not yet
complete):** "Save where we are."

**Expected behavior:**
- Give an honest summary.

**Forbidden behavior:**
- Complete the derivation.

**Success criteria:** Nothing is resolved on the learner's behalf.
"""
        cases = self.write_and_parse(text)
        self.assertEqual(len(cases), 1)
        self.assertIn("derivation not yet complete", cases[0].input_text)
        self.assertIn("Save where we are.", cases[0].input_text)


class PairedInputTests(ParseBehaviorCasesTestCase):
    """Covers the 'Input A' / 'Input B' shape used by cross-skill
    regression cases like the real file's XB-16 through XB-20."""

    def test_paired_input_is_captured_and_flagged(self) -> None:
        text = """\
## `concept-coach`

### Case XB-16 — "sliding window" as concept vs. as a problem

**Input A:** "What makes a window a window?"
**Input B:** "Help me solve this sliding-window problem."

**Expected behavior:**
- Input A routes to concept-coach.
- Input B routes to dsa-tutor.

**Forbidden behavior:**
- Absorbing Input B into concept-coach.

**Success criteria:** The same term routes differently by task.
"""
        cases = self.write_and_parse(text)
        self.assertEqual(len(cases), 1)
        case = cases[0]
        self.assertTrue(case.is_paired_input)
        self.assertIn("Input A:", case.input_text)
        self.assertIn("Input B:", case.input_text)
        self.assertIn("window a window", case.input_text)
        self.assertIn("sliding-window problem", case.input_text)


class SkillResolutionTests(ParseBehaviorCasesTestCase):
    """Covers CASE_PREFIX_TO_SKILL taking priority over heading position,
    which is what the real file's SP-*/concept-coach nesting needs."""

    def test_prefix_resolves_skill_even_under_wrong_heading(self) -> None:
        # SP-* physically nested under a concept-coach heading, matching
        # the real file's documented drift.
        text = """\
## `concept-coach`

### Case SP-1 — A vague request produces one ambiguity

**Input:** "Add CSV export to the orders page."

**Expected behavior:**
- Ask about the highest-impact ambiguity.

**Forbidden behavior:**
- Producing a full specification up front.

**Success criteria:** One question about one ambiguity.
"""
        cases = self.write_and_parse(text)
        self.assertEqual(cases[0].skill, "specification-coach")

    def test_prefix_disagreeing_with_heading_in_an_unknown_way_raises(self) -> None:
        # DT-* (dsa-tutor) nested under problem-decoder's heading is not
        # the known specification-coach/concept-coach drift, so this
        # should raise rather than silently pick one.
        text = """\
## `problem-decoder`

### Case DT-1 — Misplaced case

**Input:** x

**Expected behavior:**
- a

**Forbidden behavior:**
- b

**Success criteria:** c
"""
        with self.assertRaises(case_parser.BehaviorCaseParseError):
            self.write_and_parse(text)

    def test_cross_skill_prefixes_resolve_to_none_regardless_of_heading(self) -> None:
        text = """\
## `dsa-tutor`

### Case XB-1 — Cross-skill case under a skill heading

**Input:** x

**Expected behavior:**
- a

**Forbidden behavior:**
- b

**Success criteria:** c
"""
        cases = self.write_and_parse(text)
        self.assertIsNone(cases[0].skill)

    def test_session_continuity_section_cases_have_no_skill(self) -> None:
        text = MINIMAL_VALID_FILE + """
## Session continuity

### Case SC-1 — Pause request produces a Resume Pack

**Input:** "Save where we are."

**Expected behavior:**
- A Resume Pack is generated.

**Forbidden behavior:**
- Declining to checkpoint.

**Success criteria:** A Resume Pack appears.
"""
        cases = self.write_and_parse(text)
        sc1 = next(c for c in cases if c.case_id == "SC-1")
        self.assertIsNone(sc1.skill)


class LoadCaseByIdTests(ParseBehaviorCasesTestCase):
    def test_load_case_by_id_finds_a_case(self) -> None:
        repo_root = self.tmp_path
        evals_dir = repo_root / "evals"
        evals_dir.mkdir()
        (evals_dir / "behavior-cases.md").write_text(MINIMAL_VALID_FILE, encoding="utf-8")
        case = case_parser.load_case_by_id(repo_root, "DT-1")
        self.assertEqual(case.case_id, "DT-1")

    def test_load_case_by_id_missing_case_raises(self) -> None:
        repo_root = self.tmp_path
        evals_dir = repo_root / "evals"
        evals_dir.mkdir()
        (evals_dir / "behavior-cases.md").write_text(MINIMAL_VALID_FILE, encoding="utf-8")
        with self.assertRaises(case_parser.BehaviorCaseParseError):
            case_parser.load_case_by_id(repo_root, "ZZ-999")


class RealRepositoryFileTests(unittest.TestCase):
    """Sanity-checks the parser against the real evals/behavior-cases.md.

    Deliberately avoids hard-coding today's case count or exact ids —
    that would make this test churn every time a case is added — and
    instead checks structural invariants that should always hold.
    """

    def test_real_behavior_cases_file_parses_without_error(self) -> None:
        real_path = REPO_ROOT / "evals" / "behavior-cases.md"
        if not real_path.is_file():
            self.skipTest("evals/behavior-cases.md not present in this checkout")
        cases = case_parser.parse_behavior_cases(real_path)
        self.assertGreater(len(cases), 0)

    def test_real_file_has_no_duplicate_case_ids(self) -> None:
        real_path = REPO_ROOT / "evals" / "behavior-cases.md"
        if not real_path.is_file():
            self.skipTest("evals/behavior-cases.md not present in this checkout")
        cases = case_parser.parse_behavior_cases(real_path)
        ids = [c.case_id for c in cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_real_file_every_case_has_required_fields(self) -> None:
        real_path = REPO_ROOT / "evals" / "behavior-cases.md"
        if not real_path.is_file():
            self.skipTest("evals/behavior-cases.md not present in this checkout")
        cases = case_parser.parse_behavior_cases(real_path)
        for case in cases:
            self.assertTrue(case.input_text, msg=f"{case.case_id} has empty input_text")
            self.assertTrue(case.expected_behavior, msg=f"{case.case_id} has no expected_behavior")
            self.assertTrue(case.forbidden_behavior, msg=f"{case.case_id} has no forbidden_behavior")
            self.assertTrue(case.success_criteria, msg=f"{case.case_id} has empty success_criteria")


if __name__ == "__main__":
    unittest.main()
