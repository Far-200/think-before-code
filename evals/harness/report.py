#!/usr/bin/env python3
"""Renders a completed evaluation run as a readable Markdown report.

The report's job is to let a human reviewer understand *why* a case
got the verdict it did without re-running anything: it shows the case
id, the skill, the full transcript, the automated-check findings, the
judge's opinion (labeled as an opinion) if one was requested, and the
final verdict. It never claims a verdict is more certain than
`checks.evaluate_case` computed it to be — see that module's docstring
for what `"likely_met"`, `"likely_not_met"`, and `"needs_human_review"`
actually mean.

A case that failed before producing a response at all (a missing
fixture, a provider exception) gets `verdict == "execution_error"` and
a distinct section shape (see `_render_execution_error_section`): no
automated checks or judge opinion ran, so none are shown, but the case
still appears in the report and counts toward the summary and the
total case count — it is never silently absent.
"""

from __future__ import annotations

import datetime
from pathlib import Path

from checks import CaseResult

_VERDICT_LABELS = {
    "likely_met": "✅ Likely met (judge opinion, automated checks did not contradict)",
    "likely_not_met": "❌ Likely not met (judge opinion)",
    "needs_human_review": "🟡 Needs human review",
    "execution_error": "⚠️ Execution error (no response was produced)",
}


def _render_transcript(transcript: list) -> str:
    """Render a transcript as a blockquoted exchange rather than a
    single fenced code block, since a response can itself contain a
    fenced code block (exactly the thing several cases check for) —
    nesting ``` inside ``` breaks Markdown rendering. Blockquote lines
    (`> `) don't have that problem and still read as one contiguous,
    visually distinct transcript.
    """
    lines: list[str] = []
    for message in transcript:
        speaker = "Learner" if message.role == "user" else "Coach"
        lines.append(f"> **{speaker}:**")
        for content_line in message.content.split("\n"):
            lines.append(f"> {content_line}".rstrip())
        lines.append(">")
    return "\n".join(lines)


def _render_execution_error_section(result: CaseResult) -> str:
    """Render a case that failed before producing a response.

    This is a deliberately different shape from a normal case section
    (no expected/forbidden/success fields duplicated, no automated or
    judge sections, since none of that ran) but still a first-class
    section in the report: an execution error must be visible and
    counted, not silently absent from the document, per this harness's
    treatment of `verdict == "execution_error"` as always reportable.
    """
    case = result.case
    transcript_section = (
        _render_transcript(result.transcript)
        if result.transcript
        else "_No conversation history is available — the case failed before any turns were sent._"
    )
    return f"""\
## Case {case.case_id} — {case.title}

- **Skill:** `{case.skill or "(cross-skill)"}`
- **Source:** {BEHAVIOR_CASES_LINK} (line {case.source_line})
- **Verdict:** {_VERDICT_LABELS["execution_error"]}

> This case did not produce a response to evaluate. No automated
> checks or judge opinion were run against it — there was nothing to
> check. It is still counted in this report's summary and total case
> count, since silently dropping a failed case would understate how
> many cases were actually attempted.

### Error
```text
{result.error_message or "(no error message was recorded)"}
```

### Partial transcript
{transcript_section}
"""


def _render_case_section(result: CaseResult, is_live: bool) -> str:
    if result.verdict == "execution_error":
        return _render_execution_error_section(result)

    case = result.case
    verdict_label = _VERDICT_LABELS.get(result.verdict, result.verdict)

    expected = "\n".join(f"- {item}" for item in case.expected_behavior)
    forbidden = "\n".join(f"- {item}" for item in case.forbidden_behavior)

    automated_notes = (
        "\n".join(f"- {note}" for note in result.automated.notes)
        if result.automated.notes
        else "- No automated flags."
    )

    judge_section = "_No judge was configured for this run — verdict rests on automated checks and human review only._"
    if result.judge is not None:
        judge_section = (
            f"**Judge opinion (not a guarantee of correctness): `{result.judge.verdict}`**\n\n"
            f"{result.judge.reasoning}"
        )

    source_note = (
        "live model response" if is_live else "mocked/fixture response — no live model was called"
    )

    return f"""\
## Case {case.case_id} — {case.title}

- **Skill:** `{case.skill or "(cross-skill)"}`
- **Source:** {BEHAVIOR_CASES_LINK} (line {case.source_line})
- **Response source:** {source_note}
- **Verdict:** {verdict_label}

### Expected behavior
{expected}

### Forbidden behavior
{forbidden}

### Success criteria
{case.success_criteria}

### Transcript
{_render_transcript(result.transcript)}

### Automated structural checks
- Fenced code block found: `{result.automated.code_block_found}`
- Question mark count in final response: `{result.automated.question_count}`
- Named hard-stop phrase found (e.g. "here's the solution"): `{result.automated.solution_opening_phrase_found}`

{automated_notes}

### LLM judge
{judge_section}
"""


BEHAVIOR_CASES_LINK = "[`evals/behavior-cases.md`](../../behavior-cases.md)"


def render_report(
    results: list[CaseResult],
    *,
    is_live: bool,
    model_label: str,
    judge_label: str | None,
) -> str:
    """Render a full Markdown report for a list of `CaseResult`s."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    verdict_counts: dict[str, int] = {}
    for result in results:
        verdict_counts[result.verdict] = verdict_counts.get(result.verdict, 0) + 1

    summary_lines = [
        f"- **{_VERDICT_LABELS.get(verdict, verdict)}:** {count}"
        for verdict, count in sorted(verdict_counts.items())
    ]

    run_kind = "LIVE model run" if is_live else "MOCKED run (fixture/scripted responses, no live model call)"
    judge_line = (
        f"LLM judge: `{judge_label}`" if judge_label else "LLM judge: none configured (automated checks + human review only)"
    )

    header = f"""\
# Behavior Evaluation Report

**Generated:** {timestamp}
**Run type:** {run_kind}
**Model under test:** `{model_label}`
**{judge_line}**
**Cases run:** {len(results)}

> This report evaluates *observable coaching behavior* in one sampled
> response per case. It does not measure educational effectiveness,
> and an LLM judge's opinion (where used) is exactly that — an
> opinion from another model, shown with its reasoning so a human
> reviewer can agree or disagree, never an objective guarantee that a
> case passed or failed. Automated structural checks are cheap textual
> signals (code-block presence, question-mark counts, named hard-stop
> phrases), not judgments about coaching quality.

## Summary

{chr(10).join(summary_lines)}

---

"""

    sections = [_render_case_section(result, is_live) for result in results]
    return header + "\n---\n\n".join(sections)


def write_report(
    results: list[CaseResult],
    output_path: Path,
    *,
    is_live: bool,
    model_label: str,
    judge_label: str | None,
) -> None:
    """Render and write a report to `output_path`, creating parent dirs."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_text = render_report(
        results, is_live=is_live, model_label=model_label, judge_label=judge_label
    )
    output_path.write_text(report_text, encoding="utf-8")
