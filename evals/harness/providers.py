#!/usr/bin/env python3
"""Model provider abstraction for the behavior-evaluation runner.

Every provider implements the same tiny interface:

    class Provider:
        def send(self, system_prompt: str, messages: list[Message]) -> str: ...

`messages` is the full conversation so far (setup turns plus the
case's own input), each a `{"role": "user" | "assistant", "content":
str}` dict; `send` returns the next assistant reply as plain text.
That's the entire contract. Nothing else in this package (the runner,
the checks, the report writer) knows or cares which provider produced
a reply, which is what keeps a second provider a matter of adding one
more class here rather than touching `runner.py`.

## Providers in this file

- `MockProvider` — returns pre-scripted or fixture-loaded replies.
  Used by the test suite and by anyone who wants to see the harness's
  full pipeline (case selection, transcript recording, checks, report
  generation) run end to end with zero network access and zero cost.
  This is also what `--live` intentionally does *not* use — see
  `AnthropicProvider` below.
- `AnthropicProvider` — calls the real Anthropic API. Isolated in its
  own class with its own optional import (`anthropic`) so that nothing
  else in `scripts/`, `tests/`, or this package needs that dependency
  installed, or an API key set, to run. Constructing this class
  without the `anthropic` package installed, or without an API key
  available, raises `ProviderConfigurationError` with a clear message
  rather than a bare `ImportError` or `KeyError` deep in a stack trace.

## Adding a provider

Implement `send`, register a name in `PROVIDERS` at the bottom of this
file, and nothing else in the harness needs to change. Keep any
provider-specific SDK import inside that provider's own module-level
`try`/`except` or inside `__init__`, not at the top of this file, so
importing `providers` never requires every provider's SDK to be
installed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Message:
    """One turn in a conversation. `role` is 'user' or 'assistant'."""

    role: str
    content: str

    def __post_init__(self) -> None:
        if self.role not in ("user", "assistant"):
            raise ValueError(f"Message.role must be 'user' or 'assistant', got {self.role!r}")


class ProviderConfigurationError(RuntimeError):
    """Raised when a provider can't be constructed (missing SDK, missing key, etc.)."""


class Provider(Protocol):
    """The interface every provider implements."""

    def send(self, system_prompt: str, messages: list[Message]) -> str:
        """Return the next assistant reply given a system prompt and history."""
        ...


class MockProvider:
    """A provider that never calls a network.

    Two modes:

    - Scripted: constructed with `responses`, a list of strings
      returned in order, one per call to `send`. Raises `IndexError`
      with a clear message if `send` is called more times than there
      are scripted responses — a test that runs out of script is a
      test that's wrong about how many turns it needs, not a case for
      silently returning something.
    - Fixture-loaded: constructed with `responses_by_case`, a dict
      mapping a case id to its scripted response list, and `case_id`
      telling this instance which list to use. This is what the
      runner uses for `--fixtures`, so a whole suite of mocked
      responses can live in one JSON file (see `fixtures/` and
      `run_eval.py --fixtures`).
    """

    def __init__(
        self,
        responses: list[str] | None = None,
        *,
        responses_by_case: dict[str, list[str]] | None = None,
        case_id: str | None = None,
    ) -> None:
        if responses is not None and responses_by_case is not None:
            raise ValueError("pass either responses or responses_by_case, not both")
        if responses_by_case is not None:
            if case_id is None:
                raise ValueError("case_id is required when using responses_by_case")
            if case_id not in responses_by_case:
                raise ProviderConfigurationError(
                    f"no fixture responses found for case '{case_id}'"
                )
            self._responses = list(responses_by_case[case_id])
        else:
            self._responses = list(responses or [])
        self._call_count = 0

    def send(self, system_prompt: str, messages: list[Message]) -> str:
        if self._call_count >= len(self._responses):
            raise IndexError(
                f"MockProvider ran out of scripted responses after "
                f"{self._call_count} call(s) — the case needs more turns "
                f"than were scripted, or the runner made an unexpected "
                f"extra call"
            )
        response = self._responses[self._call_count]
        self._call_count += 1
        return response


class AnthropicProvider:
    """Calls the real Anthropic API. Requires the `anthropic` package and
    an API key (via the `api_key` argument or the `ANTHROPIC_API_KEY`
    environment variable). Never logs or persists the key.
    """

    def __init__(self, model: str, api_key: str | None = None) -> None:
        try:
            import anthropic  # noqa: F401  (import kept local — see module docstring)
        except ImportError as exc:
            raise ProviderConfigurationError(
                "the 'anthropic' package is not installed. Set up a virtual "
                "environment and install it there, e.g.:\n"
                "    python3 -m venv .venv\n"
                "    source .venv/bin/activate\n"
                "    pip install anthropic\n"
                "(on Windows, activate with '.venv\\Scripts\\activate' instead), "
                "or omit --live to use fixtures instead."
            ) from exc

        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise ProviderConfigurationError(
                "no API key found. Set the ANTHROPIC_API_KEY environment "
                "variable, or pass --api-key. Never commit an API key to "
                "this repository."
            )

        self._client = anthropic.Anthropic(api_key=resolved_key)
        self._model = model

    def send(self, system_prompt: str, messages: list[Message]) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        text_blocks = [block.text for block in response.content if block.type == "text"]
        return "\n".join(text_blocks)


PROVIDERS = {
    "mock": MockProvider,
    "anthropic": AnthropicProvider,
}
