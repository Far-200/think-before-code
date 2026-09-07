#!/usr/bin/env python3
r"""Parser for `evals/behavior-cases.md`.

This module reads the repository's existing behavior-case
specification and turns it into structured `BehaviorCase` objects the
evaluation runner can execute. It does not introduce a competing
source of truth: `behavior-cases.md` remains the human-readable
specification, and this parser is a strict, fail-loud reading of that
same file. If the Markdown structure changes in a way this parser
doesn't understand, it raises rather than silently returning a
partial or wrong case.

## Structure this parser understands

```
## `skill-name`

### Case ID — Title

**Input:** ...

**Relevant learner state:** ...   (optional)

**Expected behavior:**
- ...
- ...

**Forbidden behavior:**
- ...

**Success criteria:** ...

---
```

- A `## \`skill-name\`` heading opens a section that normally
  determines each case's skill. In practice, the file's own structure
  has drifted: `specification-coach`'s cases (`SP-*`) and several
  cross-skill boundary cases (`XB-10`-`XB-20`) are nested under the
  `## \`concept-coach\`` heading rather than their own heading. This
  parser resolves the skill from the case id's *prefix* first (see
  `CASE_PREFIX_TO_SKILL`), falling back to heading position only for
  an unrecognized prefix, and raises if a recognized prefix disagrees
  with its heading in a way that isn't this known, accounted-for
  drift.
- `XB-*` and `SC-*` cases are genuinely cross-skill or skill-less by
  design (`## Cross-skill boundary cases` and `## Session continuity`
  are section headings, not skill headings) and parse with
  `skill=None`.
- A `### Case ID — Title` heading opens a case. `ID` is the token
  before the em dash; `Title` is everything after it.
- Recognized bold-prefixed fields: `Input`, `Relevant learner state`,
  `Expected behavior`, `Forbidden behavior`, `Success criteria`. Each
  runs until the next recognized field, the next `###`/`##` heading,
  or a line that is exactly `---`.
- A small number of cross-skill regression cases use a paired
  `**Input A:**` / `**Input B:**` shape instead of one `Input`, to
  show the same wording routing to two different skills. This parser
  recognizes that shape (joining both into `input_text` separated by
  a blank line, prefixed `Input A:` / `Input B:`) so parsing doesn't
  fail on them, but flags them via `is_paired_input=True`: they test
  *routing between* skills, not the in-session behavior of one already
  -activated skill, so the harness's runner (see `runner.py`) excludes
  them from case selection rather than trying to execute them as a
  single-skill conversation.
- `Expected behavior` and `Forbidden behavior` are Markdown bullet
  lists (`- ...`); this parser keeps each bullet as one list item.
  `Input`, `Relevant learner state`, and `Success criteria` are kept
  as a single joined text block (their wrapped lines are rejoined with
  spaces, matching how the file wraps prose across lines).

## What this parser deliberately does not do

It does not interpret the *content* of a case (it doesn't decide
whether a forbidden phrase appears in a model's reply — that's
`checks.py`). It does not validate that a case is well-formed
`behavior-cases.md` in the way `scripts/validate_skills.py` validates
`SKILL.md` frontmatter; a structurally-broken case is a hard parse
error here, not a collected error message, because the runner cannot
proceed at all without a correctly parsed case.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

BEHAVIOR_CASES_RELPATH = Path("evals") / "behavior-cases.md"

# The "Session continuity" section covers multiple skills at once
# (every skill with its own "Session continuity" SKILL.md section).
# Cases in that section don't inherit a skill from their `##` heading;
# the harness's case_config.json instead names the skill explicitly
# for each selected SC-* case, since a Resume Pack case is only
# meaningful once you know which skill's checkpoint format it targets.
SESSION_CONTINUITY_HEADING = "Session continuity"

# `behavior-cases.md` attributes most cases to a skill via the nearest
# preceding `## \`skill-name\`` heading, but two things break that
# assumption in the actual file:
#
# 1. `specification-coach`'s own behavior cases (`SP-*`) and several of
#    its cross-skill boundary cases (`XB-10` through `XB-20`) are
#    physically nested under the `## \`concept-coach\`` heading rather
#    than getting their own `## \`specification-coach\`` heading —
#    apparent documentation drift from how the file was extended over
#    several releases, not a deliberate structural choice.
# 2. `## Cross-skill boundary cases` and `## Session continuity` are
#    section headings that aren't skill headings at all, so cases under
#    them (`XB-*`, `SC-*`) don't belong to whichever skill happened to
#    be last, they're genuinely cross-skill or no-single-skill.
#
# Rather than silently mis-attributing cases to the nearest heading (or
# rewriting `behavior-cases.md` to fix its own drift, which is out of
# scope for a parser), this table is the authoritative source for which
# skill a case's *id prefix* belongs to. Heading-based attribution is
# still computed and cross-checked against this table: an unexpected
# mismatch raises loudly rather than being silently trusted either way,
# so a future edit that fixes the file's structure doesn't silently
# start disagreeing with this table without anyone noticing.
CASE_PREFIX_TO_SKILL = {
    "DT": "dsa-tutor",
    "PD": "problem-decoder",
    "DR": "dry-run-coach",
    "CC": "complexity-coach",
    "MI": "mock-interviewer",
    "DC": "debug-coach",
    "TC": "test-case-coach",
    "PT": "pattern-transfer-coach",
    "CR": "code-review-coach",
    "CN": "concept-coach",
    "SP": "specification-coach",
}
# Prefixes that are genuinely cross-skill or skill-less, not drift.
CROSS_SKILL_PREFIXES = {"XB", "SC"}

_SKILL_HEADING_RE = re.compile(r"^## `([a-z0-9-]+)`\s*$")
_SECTION_HEADING_RE = re.compile(r"^## (.+?)\s*$")
_CASE_HEADING_RE = re.compile(r"^### Case ([A-Za-z0-9-]+) \u2014 (.+?)\s*$")
# The label itself may carry a parenthetical annotation, e.g.
# "**Input (mid-session):**" or "**Input (after several exchanges):**".
# The annotation is kept as part of the field's text (prefixed back on)
# rather than discarded, since it's often load-bearing context (e.g.
# "mid-session, concept was 'async/await'").
_FIELD_RE = re.compile(
    r"^\*\*(Input|Relevant learner state|Expected behavior|"
    r"Forbidden behavior|Success criteria)(\s*\([^)]*\))?:\*\*\s?(.*)$"
)
_PAIRED_INPUT_RE = re.compile(r"^\*\*Input ([AB]):\*\*\s?(.*)$")
_BULLET_RE = re.compile(r"^-\s+(.+)$")


class BehaviorCaseParseError(ValueError):
    """Raised when `behavior-cases.md` doesn't match the expected shape."""


