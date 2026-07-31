#!/usr/bin/env python3
"""Validator for the Find Your Coach routing data.

`find-your-coach/` is a deterministic router: a static page that walks
a visitor through at most three multiple-choice questions and names one
skill in this repository. Every screen it can show comes from
`find-your-coach/routes.json`, and every routing decision it can make
is a declared edge in that file — there is no classifier and no model
call. That makes the routing statically checkable, which is what this
script does.

Checks `find-your-coach/routes.json`:

  * the file exists, is valid UTF-8, and parses as a JSON object,
  * the required top-level keys (`start`, `questions`, `results`) exist
    with the right types,
  * question ids and result ids are unique, and no id is used by both,
  * every question has non-empty text and between `MIN_OPTIONS` and
    `MAX_OPTIONS` options,
  * every option has a non-empty, globally unique id and a non-empty
    label,
  * every option's `next` names an existing question or result,
  * `start` names an existing question,
  * every path from `start` terminates at a result, and no path cycles,
  * every question and result is reachable from `start` (dead route
    data is a defect, not a comment),
  * every `type = "skill"` result names a real skill directory
    containing a `SKILL.md`, with a non-empty `reason` and
    `starter_prompt`,
  * every skill in `skills/` appears as a primary finder result, and no
    result names a skill that does not exist,
  * at least `MIN_NO_MATCH_RESULTS` results are explicitly typed
    `no_match`, and no `no_match` result carries a `skill` or
    `starter_prompt` field — an honest dead end must not be dressed up
    as a recommendation,
  * `handoff` and `closest_skill` references, where present, name real
    skills,
  * every relative skill link the page constructs
    (`<skills_base>/<skill>/SKILL.md`, resolved from
    `find-your-coach/`) exists on disk,
  * the finder's own static assets are present.

Checks `evals/finder-cases.csv`:

  * the header is exactly `EXPECTED_CASE_HEADER`, in that order,
  * every row has the right number of columns, a non-empty unique `id`,
    a non-empty `path`, and a non-empty `reason`,
  * every `path` — option ids separated by `PATH_SEPARATOR` — can
    actually be walked through `routes.json`: each step must be an
    option on the question the previous step led to,
  * each path ends on a result, with no leftover steps,
  * each path reaches its declared `expected_result`,
  * every result and every option is exercised by at least one case, so
    a new branch cannot ship without a routing case behind it.

Exits 0 if everything passes, 1 otherwise, printing one readable error
per problem found rather than stopping at the first.

## Relationship to CI

This script is the single implementation of these rules.
`.github/workflows/validate-skills.yml` invokes it, so the checks that
run on a pull request are exactly the checks a contributor can run
locally with:

    python scripts/validate_finder.py

## Deliberate non-rules

Wording is not validated. Whether a question reads clearly, whether a
`reason` is persuasive, or whether an option lands a visitor in the
right place *pedagogically* is a human review question — the routing
cases in `evals/finder-cases.csv` are where that judgment is recorded.

Result ids are not required to follow a naming scheme, and neither are
option ids beyond uniqueness. Ordering and contiguity are not enforced,
for the same reason `scripts/validate_evals.py` does not enforce them
on activation-prompt ids: it would make retiring a branch painful
without making the data any safer.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

FINDER_RELPATH = Path("find-your-coach")
ROUTES_RELPATH = FINDER_RELPATH / "routes.json"
CASES_RELPATH = Path("evals") / "finder-cases.csv"
SKILLS_RELPATH = Path("skills")

FINDER_ASSETS = ("index.html", "styles.css", "app.js", "routes.json")

REQUIRED_TOP_LEVEL_KEYS = ("start", "questions", "results")

MIN_OPTIONS = 2
MAX_OPTIONS = 6

RESULT_TYPE_SKILL = "skill"
RESULT_TYPE_NO_MATCH = "no_match"
VALID_RESULT_TYPES = (RESULT_TYPE_SKILL, RESULT_TYPE_NO_MATCH)

MIN_NO_MATCH_RESULTS = 2

DEFAULT_SKILLS_BASE = "../skills"

EXPECTED_CASE_HEADER = ["id", "path", "expected_result", "reason"]
PATH_SEPARATOR = ">"


def discover_skills(skills_dir: Path) -> set[str]:
    """Return the names of real skill directories under `skills_dir`.

    A directory counts as a skill if it contains a `SKILL.md`, matching
    how `validate_skills.py` and `validate_evals.py` decide what a
    skill is.
    """
    if not skills_dir.is_dir():
        return set()
    return {
        entry.name
        for entry in skills_dir.iterdir()
        if entry.is_dir() and (entry / "SKILL.md").is_file()
    }


def load_routes(routes_path: Path) -> tuple[dict | None, list[str]]:
    """Read and parse `routes_path`, returning `(data, errors)`."""
    if not routes_path.is_file():
        return None, [f"{routes_path}: file does not exist"]

    try:
        text = routes_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return None, [f"{routes_path}: not valid UTF-8 ({exc})"]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, [f"{routes_path}: is not valid JSON ({exc})"]

    if not isinstance(data, dict):
        return None, [
            f"{routes_path}: top level must be a JSON object, found "
            f"{type(data).__name__}"
        ]

    return data, []


def index_routes(data: dict) -> tuple[dict, dict]:
    """Index the questions and results of `data` by id.

    Tolerant of malformed entries: anything without a usable string id
    is simply left out, and the structural checks report it separately.
    """
    questions: dict[str, dict] = {}
    results: dict[str, dict] = {}

    for question in data.get("questions", []) or []:
        if isinstance(question, dict):
            question_id = question.get("id")
            if isinstance(question_id, str) and question_id:
                questions.setdefault(question_id, question)

    for result in data.get("results", []) or []:
        if isinstance(result, dict):
            result_id = result.get("id")
            if isinstance(result_id, str) and result_id:
                results.setdefault(result_id, result)

    return questions, results


def _check_top_level(routes_path: Path, data: dict) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in data:
            errors.append(f"{routes_path}: missing required top-level key '{key}'")

    if "questions" in data and not isinstance(data["questions"], list):
        errors.append(f"{routes_path}: 'questions' must be a list")
    if "results" in data and not isinstance(data["results"], list):
        errors.append(f"{routes_path}: 'results' must be a list")
    if "start" in data and not (
        isinstance(data["start"], str) and data["start"].strip()
    ):
        errors.append(f"{routes_path}: 'start' must be a non-empty string")

    skills_base = data.get("skills_base", DEFAULT_SKILLS_BASE)
    if not (isinstance(skills_base, str) and skills_base.strip()):
        errors.append(
            f"{routes_path}: 'skills_base' must be a non-empty string when "
            f"present"
        )

    if isinstance(data.get("questions"), list) and not data["questions"]:
        errors.append(f"{routes_path}: 'questions' is empty")
    if isinstance(data.get("results"), list) and not data["results"]:
        errors.append(f"{routes_path}: 'results' is empty")

    return errors


def _check_questions(routes_path: Path, data: dict) -> list[str]:
    errors: list[str] = []
    seen_question_ids: set[str] = set()
    seen_option_ids: dict[str, str] = {}

    for position, question in enumerate(data.get("questions", []) or []):
        label = f"questions[{position}]"

        if not isinstance(question, dict):
            errors.append(f"{routes_path}: {label} is not an object")
            continue

        question_id = question.get("id")
        if not (isinstance(question_id, str) and question_id.strip()):
            errors.append(f"{routes_path}: {label} has a missing or empty id")
            question_id = label
        elif question_id in seen_question_ids:
            errors.append(f"{routes_path}: duplicate question id '{question_id}'")
        else:
            seen_question_ids.add(question_id)

        text = question.get("text")
        if not (isinstance(text, str) and text.strip()):
            errors.append(
                f"{routes_path}: question '{question_id}' has missing or "
                f"empty text"
            )

        options = question.get("options")
        if not isinstance(options, list):
            errors.append(
                f"{routes_path}: question '{question_id}' has no options list"
            )
            continue

        if not MIN_OPTIONS <= len(options) <= MAX_OPTIONS:
            errors.append(
                f"{routes_path}: question '{question_id}' has {len(options)} "
                f"option(s), expected between {MIN_OPTIONS} and {MAX_OPTIONS}"
            )

        for option_position, option in enumerate(options):
            option_label = f"question '{question_id}' option[{option_position}]"

            if not isinstance(option, dict):
                errors.append(f"{routes_path}: {option_label} is not an object")
                continue

            option_id = option.get("id")
            if not (isinstance(option_id, str) and option_id.strip()):
                errors.append(
                    f"{routes_path}: {option_label} has a missing or empty id"
                )
            elif option_id in seen_option_ids:
                errors.append(
                    f"{routes_path}: duplicate option id '{option_id}' in "
                    f"question '{question_id}' (already used in question "
                    f"'{seen_option_ids[option_id]}')"
                )
            else:
                seen_option_ids[option_id] = str(question_id)

            option_text = option.get("label")
            if not (isinstance(option_text, str) and option_text.strip()):
                errors.append(
                    f"{routes_path}: {option_label} has a missing or empty "
                    f"label"
                )

            if not (
                isinstance(option.get("next"), str) and option["next"].strip()
            ):
                errors.append(
                    f"{routes_path}: {option_label} has a missing or empty "
                    f"'next' target"
                )

    return errors


def _check_edges(routes_path: Path, data: dict, questions: dict, results: dict) -> list[str]:
    """Every `next` must name a node, and no id may be used twice."""
    errors: list[str] = []

    for shared in sorted(set(questions) & set(results)):
        errors.append(
            f"{routes_path}: id '{shared}' is used by both a question and a "
            f"result"
        )

    known = set(questions) | set(results)

    start = data.get("start")
    if isinstance(start, str) and start.strip() and start not in questions:
        errors.append(
            f"{routes_path}: 'start' names '{start}', which is not a question"
        )

    for question_id, question in questions.items():
        for option in question.get("options", []) or []:
            if not isinstance(option, dict):
                continue
            target = option.get("next")
            if isinstance(target, str) and target.strip() and target not in known:
                errors.append(
                    f"{routes_path}: option '{option.get('id')}' in question "
                    f"'{question_id}' points at '{target}', which is neither "
                    f"a question nor a result"
                )

    return errors


def _check_traversal(routes_path: Path, data: dict, questions: dict, results: dict) -> list[str]:
    """Reject cycles, dead ends, and unreachable nodes."""
    errors: list[str] = []

    start = data.get("start")
    if not (isinstance(start, str) and start in questions):
        return errors

    reached_results: set[str] = set()
    visited_questions: set[str] = set()
    reported_cycles: set[str] = set()

    def walk(node_id: str, on_path: list[str]) -> None:
        if node_id in results:
            reached_results.add(node_id)
            return

        if node_id not in questions:
            # Already reported by the edge check.
            return

        if node_id in on_path:
            cycle = " > ".join(on_path[on_path.index(node_id):] + [node_id])
            if cycle not in reported_cycles:
                reported_cycles.add(cycle)
                errors.append(f"{routes_path}: routing cycle detected: {cycle}")
            return

        visited_questions.add(node_id)
        question = questions[node_id]
        options = question.get("options", []) or []

        if not options:
            errors.append(
                f"{routes_path}: question '{node_id}' has no options, so a "
                f"visitor who reaches it can never reach a result"
            )
            return

        on_path.append(node_id)
        for option in options:
            if not isinstance(option, dict):
                continue
            target = option.get("next")
            if isinstance(target, str) and target.strip():
                walk(target, on_path)
        on_path.pop()

    walk(start, [])

    for question_id in sorted(set(questions) - visited_questions):
        errors.append(
            f"{routes_path}: question '{question_id}' is unreachable from "
            f"'{start}'"
        )
    for result_id in sorted(set(results) - reached_results):
        errors.append(
            f"{routes_path}: result '{result_id}' is unreachable from "
            f"'{start}'"
        )

    return errors


def _skill_link_target(repo_root: Path, skills_base: str, skill: str) -> Path:
    """Resolve the link the page builds for `skill`.

    The page lives in `find-your-coach/` and constructs
    `<skills_base>/<skill>/SKILL.md`, so the same relative path is
    resolved from the same directory here.
    """
    return (repo_root / FINDER_RELPATH / skills_base / skill / "SKILL.md").resolve()


def _check_results(
    routes_path: Path,
    repo_root: Path,
    data: dict,
    results: dict,
    skills: set[str],
) -> list[str]:
    errors: list[str] = []
    seen_result_ids: set[str] = set()

    skills_base = data.get("skills_base", DEFAULT_SKILLS_BASE)
    if not isinstance(skills_base, str) or not skills_base.strip():
        skills_base = DEFAULT_SKILLS_BASE

    primary_skills: set[str] = set()
    no_match_count = 0

    for position, result in enumerate(data.get("results", []) or []):
        label = f"results[{position}]"

        if not isinstance(result, dict):
            errors.append(f"{routes_path}: {label} is not an object")
            continue

        result_id = result.get("id")
        if not (isinstance(result_id, str) and result_id.strip()):
            errors.append(f"{routes_path}: {label} has a missing or empty id")
            result_id = label
        elif result_id in seen_result_ids:
            errors.append(f"{routes_path}: duplicate result id '{result_id}'")
        else:
            seen_result_ids.add(result_id)

        result_type = result.get("type")
        if result_type not in VALID_RESULT_TYPES:
            errors.append(
                f"{routes_path}: result '{result_id}' has type "
                f"{result_type!r}, expected one of {list(VALID_RESULT_TYPES)}"
            )
            continue

        if not (
            isinstance(result.get("reason"), str) and result["reason"].strip()
        ):
            errors.append(
                f"{routes_path}: result '{result_id}' has a missing or empty "
                f"reason"
            )

        if result_type == RESULT_TYPE_SKILL:
            errors.extend(
                _check_skill_result(
                    routes_path, repo_root, skills_base, result, result_id, skills
                )
            )
            skill = result.get("skill")
            if isinstance(skill, str) and skill in skills:
                primary_skills.add(skill)
        else:
            no_match_count += 1
            errors.extend(
                _check_no_match_result(
                    routes_path, repo_root, skills_base, result, result_id, skills
                )
            )

    if no_match_count < MIN_NO_MATCH_RESULTS:
        errors.append(
            f"{routes_path}: found {no_match_count} result(s) of type "
            f"'{RESULT_TYPE_NO_MATCH}', expected at least "
            f"{MIN_NO_MATCH_RESULTS} — the finder must be able to say that "
            f"nothing here fits"
        )

    for skill in sorted(skills - primary_skills):
        errors.append(
            f"{routes_path}: skill '{skill}' is never reachable as a primary "
            f"finder result"
        )

    return errors


def _check_skill_result(
    routes_path: Path,
    repo_root: Path,
    skills_base: str,
    result: dict,
    result_id: str,
    skills: set[str],
) -> list[str]:
    errors: list[str] = []

    skill = result.get("skill")
    if not (isinstance(skill, str) and skill.strip()):
        errors.append(
            f"{routes_path}: result '{result_id}' has type "
            f"'{RESULT_TYPE_SKILL}' but no skill name"
        )
    elif skill not in skills:
        errors.append(
            f"{routes_path}: result '{result_id}' names skill '{skill}', "
            f"which is not a directory containing a SKILL.md under "
            f"'{SKILLS_RELPATH}/'"
        )
    else:
        target = _skill_link_target(repo_root, skills_base, skill)
        if not target.is_file():
            errors.append(
                f"{routes_path}: result '{result_id}' would link to "
                f"'{skills_base}/{skill}/SKILL.md', which does not resolve "
                f"({target})"
            )

    if not (
        isinstance(result.get("starter_prompt"), str)
        and result["starter_prompt"].strip()
    ):
        errors.append(
            f"{routes_path}: result '{result_id}' has a missing or empty "
            f"starter_prompt"
        )

    errors.extend(
        _check_skill_reference(
            routes_path, repo_root, skills_base, result, result_id, skills, "handoff"
        )
    )

    return errors


def _check_no_match_result(
    routes_path: Path,
    repo_root: Path,
    skills_base: str,
    result: dict,
    result_id: str,
    skills: set[str],
) -> list[str]:
    errors: list[str] = []

    for forbidden in ("skill", "starter_prompt"):
        if forbidden in result:
            errors.append(
                f"{routes_path}: no-match result '{result_id}' carries "
                f"'{forbidden}' — a no-match outcome must not present itself "
                f"as a skill recommendation"
            )

    if not (
        isinstance(result.get("explanation"), str)
        and result["explanation"].strip()
    ):
        errors.append(
            f"{routes_path}: no-match result '{result_id}' has a missing or "
            f"empty explanation"
        )

    errors.extend(
        _check_skill_reference(
            routes_path,
            repo_root,
            skills_base,
            result,
            result_id,
            skills,
            "closest_skill",
        )
    )

    return errors


def _check_skill_reference(
    routes_path: Path,
    repo_root: Path,
    skills_base: str,
    result: dict,
    result_id: str,
    skills: set[str],
    key: str,
) -> list[str]:
    """Validate an optional `{skill, note}` reference on a result."""
    errors: list[str] = []
    reference = result.get(key)

    if reference is None:
        return errors

    if not isinstance(reference, dict):
        errors.append(
            f"{routes_path}: result '{result_id}' has a '{key}' that is not "
            f"an object"
        )
        return errors

    skill = reference.get("skill")
    if not (isinstance(skill, str) and skill.strip()):
        errors.append(
            f"{routes_path}: result '{result_id}' has a '{key}' without a "
            f"skill name"
        )
        return errors

    if skill not in skills:
        errors.append(
            f"{routes_path}: result '{result_id}' has a '{key}' naming "
            f"'{skill}', which is not a real skill"
        )
        return errors

    target = _skill_link_target(repo_root, skills_base, skill)
    if not target.is_file():
        errors.append(
            f"{routes_path}: result '{result_id}' '{key}' would link to "
            f"'{skills_base}/{skill}/SKILL.md', which does not resolve "
            f"({target})"
        )

    return errors


def _check_finder_assets(finder_dir: Path) -> list[str]:
    errors: list[str] = []
    if not finder_dir.is_dir():
        return [f"{finder_dir}: directory does not exist"]
    for asset in FINDER_ASSETS:
        if not (finder_dir / asset).is_file():
            errors.append(f"{finder_dir / asset}: missing finder asset")
    return errors


def validate_routes(routes_path: Path, skills_dir: Path) -> tuple[dict | None, list[str]]:
    """Validate the route data, returning `(data, errors)`."""
    data, errors = load_routes(routes_path)
    if data is None:
        return None, errors

    repo_root = routes_path.parent.parent
    skills = discover_skills(skills_dir)

    if not skills_dir.is_dir():
        errors.append(
            f"{skills_dir}: directory does not exist, so skill results "
            f"cannot be checked"
        )

    errors.extend(_check_top_level(routes_path, data))
    errors.extend(_check_questions(routes_path, data))

    questions, results = index_routes(data)

    errors.extend(_check_edges(routes_path, data, questions, results))
    errors.extend(_check_traversal(routes_path, data, questions, results))
    errors.extend(_check_results(routes_path, repo_root, data, results, skills))

    return data, errors


def read_case_records(csv_path: Path) -> tuple[list[tuple[int, list[str]]], list[str]]:
    """Read `csv_path` into `(line_number, row)` pairs."""
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


def walk_path(
    data: dict,
    questions: dict,
    results: dict,
    option_ids: list[str],
) -> tuple[str | None, str | None]:
    """Walk `option_ids` from the start question.

    Returns `(result_id, error)`. Exactly one of the two is `None`.
    """
    node_id = data.get("start")
    if not (isinstance(node_id, str) and node_id in questions):
        return None, "the route data has no usable starting question"

    for position, option_id in enumerate(option_ids, start=1):
        if node_id in results:
            return None, (
                f"step {position} ('{option_id}') comes after the path has "
                f"already reached result '{node_id}'"
            )

        question = questions.get(node_id)
        if question is None:
            return None, f"step {position} starts from unknown question '{node_id}'"

        chosen = None
        for option in question.get("options", []) or []:
            if isinstance(option, dict) and option.get("id") == option_id:
                chosen = option
                break

        if chosen is None:
            return None, (
                f"step {position} ('{option_id}') is not an option on "
                f"question '{node_id}'"
            )

        node_id = chosen.get("next")
        if not isinstance(node_id, str):
            return None, f"step {position} ('{option_id}') has no 'next' target"

    if node_id in results:
        return node_id, None

    return None, f"the path stops on question '{node_id}' instead of a result"


def validate_finder_cases(csv_path: Path, data: dict | None) -> list[str]:
    """Validate `evals/finder-cases.csv` against the route data."""
    records, errors = read_case_records(csv_path)
    if errors:
        return errors

    if not records:
        return [f"{csv_path}: file is empty"]

    _, header = records[0]
    if header != EXPECTED_CASE_HEADER:
        return [
            f"{csv_path}: unexpected header {header!r}, expected "
            f"{EXPECTED_CASE_HEADER!r}"
        ]

    if data is None:
        return [
            f"{csv_path}: the route data could not be loaded, so no path can "
            f"be checked"
        ]

    questions, results = index_routes(data)

    all_option_ids: set[str] = set()
    for question in questions.values():
        for option in question.get("options", []) or []:
            if isinstance(option, dict) and isinstance(option.get("id"), str):
                all_option_ids.add(option["id"])

    seen_ids: dict[str, int] = {}
    covered_results: set[str] = set()
    covered_options: set[str] = set()

    for line, row in records[1:]:
        if len(row) != len(EXPECTED_CASE_HEADER):
            errors.append(
                f"{csv_path}: line {line} has {len(row)} column(s), expected "
                f"{len(EXPECTED_CASE_HEADER)}"
            )
            continue

        case_id, path, expected_result, reason = row

        if not case_id.strip():
            errors.append(f"{csv_path}: line {line} has an empty id")
        elif case_id in seen_ids:
            errors.append(
                f"{csv_path}: duplicate id '{case_id}' at line {line} (first "
                f"used at line {seen_ids[case_id]})"
            )
        else:
            seen_ids[case_id] = line

        if not reason.strip():
            errors.append(f"{csv_path}: line {line} has an empty reason")

        if not path.strip():
            errors.append(f"{csv_path}: line {line} has an empty path")
            continue

        option_ids = [step.strip() for step in path.split(PATH_SEPARATOR)]
        if any(not step for step in option_ids):
            errors.append(
                f"{csv_path}: line {line} has an empty step in path {path!r}"
            )
            continue

        covered_options.update(option_ids)

        if not expected_result.strip():
            errors.append(f"{csv_path}: line {line} has an empty expected_result")
        elif expected_result not in results:
            errors.append(
                f"{csv_path}: line {line} expects result '{expected_result}', "
                f"which does not exist in the route data"
            )

        reached, walk_error = walk_path(data, questions, results, option_ids)
        if walk_error is not None:
            errors.append(f"{csv_path}: line {line} ({case_id}): {walk_error}")
            continue

        covered_results.add(reached)

        if expected_result.strip() and reached != expected_result:
            errors.append(
                f"{csv_path}: line {line} ({case_id}): path reaches "
                f"'{reached}', but expected_result is '{expected_result}'"
            )

    for result_id in sorted(set(results) - covered_results):
        errors.append(
            f"{csv_path}: result '{result_id}' has no routing case reaching it"
        )
    for option_id in sorted(all_option_ids - covered_options):
        errors.append(
            f"{csv_path}: option '{option_id}' is not exercised by any "
            f"routing case"
        )

    return errors


def validate_finder(repo_root: Path) -> list[str]:
    """Validate the finder's route data and routing cases."""
    errors = _check_finder_assets(repo_root / FINDER_RELPATH)

    data, route_errors = validate_routes(
        repo_root / ROUTES_RELPATH,
        repo_root / SKILLS_RELPATH,
    )
    errors.extend(route_errors)
    errors.extend(validate_finder_cases(repo_root / CASES_RELPATH, data))

    return errors


def count_cases(csv_path: Path) -> int:
    """Return the number of non-header records in `csv_path`."""
    records, errors = read_case_records(csv_path)
    if errors or not records:
        return 0
    return len(records) - 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the Find Your Coach routing data "
            "(find-your-coach/routes.json) and the routing cases in "
            "evals/finder-cases.csv: structure, reachability, honest "
            "no-match outcomes, real skill links, and every declared path "
            "reaching its expected result."
        )
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to validate (default: current directory)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.root).resolve()
    errors = validate_finder(repo_root)

    if errors:
        print(f"Found {len(errors)} problem(s):\n", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    data, _ = load_routes(repo_root / ROUTES_RELPATH)
    questions, results = index_routes(data or {})
    print(
        f"OK: {len(questions)} question(s) and {len(results)} result(s) "
        f"validated; {count_cases(repo_root / CASES_RELPATH)} routing case(s) "
        f"reach their expected result."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
