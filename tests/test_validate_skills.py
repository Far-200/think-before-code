"""Tests for `scripts/validate_skills.py`.

Each test protects a validation guarantee that a contributor would
otherwise have to rediscover by breaking CI: a skill that is missing
its `SKILL.md`, a frontmatter `name` that has drifted from its
directory, a description that has grown past the limit an agent host
will accept, a Markdown link that no longer resolves, and so on.

Fixtures are generated into a temporary directory. Nothing here reads
or writes the real repository.
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_skills  # noqa: E402  (path set up above)


VALID_DESCRIPTION = (
    "Coaches a learner through a problem without handing over the "
    "answer. Use when the learner wants to be asked questions."
)


def write_skill(
    skills_root: Path,
    directory: str,
    *,
    name: str | None = None,
    description: str | None = VALID_DESCRIPTION,
    body: str = "\nAsk one question at a time.\n",
    frontmatter: str | None = None,
) -> Path:
    """Write a `skills/<directory>/SKILL.md` fixture and return its path.

    By default the frontmatter is valid and its `name` matches the
    directory. Pass `frontmatter` to supply a raw block instead, for
    the malformed cases.
    """
    skill_dir = skills_root / directory
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"

    if frontmatter is None:
        lines = ["---"]
        if name is not None:
            lines.append(f"name: {name if name else ''}".rstrip())
        if description is not None:
            lines.append(f"description: {description}".rstrip())
        lines.append("---")
        frontmatter = "\n".join(lines)

    skill_md.write_text(frontmatter + "\n" + body, encoding="utf-8")
    return skill_md


class SkillFixtureTestCase(unittest.TestCase):
    """Base case providing a throwaway repository root."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo_root = Path(self._tmp.name)
        self.skills_root = self.repo_root / "skills"
        self.skills_root.mkdir()

    def validate_dir(self, directory: str, seen: dict | None = None) -> list[str]:
        return validate_skills.validate_skill_directory(
            self.skills_root / directory,
            {} if seen is None else seen,
        )

    def assertNoErrors(self, errors: list[str]) -> None:
        self.assertEqual(errors, [], f"expected no errors, got: {errors}")

    def assertErrorMentions(self, errors: list[str], *fragments: str) -> None:
        self.assertTrue(errors, "expected at least one error, got none")
        joined = "\n".join(errors)
        for fragment in fragments:
            self.assertIn(fragment, joined)


class ValidSkillTests(SkillFixtureTestCase):
    def test_minimal_valid_skill_passes(self):
        write_skill(self.skills_root, "dsa-tutor", name="dsa-tutor")
        self.assertNoErrors(self.validate_dir("dsa-tutor"))

    def test_description_at_the_length_limit_passes(self):
        at_limit = "x" * validate_skills.MAX_DESCRIPTION_LENGTH
        write_skill(
            self.skills_root, "dsa-tutor", name="dsa-tutor", description=at_limit
        )
        self.assertNoErrors(self.validate_dir("dsa-tutor"))

    def test_quoted_frontmatter_values_are_unwrapped(self):
        write_skill(
            self.skills_root,
            "dsa-tutor",
            frontmatter='---\nname: "dsa-tutor"\ndescription: "Coaches."\n---',
        )
        self.assertNoErrors(self.validate_dir("dsa-tutor"))


class MissingAndMalformedFileTests(SkillFixtureTestCase):
    def test_directory_without_skill_md_fails(self):
        (self.skills_root / "dsa-tutor").mkdir()
        self.assertErrorMentions(self.validate_dir("dsa-tutor"), "missing SKILL.md")

    def test_missing_frontmatter_fails(self):
        skill_dir = self.skills_root / "dsa-tutor"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "# dsa-tutor\n\nNo frontmatter here.\n", encoding="utf-8"
        )
        self.assertErrorMentions(
            self.validate_dir("dsa-tutor"), "does not begin with YAML-style frontmatter"
        )

    def test_unclosed_frontmatter_fails(self):
        write_skill(
            self.skills_root,
            "dsa-tutor",
            frontmatter="---\nname: dsa-tutor\ndescription: Coaches.",
            body="\n",
        )
        self.assertErrorMentions(self.validate_dir("dsa-tutor"), "never closed")

    def test_non_key_value_frontmatter_line_fails(self):
        write_skill(
            self.skills_root,
            "dsa-tutor",
            frontmatter="---\nname: dsa-tutor\nthis line has no colon\n---",
        )
        self.assertErrorMentions(
            self.validate_dir("dsa-tutor"), "not a 'key: value' pair"
        )

    def test_duplicate_frontmatter_key_fails(self):
        write_skill(
            self.skills_root,
            "dsa-tutor",
            frontmatter=(
                "---\nname: dsa-tutor\ndescription: First.\n"
                "description: Second.\n---"
            ),
        )
        self.assertErrorMentions(
            self.validate_dir("dsa-tutor"), "duplicate frontmatter key 'description'"
        )

    def test_invalid_utf8_fails_without_raising(self):
        skill_dir = self.skills_root / "dsa-tutor"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_bytes(b"---\nname: dsa-tutor\n\xff\xfe\n---\n")
        self.assertErrorMentions(self.validate_dir("dsa-tutor"), "not valid UTF-8")


