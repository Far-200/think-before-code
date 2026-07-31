#!/usr/bin/env python3
"""Validator for this repository's evaluation specifications.

Checks `evals/activation-prompts.csv`, the activation and negative-
activation specification consumed by CI (and, eventually, by an
automated runner):

  * the CSV exists and is not empty,
  * the header row is exactly `EXPECTED_HEADER`, in that order,
  * every row has exactly as many columns as the header,
  * every row has a non-empty `id`,
  * no two rows share an `id`,
  * every `target_skill` is either a real skill directory under
    `skills/` (a directory containing a `SKILL.md`) or the literal
    `none`,
  * every `should_activate` value is exactly `true` or `false`,
  * `prompt` and `reason` are non-empty,
  * every real skill has at least one `should_activate = true` row
    (positive activation coverage),
  * every real skill has at least one `should_activate = false` row
    (negative activation coverage) — a skill with no negative case has
    an untested activation boundary.

Rows with `target_skill = none` are allowed (they assert that *no*
skill in this repository should engage) but do not count toward any
skill's coverage.

Exits 0 if everything passes, 1 otherwise, printing one readable error
per problem found, each naming the file and, where applicable, the
line, field, id, or skill involved.

## Relationship to CI

This script is the single implementation of these rules. The
`validate-skills.yml` workflow invokes it rather than restating the
logic in YAML, so the checks that run in CI are exactly the checks a
contributor can run locally with:

    python scripts/validate_evals.py

## Deliberate non-rules

The `id` values in this repository currently follow an `A001`-style
sequence, but this validator intentionally does **not** enforce a
prefix, a fixed width, contiguity, or ordering. None of those were
ever enforced in CI, and requiring them would make it painful to
retire a row or reserve a range. Uniqueness and non-emptiness are
what the specification actually depends on.

Column *values* beyond the checks above are not validated: whether a
`prompt` is a good test of a boundary, or whether a `reason` is
accurate, is a human review question, not a structural one.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

EXPECTED_HEADER = ["id", "target_skill", "should_activate", "prompt", "reason"]

VALID_ACTIVATION_VALUES = ("true", "false")

NO_SKILL = "none"

ACTIVATION_CSV_RELPATH = Path("evals") / "activation-prompts.csv"
SKILLS_RELPATH = Path("skills")


def discover_skills(skills_dir: Path) -> set[str]:
    """Return the names of real skill directories under `skills_dir`.

    A directory counts as a skill if it contains a `SKILL.md`, which
    matches how `validate_skills.py` decides what a skill is.
    """
    if not skills_dir.is_dir():
        return set()
    return {
        entry.name
        for entry in skills_dir.iterdir()
        if entry.is_dir() and (entry / "SKILL.md").is_file()
    }


def read_csv_records(csv_path: Path) -> tuple[list[tuple[int, list[str]]], list[str]]:
    """Read `csv_path` into `(line_number, row)` pairs.

    Returns the records and a list of errors. If the errors list is
    non-empty the records should not be trusted. The line number is
    the physical line the record ended on, so error messages stay
    useful even if a quoted field ever contains a newline.
    """
    if not csv_path.is_file():
        return [], [f"{csv_path}: file does not exist"]

    try:
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            return [(reader.line_num, row) for row in reader], []
    except UnicodeDecodeError as exc:
        return [], [f"{csv_path}: not valid UTF-8 ({exc})"]
    except csv.Error as exc:
        return [], [f"{csv_path}: could not be parsed as CSV ({exc})"]


def validate_activation_prompts(csv_path: Path, skills_dir: Path) -> list[str]:
    """Validate the activation-prompt CSV against the skills on disk.

    Returns a list of readable error strings — empty when the CSV
    satisfies every rule documented in the module docstring.
    """
    records, errors = read_csv_records(csv_path)
    if errors:
        return errors

    if not records:
        return [f"{csv_path}: file is empty"]

    _, header = records[0]
    if header != EXPECTED_HEADER:
        return [
            f"{csv_path}: unexpected header {header!r}, expected "
            f"{EXPECTED_HEADER!r}"
        ]

    if not skills_dir.is_dir():
        return [
            f"{skills_dir}: directory does not exist, so target_skill "
            f"values and per-skill activation coverage cannot be checked"
        ]

    skills = discover_skills(skills_dir)
    valid_targets = skills | {NO_SKILL}

    seen_ids: dict[str, int] = {}
    coverage: dict[str, set[str]] = {}

    for line, row in records[1:]:
        if len(row) != len(EXPECTED_HEADER):
            errors.append(
                f"{csv_path}: line {line} has {len(row)} column(s), "
                f"expected {len(EXPECTED_HEADER)}"
            )
            continue

        row_id, target_skill, should_activate, prompt, reason = row

        if not row_id.strip():
            errors.append(f"{csv_path}: line {line} has an empty id")
        elif row_id in seen_ids:
            errors.append(
                f"{csv_path}: duplicate id '{row_id}' at line {line} "
                f"(first used at line {seen_ids[row_id]})"
            )
        else:
            seen_ids[row_id] = line

        if target_skill not in valid_targets:
            errors.append(
                f"{csv_path}: line {line} has target_skill "
                f"{target_skill!r}, which is not a skill directory under "
                f"'{skills_dir.name}/' and is not '{NO_SKILL}'"
            )

        if should_activate not in VALID_ACTIVATION_VALUES:
            errors.append(
                f"{csv_path}: line {line} has invalid should_activate "
                f"value {should_activate!r}, expected one of "
                f"{list(VALID_ACTIVATION_VALUES)}"
            )

        if not prompt.strip():
            errors.append(f"{csv_path}: line {line} has an empty prompt")

        if not reason.strip():
            errors.append(f"{csv_path}: line {line} has an empty reason")

        if target_skill in skills and should_activate in VALID_ACTIVATION_VALUES:
            coverage.setdefault(target_skill, set()).add(should_activate)

    for skill in sorted(skills):
        seen = coverage.get(skill, set())
        if "true" not in seen:
            errors.append(
                f"{csv_path}: skill '{skill}' has no should_activate = "
                f"true row (no positive activation case)"
            )
        if "false" not in seen:
            errors.append(
                f"{csv_path}: skill '{skill}' has no should_activate = "
                f"false row (no negative activation case)"
            )

    return errors


def count_activation_rows(csv_path: Path) -> int:
    """Return the number of non-header records in `csv_path`."""
    records, errors = read_csv_records(csv_path)
    if errors or not records:
        return 0
    return len(records) - 1


def validate_evals(repo_root: Path) -> list[str]:
    """Validate every evaluation specification under `repo_root`."""
    return validate_activation_prompts(
        repo_root / ACTIVATION_CSV_RELPATH,
        repo_root / SKILLS_RELPATH,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate this repository's evaluation specifications "
            "(evals/activation-prompts.csv): shape, uniqueness, valid "
            "target skills, and positive plus negative activation "
            "coverage for every skill."
        )
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to validate (default: current directory)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.root).resolve()
    errors = validate_evals(repo_root)

    if errors:
        print(f"Found {len(errors)} problem(s):\n", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    csv_path = repo_root / ACTIVATION_CSV_RELPATH
    skill_count = len(discover_skills(repo_root / SKILLS_RELPATH))
    print(
        f"OK: {count_activation_rows(csv_path)} activation-prompt row(s) "
        f"validated; all {skill_count} skill(s) have positive and "
        f"negative activation coverage."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