@dataclass
class BehaviorCase:
    """One parsed case from `evals/behavior-cases.md`."""

    case_id: str
    title: str
    skill: str | None  # None for a case in the Session continuity section
    input_text: str
    relevant_learner_state: str | None
    expected_behavior: list[str] = field(default_factory=list)
    forbidden_behavior: list[str] = field(default_factory=list)
    success_criteria: str = ""
    source_line: int = 0
    is_paired_input: bool = False


def _flush_field(
    current_field: str | None,
    buffer: list[str],
    case: dict,
) -> None:
    """Commit the buffered lines for `current_field` into `case`."""
    if current_field is None or not buffer:
        return
    if current_field in ("Input A", "Input B"):
        label = current_field[-1]
        text = " ".join(line.strip() for line in buffer if line.strip())
        case.setdefault("_paired_text", {})[label] = text
        return
    if current_field in ("Expected behavior", "Forbidden behavior"):
        bullets: list[str] = []
        for line in buffer:
            match = _BULLET_RE.match(line)
            if match:
                bullets.append(match.group(1).strip())
            elif bullets:
                # Continuation of a wrapped bullet line.
                bullets[-1] = f"{bullets[-1]} {line.strip()}"
        key = "expected_behavior" if current_field == "Expected behavior" else "forbidden_behavior"
        case[key] = [bullet.strip() for bullet in bullets]
    else:
        text = " ".join(line.strip() for line in buffer if line.strip())
        key = {
            "Input": "input_text",
            "Relevant learner state": "relevant_learner_state",
            "Success criteria": "success_criteria",
        }[current_field]
        case[key] = text


def _rejoin_wrapped_field_labels(lines: list[str]) -> list[str]:
    """Merge a field label's opening line forward when its parenthetical
    annotation wraps onto a following physical line before `):**` closes.

    `behavior-cases.md` wraps prose at a fixed column, and a handful of
    field labels carry a parenthetical annotation long enough to wrap,
    e.g.:

        **Input (mid-`complexity-coach`-session, derivation not yet
        complete):** "Save where we are, ..."

    This must be re-joined into one physical line before the field
    regexes run, since they operate line-by-line and don't span lines
    on their own. Only lines that look like the start of a bold field
    label with an unclosed parenthetical are merged; anything else
    (including ordinary wrapped prose inside a field's body, which the
    field-body collection loop already rejoins) is left untouched.
    """
    label_start_re = re.compile(r"^\*\*(?:Input|Relevant learner state)\s*\([^)]*$")
    merged: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if label_start_re.match(line):
            joined = line
            j = i + 1
            # Merge forward until the parenthetical actually closes with
            # "):**", or we run out of lines (malformed file — leave as
            # a parse error the caller will surface, don't loop forever).
            while j < len(lines) and "):**" not in joined:
                joined = f"{joined} {lines[j].strip()}"
                j += 1
            merged.append(joined)
            i = j
        else:
            merged.append(line)
            i += 1
    return merged


