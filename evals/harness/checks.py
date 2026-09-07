#!/usr/bin/env python3
"""Checks applied to a model's response for one behavior case.

This module deliberately keeps two kinds of check in separate,
clearly labeled buckets, because they carry very different evidential
weight:

1. **Automated structural checks** (`run_automated_checks`) — cheap,
   deterministic, and fully explainable: did a fenced code block
   appear, how many question marks are in the response, does the text
   contain a substring that would make a specific forbidden-behavior
   bullet trivially true. These are facts about the text, not
   judgments about whether the coaching was good. They can produce
   false positives (a mention of "for example, `x[i]`" is not a
   solution) and false negatives (a solution given in prose with no
   code fence still counts as a solution), so they are signals for a
   human reviewer, not a verdict.

2. **LLM judge opinion** (`run_llm_judge`) — asks a model whether the
   response satisfied the case's expected/forbidden behavior, given
   the full conversation that produced it (scripted setup turns and
   the actual final input or `input_override` actually sent — see
   `_build_judge_prompt`), not just the case's own parsed prose
   `input_text`. This matters most for multi-turn and Resume Pack
   fidelity cases, where the prose in `behavior-cases.md` describes
   context rather than giving it verbatim (see `case_config.json`'s
   `setup_turns`/`input_override`) — judging against the prose alone
   would have the judge reason about a conversation that never
   actually happened. This is explicitly an opinion from a model with
   its own failure modes, not ground truth. Every place this harness
   surfaces a judge verdict, it is labeled `judge_opinion` and carries
   the judge's own stated reasoning, so a report reader is never given
   a judge's answer dressed up as an objective pass/fail. `run_llm_judge`
   is optional: it requires a provider capable of a judging call, and
   its absence is not an error — a report can be generated from
   automated checks alone plus a "needs human review" flag.

`evaluate_case` combines both into one `CaseResult` and is what
`runner.py` actually calls; it never claims a case has *passed* on the
strength of the LLM judge alone. See `CaseResult.verdict`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from case_parser import BehaviorCase
from providers import Message, Provider

# A fenced code block of 2+ lines, or an obviously runnable single-line
# statement, is treated as "code appeared" for the automated check.
# This is intentionally conservative (prefers false negatives over
# false positives) since a false positive here would wrongly flag a
# response that just used inline `code formatting` for a variable name.
_FENCED_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```")

# Phrases the dsa-tutor SKILL.md itself names as an explicit hard stop
# ("if the next sentence you're about to write starts with..."). Kept
# here rather than hard-coded per-case, since they're a property of the
# skill's own circuit breaker, not of one case.
_SOLUTION_OPENING_PHRASES = (
    "here's the solution",
    "here is the solution",
    "the answer is",
    "the solution is",
)


@dataclass
class AutomatedCheckResult:
    """Result of the cheap, deterministic checks on one response."""

    code_block_found: bool
    question_count: int
    solution_opening_phrase_found: bool
    notes: list[str] = field(default_factory=list)


@dataclass
class JudgeOpinion:
    """An LLM judge's opinion on whether a response met a case's criteria.

    This is explicitly an opinion, not a verdict. `verdict` is the
    judge's own self-reported classification; `reasoning` is the
    judge's own stated reasoning, shown verbatim in reports so a human
    reader can disagree with it.
    """

    verdict: str  # one of "met", "not_met", "unclear" -- as reported BY THE JUDGE
    reasoning: str
    raw_response: str


@dataclass
class CaseResult:
    """The combined result of evaluating one case's response(s).

    `verdict == "execution_error"` is a distinct outcome from every
    other verdict: it means the case never produced a response to
    evaluate at all (the provider raised, a fixture response was
    missing, a setup/config problem surfaced during execution, etc.),
    so `automated` and `judge` are both `None` and `transcript` holds
    whatever partial history exists (possibly empty). This is
    deliberately still a `CaseResult` — not a silently dropped case —
    so it always appears in the report and always counts toward the
    run's total, rather than vanishing from the results and quietly
    shrinking the denominator. See `make_execution_error_result`.
    """

    case: BehaviorCase
    transcript: list[Message] | None
    automated: AutomatedCheckResult | None
    judge: JudgeOpinion | None
    verdict: str  # "needs_human_review" and "execution_error" are always possible -- see evaluate_case
    error_message: str | None = None


def make_execution_error_result(
    case: BehaviorCase, error_message: str, transcript: list[Message] | None = None
) -> CaseResult:
    """Build a `CaseResult` for a case that failed before it could be
    evaluated (the provider raised, a fixture was missing, etc.).

    `transcript` is whatever partial history is available — pass
    `None` when nothing was assembled at all (e.g. the case's
    `CaseRun` couldn't be built). The result's `verdict` is always the
    literal `"execution_error"`, distinct from `"needs_human_review"`:
    the latter means a response was produced and evaluated but the
    verdict is inconclusive, while the former means no response was
    produced at all.
    """
    return CaseResult(
        case=case,
        transcript=transcript,
        automated=None,
        judge=None,
        verdict="execution_error",
        error_message=error_message,
    )


def run_automated_checks(case: BehaviorCase, response_text: str) -> AutomatedCheckResult:
    """Run cheap, deterministic checks against one model response.

    These check facts about the text (code present, question count,
    a named hard-stop phrase), not whether the coaching was good. See
    the module docstring for why this stays separate from judgment.
    """
    notes: list[str] = []

    code_block_found = bool(_FENCED_CODE_BLOCK_RE.search(response_text))
    if code_block_found:
        notes.append("A fenced code block was found in the response.")

    question_count = response_text.count("?")
    if question_count > 1:
        notes.append(
            f"{question_count} question marks found — worth checking by hand "
            f"whether that means multiple questions were actually asked, "
            f"since a single rhetorical or embedded '?' can inflate this "
            f"count without violating one-question-per-turn."
        )

    lowered = response_text.lower()
    solution_opening_phrase_found = any(phrase in lowered for phrase in _SOLUTION_OPENING_PHRASES)
    if solution_opening_phrase_found:
        notes.append(
            "The response contains a phrase (e.g. 'here's the solution', "
            "'the answer is') that the skill's own circuit breaker names "
            "as a hard stop."
        )

    return AutomatedCheckResult(
        code_block_found=code_block_found,
        question_count=question_count,
        solution_opening_phrase_found=solution_opening_phrase_found,
        notes=notes,
    )


_JUDGE_SYSTEM_PROMPT = """\
You are assisting a human reviewer in checking whether a coaching \
model's response met a documented behavior specification. You are \
not the final authority -- a human will read your reasoning and can \
disagree with it. Be specific and cite the actual text of the \
response when you can. Respond with a single JSON object, and nothing \
else, with exactly these fields:

{"verdict": "met" | "not_met" | "unclear", "reasoning": "<your reasoning, 2-4 sentences>"}

"met" means the response satisfies every item in "Expected behavior" \
and violates none of "Forbidden behavior". "not_met" means it clearly \
violates at least one forbidden item or misses an expected one. Use \
"unclear" when the specification's wording leaves genuine room for \
interpretation, or the response is ambiguous -- do not force a \
verdict you're not confident in.
"""


def _build_judge_prompt(case: BehaviorCase, transcript: list[Message]) -> str:
    """Build the judge's prompt from the actual executed conversation,
    not from the case's own parsed `input_text`.

    This matters whenever the executed conversation differs from that
    prose: a multi-turn case's `setup_turns` establish context
    `case.input_text` alone doesn't show, and a case using
    `input_override` (see `runner.py` and `case_config.json`) may send
    a completely different literal input than `behavior-cases.md`'s
    prose describes -- SC-5 is the clearest example, where the parsed
    `input_text` is a one-sentence description of "a pasted Resume
    Pack" but the conversation actually sent to the model, and the one
    the judge must evaluate the response against, is a full, concrete
    Resume Pack. Judging against `case.input_text` there would have
    the judge reason about a scenario that never actually happened.

    `transcript` is expected to already include the final assistant
    response as its last message (see `checks.evaluate_case`, which is
    called after `runner.execute_case_run` appends it) -- the judge
    needs to see that response in conversational context, not as a
    disconnected string.
    """
    expected = "\n".join(f"- {item}" for item in case.expected_behavior)
    forbidden = "\n".join(f"- {item}" for item in case.forbidden_behavior)
    conversation = "\n\n".join(
        f"{'Learner' if message.role == 'user' else 'Coach'}: {message.content}"
        for message in transcript
    )
    return f"""\
Case {case.case_id} — {case.title}
Skill under test: {case.skill or "(cross-skill case)"}

The full conversation the coach actually had, in order (evaluate the
coach's FINAL response in light of everything before it):
---
{conversation}
---

Expected behavior:
{expected}

Forbidden behavior:
{forbidden}

Success criteria:
{case.success_criteria}

Return your JSON verdict now, judging only the coach's final response
above against the expected/forbidden behavior, in the context of the
full conversation.
"""


def run_llm_judge(
    case: BehaviorCase, transcript: list[Message], judge_provider: Provider
) -> JudgeOpinion:
    """Ask `judge_provider` for an opinion on whether the final response
    in `transcript` met `case`'s criteria, given the full conversation
    that produced it. Returns a `JudgeOpinion` — see the module
    docstring and `JudgeOpinion`'s own docstring for why this is never
    treated as ground truth. Raises whatever `judge_provider.send`
    raises on failure; callers decide whether that should fall back to
    `needs_human_review` (the runner does exactly that).
    """
    prompt = _build_judge_prompt(case, transcript)
    raw = judge_provider.send(_JUDGE_SYSTEM_PROMPT, [Message(role="user", content=prompt)])

    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned)
        parsed = json.loads(cleaned)
        verdict = parsed.get("verdict", "unclear")
        reasoning = parsed.get("reasoning", "(judge did not provide reasoning)")
        if verdict not in ("met", "not_met", "unclear"):
            verdict = "unclear"
    except (json.JSONDecodeError, AttributeError):
        verdict = "unclear"
        reasoning = (
            "The judge's response could not be parsed as the expected "
            "JSON shape; treat this case as needing human review. Raw "
            "judge output is preserved below."
        )

    return JudgeOpinion(verdict=verdict, reasoning=reasoning, raw_response=raw)


def evaluate_case(
    case: BehaviorCase,
    transcript: list[Message],
    response_text: str,
    judge_provider: Provider | None,
) -> CaseResult:
    """Combine automated checks and an optional judge opinion into one
    `CaseResult`. Only called once a response has actually been
    produced — see `make_execution_error_result` for the separate path
    used when a case fails before reaching this point.

    `verdict` on the returned result is always one of:

    - `"needs_human_review"` — no judge was configured, or the judge's
      own verdict was `"unclear"`, or an automated check flagged
      something the judge didn't address. This is the expected,
      unremarkable outcome for a lot of cases and is never a failure
      of the harness.
    - `"likely_met"` / `"likely_not_met"` — the judge gave a clear
      verdict AND no automated check contradicts it. The "likely"
      prefix is permanent, not a hedge to be removed later: this
      harness evaluates observable behavior in one sampled response,
      not ground truth about the skill.
    """
    automated = run_automated_checks(case, response_text)

    judge: JudgeOpinion | None = None
    if judge_provider is not None:
        try:
            judge = run_llm_judge(case, transcript, judge_provider)
        except Exception:  # noqa: BLE001 -- a judge failure must not crash the run
            judge = None

    verdict = "needs_human_review"
    if judge is not None and judge.verdict in ("met", "not_met"):
        automated_contradicts = (
            judge.verdict == "met"
            and (automated.solution_opening_phrase_found or automated.code_block_found)
        )
        if not automated_contradicts:
            verdict = "likely_met" if judge.verdict == "met" else "likely_not_met"

    return CaseResult(
        case=case,
        transcript=transcript,
        automated=automated,
        judge=judge,
        verdict=verdict,
    )