class RequiredMetadataTests(SkillFixtureTestCase):
    def test_missing_description_fails(self):
        write_skill(
            self.skills_root, "dsa-tutor", name="dsa-tutor", description=None
        )
        self.assertErrorMentions(
            self.validate_dir("dsa-tutor"), "missing 'description'"
        )

    def test_missing_name_fails(self):
        write_skill(self.skills_root, "dsa-tutor", name=None)
        self.assertErrorMentions(self.validate_dir("dsa-tutor"), "missing 'name'")

    def test_empty_description_fails(self):
        write_skill(
            self.skills_root,
            "dsa-tutor",
            frontmatter="---\nname: dsa-tutor\ndescription:\n---",
        )
        self.assertErrorMentions(self.validate_dir("dsa-tutor"), "'description' is empty")

    def test_overlong_description_fails(self):
        too_long = "x" * (validate_skills.MAX_DESCRIPTION_LENGTH + 1)
        write_skill(
            self.skills_root, "dsa-tutor", name="dsa-tutor", description=too_long
        )
        self.assertErrorMentions(
            self.validate_dir("dsa-tutor"),
            "exceeding the 1024-character limit",
        )

    def test_overlong_name_fails(self):
        long_name = "a" * (validate_skills.MAX_NAME_LENGTH + 1)
        write_skill(self.skills_root, long_name, name=long_name)
        self.assertErrorMentions(
            self.validate_dir(long_name), "exceeding the 64-character limit"
        )


class NameRuleTests(SkillFixtureTestCase):
    def test_name_not_matching_directory_fails(self):
        write_skill(self.skills_root, "dsa-tutor", name="debug-coach")
        self.assertErrorMentions(
            self.validate_dir("dsa-tutor"), "does not match", "'dsa-tutor'"
        )

    def test_uppercase_name_fails(self):
        write_skill(self.skills_root, "DSA-Tutor", name="DSA-Tutor")
        self.assertErrorMentions(
            self.validate_dir("DSA-Tutor"), "must use only lowercase"
        )

    def test_underscore_name_fails(self):
        write_skill(self.skills_root, "dsa_tutor", name="dsa_tutor")
        self.assertErrorMentions(
            self.validate_dir("dsa_tutor"), "must use only lowercase"
        )

    def test_trailing_hyphen_name_fails(self):
        write_skill(self.skills_root, "dsa-tutor-", name="dsa-tutor-")
        self.assertErrorMentions(
            self.validate_dir("dsa-tutor-"), "must use only lowercase"
        )

    def test_duplicate_skill_name_across_directories_fails(self):
        write_skill(self.skills_root, "dsa-tutor", name="dsa-tutor")
        write_skill(self.skills_root, "dsa-tutor-copy", name="dsa-tutor")

        seen: dict = {}
        first = self.validate_dir("dsa-tutor", seen)
        second = self.validate_dir("dsa-tutor-copy", seen)

        self.assertNoErrors(first)
        self.assertErrorMentions(second, "duplicate skill name 'dsa-tutor'")