def _resolve_case_skill(
    path: Path, case_id: str, source_line: int, heading_skill: str | None
) -> str | None:
    """Resolve which skill a case belongs to, preferring the id-prefix
    table over heading position (see `CASE_PREFIX_TO_SKILL` for why).

    Raises `BehaviorCaseParseError` if a prefix-mapped case's heading
    attribution disagrees with the table in a way that isn't the known,
    documented drift (`specification-coach`/`concept-coach` nesting) —
    that would mean either this table or the file's structure changed
    in a way nobody reconciled, and a loud failure is safer than
    silently picking one.
    """
    prefix_match = re.match(r"^([A-Za-z]+)-\d+$", case_id)
    prefix = prefix_match.group(1) if prefix_match else None

    if prefix in CROSS_SKILL_PREFIXES:
        return None  # Cross-skill or skill-less by design; heading is irrelevant.

    if prefix in CASE_PREFIX_TO_SKILL:
        mapped_skill = CASE_PREFIX_TO_SKILL[prefix]
        known_drift = {
            ("specification-coach", "concept-coach"),
        }
        if (
            heading_skill is not None
            and heading_skill != mapped_skill
            and (mapped_skill, heading_skill) not in known_drift
        ):
            raise BehaviorCaseParseError(
                f"{path}: case {case_id} (line {source_line}) has prefix "
                f"'{prefix}' (expected skill '{mapped_skill}') but sits "
                f"under the '{heading_skill}' heading — this doesn't match "
                f"the known documentation drift this parser accounts for, "
                f"so the id-prefix table or the file's structure has "
                f"changed and needs reconciling"
            )
        return mapped_skill

    # Unrecognized prefix: fall back to heading attribution rather than
    # failing outright, since a future skill could add a new prefix that
    # this table simply hasn't been updated for yet.
    return heading_skill


