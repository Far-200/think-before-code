#!/usr/bin/env python3
r"""CLI entry point for the Think Before Code behavior-evaluation harness.

Runs a selected subset of `evals/behavior-cases.md`'s cases (as
configured in `evals/harness/case_config.json`) against a provider and
writes a Markdown report.

## Modes

- **Mocked (default and always available):**

      python evals/harness/run_eval.py --fixtures evals/harness/fixtures/example_run.json

  Reads pre-recorded responses from a fixture file (see
  `fixtures/example_run.json` for the format) and runs the full
  pipeline — case selection, skill loading, transcript assembly,
  automated checks, optional judge — with zero network access and zero
  API cost. This is what CI and this repository's own tests use.

- **Live (requires the `anthropic` package and an API key):**

      python3 -m venv .venv
      source .venv/bin/activate      # Windows: .venv\Scripts\activate
      pip install anthropic
      export ANTHROPIC_API_KEY=sk-...
      python evals/harness/run_eval.py --live --model claude-sonnet-4-6

  Actually calls the Anthropic API for each case. Requires the
  `anthropic` package, installed into a virtual environment as shown
  above rather than into the system Python. Never required to run
  this repository's existing structural validators or unit tests —
  see the top-level README's Testing and validation section.

Exactly one of `--fixtures` or `--live` must be given.

## What this harness does not do

It does not prove a skill produces good learning outcomes — it checks
whether a sampled response matches the documented expected/forbidden
behavior for a case, using cheap automated text checks plus an
optional, clearly-labeled LLM judge opinion. See `checks.py` and
`report.py` for exactly what each verdict does and doesn't mean.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from checks import evaluate_case, make_execution_error_result
from providers import AnthropicProvider, MockProvider, Provider, ProviderConfigurationError
from runner import RunnerConfigurationError, build_case_runs, execute_case_run


def _load_fixture_responses(fixture_path: Path) -> dict[str, list[str]]:
    if not fixture_path.is_file():
        raise RunnerConfigurationError(f"{fixture_path} does not exist")
    try:
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RunnerConfigurationError(f"{fixture_path}: invalid JSON ({exc})") from exc

    responses = data.get("responses")
    if not isinstance(responses, dict):
        raise RunnerConfigurationError(
            f"{fixture_path}: expected a top-level 'responses' object mapping "
            f"case id -> list of response strings"
        )
    return responses


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a representative subset of evals/behavior-cases.md against "
            "a configured provider and write a Markdown report."
        )
    )
    parser.add_argument("--root", default=".", help="Repository root (default: current directory)")
    parser.add_argument(
        "--cases",
        nargs="*",
        default=None,
        help="Case ids to run (default: every case in case_config.json)",
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--fixtures",
        metavar="FIXTURE_JSON",
        help="Path to a fixture file of pre-recorded responses (mocked run, no network access)",
    )
    mode_group.add_argument(
        "--live",
        action="store_true",
        help="Call the real Anthropic API (requires 'anthropic' package and ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Model name to use for --live (ignored for --fixtures)",
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        help=(
            "Also ask an LLM judge for an opinion on each case (requires --live, "
            "since the mocked path has no model to ask; the judge opinion is "
            "always reported as an opinion, never a verdict — see checks.py)"
        ),
    )
    parser.add_argument(
        "--output",
        default="evals/harness/reports/latest.md",
        help="Where to write the Markdown report",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.root).resolve()

    try:
        case_runs = build_case_runs(repo_root, case_ids=args.cases)
    except RunnerConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    if not case_runs:
        print("No cases selected — nothing to run.", file=sys.stderr)
        return 1

    if args.judge and not args.live:
        print(
            "Error: --judge requires --live (the mocked path has no model "
            "available to act as a judge).",
            file=sys.stderr,
        )
        return 1

    provider: Provider
    judge_provider: Provider | None = None
    model_label: str

    if args.fixtures:
        try:
            fixture_responses = _load_fixture_responses(Path(args.fixtures))
        except RunnerConfigurationError as exc:
            print(f"Fixture error: {exc}", file=sys.stderr)
            return 1
        is_live = False
        model_label = "mock (fixture-driven)"
    else:
        try:
            live_provider = AnthropicProvider(model=args.model)
        except ProviderConfigurationError as exc:
            print(f"Provider error: {exc}", file=sys.stderr)
            return 1
        is_live = True
        model_label = args.model
        if args.judge:
            judge_provider = live_provider

    results = []
    for case_run in case_runs:
        if args.fixtures:
            if case_run.case.case_id not in fixture_responses:
                message = (
                    f"no fixture response found for case "
                    f"'{case_run.case.case_id}' in {args.fixtures}"
                )
                print(f"Warning: {message} — recording as an execution error.", file=sys.stderr)
                results.append(make_execution_error_result(case_run.case, message))
                continue
            provider = MockProvider(
                responses_by_case=fixture_responses, case_id=case_run.case.case_id
            )
        else:
            provider = live_provider  # noqa: F821 -- only reached when args.live

        try:
            transcript, response_text = execute_case_run(case_run, provider)
        except Exception as exc:  # noqa: BLE001 -- one case's failure shouldn't abort the run
            message = f"{type(exc).__name__}: {exc}"
            print(
                f"Error executing case '{case_run.case.case_id}': {message}",
                file=sys.stderr,
            )
            results.append(make_execution_error_result(case_run.case, message))
            continue

        result = evaluate_case(case_run.case, transcript, response_text, judge_provider)
        results.append(result)

    if not results:
        print("No cases produced a result — nothing to report.", file=sys.stderr)
        return 1

    from report import write_report

    output_path = repo_root / args.output
    write_report(
        results,
        output_path,
        is_live=is_live,
        model_label=model_label,
        judge_label=args.model if judge_provider else None,
    )

    verdict_counts: dict[str, int] = {}
    for result in results:
        verdict_counts[result.verdict] = verdict_counts.get(result.verdict, 0) + 1
    summary = ", ".join(f"{v}={c}" for v, c in sorted(verdict_counts.items()))
    print(f"Ran {len(results)} case(s). {summary}")
    print(f"Report written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