class RepositoryShapeTests(SkillFixtureTestCase):
    def test_obsolete_flat_skill_file_fails(self):
        write_skill(self.skills_root, "dsa-tutor", name="dsa-tutor")
        (self.skills_root / "dsa-tutor.md").write_text("stale\n", encoding="utf-8")
        self.assertErrorMentions(
            validate_skills.find_obsolete_flat_skill_files(self.skills_root),
            "obsolete flat skill file",
        )

    def test_directories_only_is_not_flagged_as_flat_file(self):
        write_skill(self.skills_root, "dsa-tutor", name="dsa-tutor")
        self.assertNoErrors(
            validate_skills.find_obsolete_flat_skill_files(self.skills_root)
        )

    def test_missing_expected_skill_directory_fails(self):
        write_skill(self.skills_root, "dsa-tutor", name="dsa-tutor")
        with mock.patch.object(
            validate_skills, "EXPECTED_SKILLS", {"dsa-tutor", "debug-coach"}
        ):
            errors = validate_skills.check_expected_skills_present(self.skills_root)
        self.assertErrorMentions(
            errors, "expected skill directory 'debug-coach' is missing"
        )

    def test_all_expected_skill_directories_present_passes(self):
        write_skill(self.skills_root, "dsa-tutor", name="dsa-tutor")
        with mock.patch.object(validate_skills, "EXPECTED_SKILLS", {"dsa-tutor"}):
            errors = validate_skills.check_expected_skills_present(self.skills_root)
        self.assertNoErrors(errors)

    def test_missing_skills_directory_fails(self):
        errors = validate_skills.check_expected_skills_present(
            self.repo_root / "nope"
        )
        self.assertErrorMentions(errors, "directory does not exist")


class MarkdownLinkTests(SkillFixtureTestCase):
    def test_resolvable_relative_link_passes(self):
        (self.repo_root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
        (self.repo_root / "README.md").write_text(
            "See [the changelog](./CHANGELOG.md).\n", encoding="utf-8"
        )
        self.assertNoErrors(
            validate_skills.check_relative_markdown_links(self.repo_root)
        )

    def test_broken_relative_link_fails(self):
        (self.repo_root / "README.md").write_text(
            "See [the changelog](./CHANGELOG.md).\n", encoding="utf-8"
        )
        self.assertErrorMentions(
            validate_skills.check_relative_markdown_links(self.repo_root),
            "./CHANGELOG.md",
            "does not",
        )

    def test_link_with_anchor_resolves_against_the_file(self):
        (self.repo_root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
        (self.repo_root / "README.md").write_text(
            "See [1.4.0](./CHANGELOG.md#140).\n", encoding="utf-8"
        )
        self.assertNoErrors(
            validate_skills.check_relative_markdown_links(self.repo_root)
        )

    def test_external_and_anchor_only_links_are_ignored(self):
        (self.repo_root / "README.md").write_text(
            "[site](https://example.com/missing) and [top](#heading)\n",
            encoding="utf-8",
        )
        self.assertNoErrors(
            validate_skills.check_relative_markdown_links(self.repo_root)
        )


class CommandLineTests(SkillFixtureTestCase):
    """Exercise `main()` end to end, keeping its output off the test log."""

    def setUp(self) -> None:
        super().setUp()
        quiet = contextlib.ExitStack()
        quiet.enter_context(contextlib.redirect_stdout(io.StringIO()))
        quiet.enter_context(contextlib.redirect_stderr(io.StringIO()))
        self.addCleanup(quiet.close)

    def test_main_returns_zero_for_a_valid_repository(self):
        write_skill(self.skills_root, "dsa-tutor", name="dsa-tutor")
        with mock.patch.object(validate_skills, "EXPECTED_SKILLS", {"dsa-tutor"}):
            exit_code = validate_skills.main(["--root", str(self.repo_root)])
        self.assertEqual(exit_code, 0)

    def test_main_returns_one_for_an_invalid_repository(self):
        write_skill(self.skills_root, "dsa-tutor", name="wrong-name")
        with mock.patch.object(validate_skills, "EXPECTED_SKILLS", {"dsa-tutor"}):
            exit_code = validate_skills.main(["--root", str(self.repo_root)])
        self.assertEqual(exit_code, 1)

    def test_skip_link_check_ignores_broken_links(self):
        write_skill(self.skills_root, "dsa-tutor", name="dsa-tutor")
        (self.repo_root / "README.md").write_text(
            "[gone](./missing.md)\n", encoding="utf-8"
        )
        with mock.patch.object(validate_skills, "EXPECTED_SKILLS", {"dsa-tutor"}):
            with_links = validate_skills.main(["--root", str(self.repo_root)])
            without_links = validate_skills.main(
                ["--root", str(self.repo_root), "--skip-link-check"]
            )
        self.assertEqual(with_links, 1)
        self.assertEqual(without_links, 0)


if __name__ == "__main__":
    unittest.main()
