#!/usr/bin/env python3
"""Structural validator for the Agent Skills in this repository.

Checks, per skill directory under `skills/`:

  * the directory contains a `SKILL.md` file,
  * `SKILL.md` begins with YAML-style frontmatter (`---` ... `---`),
  * the frontmatter has non-empty `name` and `description` fields,
  * `name` exactly matches the directory name,
  * `name` uses only lowercase letters, digits, and hyphens,
  * `name` is no more than `MAX_NAME_LENGTH` (64) characters,
  * `description` is no more than `MAX_DESCRIPTION_LENGTH` (1024)
    characters,
  * the frontmatter block contains no duplicate keys (a duplicate key
    is reported as a readable error instead of silently overwriting
    the earlier value),
  * no two skills share the same `name`,
  * no obsolete flat `skills/*.md` files exist alongside the
    directories,
  * every skill directory expected after this repository's current
    round of work actually exists,
  * every `SKILL.md` (and every other Markdown file scanned) is valid
    UTF-8,
  * relative Markdown-to-Markdown links across the repository point at
    files that actually exist, where that can be reasonably detected.

Exits 0 if everything passes, 1 otherwise, printing one readable error
per problem found, each naming the offending file.

## Limitations of the frontmatter parser

This script does **not** use a real YAML parser — the repository has
no dependency on one, and pulling one in for a handful of two-field
blocks would be more machinery than the task warrants. Instead it uses
a minimal line-based parser that:

  * only understands simple `key: value` pairs at the top level of the
    frontmatter block,
  * does not understand multi-line values, nested mappings, lists,
    quoted strings with embedded colons, or YAML anchors/aliases,
  * takes the value as everything after the first `: ` on the line,
    trimmed of surrounding whitespace and a single layer of matching
    quotes.

This is sufficient for this repository's `SKILL.md` frontmatter, which
is intentionally just `name:` and `description:`. If frontmatter ever
grows more complex, switch to a real YAML library instead of extending
this parser.

## Limitations of the link checker

The link checker only looks for Markdown inline links
(`[text](path)`) whose `path` is relative (does not start with a URL
scheme like `http://` or `https://`, and is not a bare `#anchor`). It
resolves the path relative to the Markdown file containing the link,
strips any trailing `#anchor`, and checks the result exists on disk.
It does not validate the anchor itself, does not follow reference-style
links (`[text][ref]`), and does not check links inside code blocks
(a link-shaped string inside a fenced code example will still be
checked, which is usually the desired behavior for this repository but
worth knowing about).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXPECTED_SKILLS = {
    "dsa-tutor",
    "problem-decoder",
    "dry-run-coach",
    "complexity-coach",
    "mock-interviewer",
    "debug-coach",
    "test-case-coach",
    "pattern-transfer-coach",
    "code-review-coach",
}

MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


class ValidationError(Exception):
    """Raised for a single, readable validation failure."""


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"{path}: not valid UTF-8 ({exc})") from exc


def parse_frontmatter(path: Path, text: str) -> dict:
    """Parse a minimal `---`-delimited frontmatter block.

    See the module docstring for the documented limitations of this
    parser. Returns a dict of the fields found.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValidationError(
            f"{path}: does not begin with YAML-style frontmatter "
            f"(expected the first line to be '---')"
        )

    fields: dict[str, str] = {}
    closed = False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            raise ValidationError(
                f"{path}: frontmatter line is not a 'key: value' pair: "
                f"{line!r}"
            )
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key in fields:
            raise ValidationError(
                f"{path}: duplicate frontmatter key '{key}' (first value "
                f"{fields[key]!r}, repeated value {value!r}) — each key "
                f"must appear at most once"
            )
        fields[key] = value

    if not closed:
        raise ValidationError(
            f"{path}: frontmatter block is never closed with a second "
            f"'---' line"
        )

    return fields


