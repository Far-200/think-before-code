#!/usr/bin/env python3
"""Executes selected behavior cases against a configured provider.

This module owns the actual conversation loop:

1. Load the case's skill instructions (its `SKILL.md` body, minus
   frontmatter) as the system prompt — the same file a person would
   copy into their own agent, so the harness tests the real artifact,
   not a paraphrase of it.
2. Replay any `setup_turns` from `case_config.json` to establish the
   conversation state the case's `Relevant learner state` describes.
3. Send the case's own input (or `input_override`, when the case's
   prose input isn't literal text — see `case_config.json`) as the
   final user turn.
4. Return the full transcript and the final assistant response for
   `checks.py` to evaluate.

Cases with `setup_turns` are genuinely multi-turn: each setup turn is
replayed as history, but only the *final* input is actually sent to
the provider for a fresh reply — the setup turns' assistant lines are
fixed script, not additional provider calls, since they exist to
establish state, not to be evaluated themselves. Only the response to
the case's actual `Input` is what `checks.py` evaluates.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from case_parser import BehaviorCase, parse_behavior_cases, BehaviorCaseParseError
from providers import Message, Provider

BEHAVIOR_CASES_RELPATH = Path("evals") / "behavior-cases.md"
CASE_CONFIG_RELPATH = Path("evals") / "harness" / "case_config.json"
SKILLS_RELPATH = Path("skills")

_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)


class RunnerConfigurationError(RuntimeError):
    """Raised when case_config.json or a referenced skill/case can't be resolved."""


@dataclass
class CaseRun:
    """Everything about one case's configured execution, before it's run."""

    case: BehaviorCase
    skill: str
    system_prompt: str
    setup_turns: list[Message]
    final_input: str
    notes: str


def load_skill_system_prompt(repo_root: Path, skill: str) -> str:
    """Load `skills/<skill>/SKILL.md`'s body (frontmatter stripped) as a
    system prompt. Raises `RunnerConfigurationError` if the skill
    directory or file doesn't exist, so a typo in case_config.json
    fails loudly instead of silently testing an empty prompt.
    """
    skill_path = repo_root / SKILLS_RELPATH / skill / "SKILL.md"
    if not skill_path.is_file():
        raise RunnerConfigurationError(
            f"case_config.json names skill '{skill}', but "
            f"{skill_path} does not exist"
        )
    text = skill_path.read_text(encoding="utf-8")
    body = _FRONTMATTER_RE.sub("", text, count=1)
    if body == text:
        raise RunnerConfigurationError(
            f"{skill_path} does not start with the expected '---' "
            f"frontmatter block; refusing to guess at a system prompt"
        )
    return body.strip()


def load_case_config(repo_root: Path) -> dict:
    """Load and minimally validate `case_config.json`."""
    config_path = repo_root / CASE_CONFIG_RELPATH
    if not config_path.is_file():
        raise RunnerConfigurationError(f"{config_path} does not exist")
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RunnerConfigurationError(f"{config_path}: invalid JSON ({exc})") from exc

    if "cases" not in data or not isinstance(data["cases"], list):
        raise RunnerConfigurationError(f"{config_path}: missing or invalid 'cases' array")
    for entry in data["cases"]:
        for required_key in ("case_id", "skill"):
            if required_key not in entry:
                raise RunnerConfigurationError(
                    f"{config_path}: a case entry is missing required key "
                    f"'{required_key}': {entry!r}"
                )
    return data


def build_case_runs(
    repo_root: Path,
    case_ids: list[str] | None = None,
) -> list[CaseRun]:
    """Build the full list of executable `CaseRun`s from case_config.json
    and evals/behavior-cases.md. If `case_ids` is given, only those
    cases are built (still validated against the config and the parsed
    file); otherwise every case in case_config.json is built.
    """
    config = load_case_config(repo_root)
    try:
        all_parsed_cases = {
            c.case_id: c
            for c in parse_behavior_cases(repo_root / BEHAVIOR_CASES_RELPATH)
        }
    except BehaviorCaseParseError as exc:
        raise RunnerConfigurationError(str(exc)) from exc

    configured_ids = {entry["case_id"] for entry in config["cases"]}
    if case_ids is not None:
        unknown = set(case_ids) - configured_ids
        if unknown:
            raise RunnerConfigurationError(
                f"requested case id(s) not in case_config.json: "
                f"{', '.join(sorted(unknown))}. Configured cases: "
                f"{', '.join(sorted(configured_ids))}"
            )

    runs: list[CaseRun] = []
    for entry in config["cases"]:
        if case_ids is not None and entry["case_id"] not in case_ids:
            continue

        case_id = entry["case_id"]
        if case_id not in all_parsed_cases:
            raise RunnerConfigurationError(
                f"case_config.json references case '{case_id}', which was "
                f"not found in {BEHAVIOR_CASES_RELPATH}. It may have been "
                f"renamed or removed — update case_config.json to match."
            )
        case = all_parsed_cases[case_id]
        skill = entry["skill"]

        setup_turns = [
            Message(role=turn["role"], content=turn["content"])
            for turn in entry.get("setup_turns", [])
        ]
        final_input = entry.get("input_override", case.input_text)

        runs.append(
            CaseRun(
                case=case,
                skill=skill,
                system_prompt=load_skill_system_prompt(repo_root, skill),
                setup_turns=setup_turns,
                final_input=final_input,
                notes=entry.get("notes", ""),
            )
        )

    return runs


def execute_case_run(case_run: CaseRun, provider: Provider) -> tuple[list[Message], str]:
    """Run one `CaseRun` against `provider` and return `(transcript,
    final_response)`. `transcript` includes the setup turns and the
    final input/response pair, in order — everything a reviewer would
    need to see to judge the response in context. `provider.send` is
    called exactly once: with the full history (setup turns plus the
    final input) and the loaded system prompt.
    """
    history = list(case_run.setup_turns)
    history.append(Message(role="user", content=case_run.final_input))

    response_text = provider.send(case_run.system_prompt, history)

    transcript = history + [Message(role="assistant", content=response_text)]
    return transcript, response_text