def parse_behavior_cases(path: Path) -> list[BehaviorCase]:
    """Parse every case out of the behavior-cases Markdown file at `path`.

    Raises `BehaviorCaseParseError` if the file is missing, empty, or
    contains a case heading this parser cannot make sense of. Returns
    every case found, in file order, regardless of whether the caller
    plans to use all of them — case selection is the runner's job, not
    the parser's.
    """
    if not path.is_file():
        raise BehaviorCaseParseError(f"{path}: file does not exist")

    text = path.read_text(encoding="utf-8")
    lines = _rejoin_wrapped_field_labels(text.split("\n"))

    cases: list[BehaviorCase] = []
    current_skill: str | None = None
    in_session_continuity = False

    case_buffer: dict | None = None
    current_field: str | None = None
    field_buffer: list[str] = []

    def close_case(end_line: int) -> None:
        nonlocal case_buffer, current_field, field_buffer
        if case_buffer is None:
            return
        _flush_field(current_field, field_buffer, case_buffer)
        current_field = None
        field_buffer = []

        paired_text = case_buffer.get("_paired_text")
        if paired_text:
            parts = [
                f"Input {label}: {paired_text[label]}"
                for label in ("A", "B")
                if label in paired_text
            ]
            case_buffer["input_text"] = "\n\n".join(parts)

        missing = [
            key
            for key in ("input_text", "expected_behavior", "forbidden_behavior", "success_criteria")
            if not case_buffer.get(key)
        ]
        if missing:
            raise BehaviorCaseParseError(
                f"{path}: case {case_buffer['case_id']} (line "
                f"{case_buffer['source_line']}) is missing required "
                f"field(s): {', '.join(missing)}"
            )

        case_buffer["skill"] = _resolve_case_skill(
            path, case_buffer["case_id"], case_buffer["source_line"], case_buffer["skill"]
        )

        cases.append(
            BehaviorCase(
                case_id=case_buffer["case_id"],
                title=case_buffer["title"],
                skill=case_buffer["skill"],
                input_text=case_buffer["input_text"],
                relevant_learner_state=case_buffer.get("relevant_learner_state"),
                expected_behavior=case_buffer["expected_behavior"],
                forbidden_behavior=case_buffer["forbidden_behavior"],
                success_criteria=case_buffer["success_criteria"],
                source_line=case_buffer["source_line"],
                is_paired_input=case_buffer.get("is_paired_input", False),
            )
        )
        case_buffer = None

    for line_number, line in enumerate(lines, start=1):
        skill_heading = _SKILL_HEADING_RE.match(line)
        section_heading = _SECTION_HEADING_RE.match(line)
        case_heading = _CASE_HEADING_RE.match(line)

        if skill_heading or (section_heading and not case_heading):
            close_case(line_number)
            if skill_heading:
                current_skill = skill_heading.group(1)
                in_session_continuity = False
            else:
                heading_text = section_heading.group(1).strip()
                in_session_continuity = heading_text == SESSION_CONTINUITY_HEADING
                if in_session_continuity:
                    current_skill = None
            continue

        if case_heading:
            close_case(line_number)
            case_id, title = case_heading.group(1), case_heading.group(2)
            if not in_session_continuity and current_skill is None:
                raise BehaviorCaseParseError(
                    f"{path}: case {case_id} at line {line_number} appears "
                    f"before any '## `skill-name`' heading"
                )
            case_buffer = {
                "case_id": case_id,
                "title": title,
                "skill": current_skill,
                "input_text": "",
                "relevant_learner_state": None,
                "expected_behavior": [],
                "forbidden_behavior": [],
                "success_criteria": "",
                "source_line": line_number,
            }
            current_field = None
            field_buffer = []
            continue

        if case_buffer is None:
            continue

        if line.strip() == "---":
            close_case(line_number)
            continue

        paired_match = _PAIRED_INPUT_RE.match(line)
        if paired_match:
            _flush_field(current_field, field_buffer, case_buffer)
            label, rest_of_line = paired_match.group(1), paired_match.group(2)
            case_buffer["is_paired_input"] = True
            # Reuse current_field/field_buffer to collect this label's
            # wrapped continuation lines, but route the eventual flush
            # through the paired-specific field name below instead of
            # the plain "Input" field, so "Input A" and "Input B" don't
            # overwrite each other.
            current_field = f"Input {label}"
            field_buffer = [rest_of_line] if rest_of_line else []
            continue

        field_match = _FIELD_RE.match(line)
        if field_match:
            _flush_field(current_field, field_buffer, case_buffer)
            current_field = field_match.group(1)
            annotation = field_match.group(2)
            rest_of_line = field_match.group(3)
            first_line = f"{annotation.strip()} {rest_of_line}".strip() if annotation else rest_of_line
            field_buffer = [first_line] if first_line else []
            continue

        if current_field is not None:
            field_buffer.append(line)

    close_case(len(lines) + 1)

    if not cases:
        raise BehaviorCaseParseError(f"{path}: no cases found")

    duplicate_check: dict[str, int] = {}
    for case in cases:
        if case.case_id in duplicate_check:
            raise BehaviorCaseParseError(
                f"{path}: duplicate case id '{case.case_id}' at line "
                f"{case.source_line} (first seen at line "
                f"{duplicate_check[case.case_id]})"
            )
        duplicate_check[case.case_id] = case.source_line

    return cases


def load_case_by_id(repo_root: Path, case_id: str) -> BehaviorCase:
    """Convenience lookup: parse the repo's behavior-cases.md and return one case."""
    cases = parse_behavior_cases(repo_root / BEHAVIOR_CASES_RELPATH)
    for case in cases:
        if case.case_id == case_id:
            return case
    raise BehaviorCaseParseError(
        f"case id '{case_id}' not found in {BEHAVIOR_CASES_RELPATH}"
    )


def main(argv: list[str] | None = None) -> int:
    """Small CLI: list every parsed case id, title, and skill. Useful for
    sanity-checking the parser against the real file without running
    any evaluation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="List every case parsed from evals/behavior-cases.md."
    )
    parser.add_argument("--root", default=".", help="Repository root (default: current directory)")
    args = parser.parse_args(argv)

    repo_root = Path(args.root).resolve()
    try:
        cases = parse_behavior_cases(repo_root / BEHAVIOR_CASES_RELPATH)
    except BehaviorCaseParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 1

    for case in cases:
        skill_label = case.skill or "(cross-skill / no single skill)"
        print(f"{case.case_id}\t{skill_label}\t{case.title}")
    print(f"\n{len(cases)} case(s) parsed.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