def validate_skill_directory(skill_dir: Path, seen_names: dict) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.is_file():
        errors.append(f"{skill_dir}: missing SKILL.md")
        return errors

    try:
        text = read_utf8(skill_md)
    except ValidationError as exc:
        errors.append(str(exc))
        return errors

    try:
        fields = parse_frontmatter(skill_md, text)
    except ValidationError as exc:
        errors.append(str(exc))
        return errors

    for required in ("name", "description"):
        if required not in fields:
            errors.append(f"{skill_md}: frontmatter is missing '{required}'")
        elif not fields[required].strip():
            errors.append(f"{skill_md}: '{required}' is empty")

    description = fields.get("description", "").strip()
    if description and len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"{skill_md}: 'description' is {len(description)} characters, "
            f"exceeding the {MAX_DESCRIPTION_LENGTH}-character limit"
        )

    name = fields.get("name", "").strip()
    if name:
        if name != skill_dir.name:
            errors.append(
                f"{skill_md}: frontmatter name '{name}' does not match "
                f"its parent directory '{skill_dir.name}'"
            )
        if len(name) > MAX_NAME_LENGTH:
            errors.append(
                f"{skill_md}: name '{name}' is {len(name)} characters, "
                f"exceeding the {MAX_NAME_LENGTH}-character limit"
            )
        if not NAME_PATTERN.match(name):
            errors.append(
                f"{skill_md}: name '{name}' must use only lowercase "
                f"letters, digits, and hyphens (no leading/trailing/"
                f"double hyphens)"
            )
        if name in seen_names:
            errors.append(
                f"{skill_md}: duplicate skill name '{name}', already "
                f"used by {seen_names[name]}"
            )
        else:
            seen_names[name] = skill_md

    return errors


def find_obsolete_flat_skill_files(skills_root: Path) -> list[str]:
    errors = []
    if not skills_root.is_dir():
        return errors
    for entry in sorted(skills_root.iterdir()):
        if entry.is_file() and entry.suffix == ".md":
            errors.append(
                f"{entry}: obsolete flat skill file directly under "
                f"'{skills_root.name}/' — skills must live in their own "
                f"directory as '{skills_root.name}/<name>/SKILL.md'"
            )
    return errors


def check_expected_skills_present(skills_root: Path) -> list[str]:
    errors = []
    if not skills_root.is_dir():
        return [f"{skills_root}: directory does not exist"]
    present = {
        entry.name
        for entry in skills_root.iterdir()
        if entry.is_dir() and (entry / "SKILL.md").is_file()
    }
    missing = EXPECTED_SKILLS - present
    for name in sorted(missing):
        errors.append(
            f"{skills_root}: expected skill directory '{name}' is "
            f"missing"
        )
    return errors


def check_relative_markdown_links(repo_root: Path) -> list[str]:
    errors = []
    md_files = sorted(repo_root.rglob("*.md"))
    for md_file in md_files:
        if ".git" in md_file.parts:
            continue
        try:
            text = read_utf8(md_file)
        except ValidationError as exc:
            errors.append(str(exc))
            continue

        for match in LINK_PATTERN.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("#"):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            resolved = (md_file.parent / target_path).resolve()
            if not resolved.exists():
                errors.append(
                    f"{md_file}: links to '{target}', which does not "
                    f"resolve to an existing file ({resolved})"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the structure of this repository's Agent Skills "
            "(skills/*/SKILL.md) and cross-check relative Markdown "
            "links across the repository."
        )
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to validate (default: current directory)",
    )
    parser.add_argument(
        "--skip-link-check",
        action="store_true",
        help="Skip the relative Markdown link check (skill-only run)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.root).resolve()
    skills_root = repo_root / "skills"

    all_errors: list[str] = []

    all_errors.extend(find_obsolete_flat_skill_files(skills_root))
    all_errors.extend(check_expected_skills_present(skills_root))

    seen_names: dict = {}
    if skills_root.is_dir():
        for entry in sorted(skills_root.iterdir()):
            if entry.is_dir():
                all_errors.extend(validate_skill_directory(entry, seen_names))

    if not args.skip_link_check:
        all_errors.extend(check_relative_markdown_links(repo_root))

    if all_errors:
        print(f"Found {len(all_errors)} problem(s):\n", file=sys.stderr)
        for error in all_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    skill_count = len(seen_names)
    print(f"OK: {skill_count} skill(s) validated, no problems found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
