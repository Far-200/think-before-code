"""Unit tests for `evals/harness/`, the behavior-evaluation runner.

This file exists so that `python -m unittest discover`, run from the
repository root, recurses into `tests/harness/` — plain directories
are skipped by discovery, packages are not, matching the convention
already used by `tests/__init__.py`.

Every test in this package runs against mocked or fixture-based data
and makes no network calls — see `evals/harness/providers.py`'s
`MockProvider` and the fixtures under `evals/harness/fixtures/`.
"""
