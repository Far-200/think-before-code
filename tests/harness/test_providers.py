"""Tests for `evals/harness/providers.py`.

`MockProvider` is what every other test in this suite runs against —
these tests protect its own scripted/fixture-driven behavior directly.
`AnthropicProvider` is tested only for its configuration-error paths
(missing package, missing key): actually calling the live API is
outside the scope of a unit test that must run without network access
or a paid API key, per this repository's existing testing philosophy.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "evals" / "harness"))

import providers  # noqa: E402  (path set up above)


class MessageTests(unittest.TestCase):
    def test_valid_roles_construct(self) -> None:
        providers.Message(role="user", content="hi")
        providers.Message(role="assistant", content="hi")

    def test_invalid_role_raises(self) -> None:
        with self.assertRaises(ValueError):
            providers.Message(role="system", content="hi")


class MockProviderScriptedTests(unittest.TestCase):
    def test_returns_responses_in_order(self) -> None:
        provider = providers.MockProvider(responses=["first", "second"])
        self.assertEqual(provider.send("system", []), "first")
        self.assertEqual(provider.send("system", []), "second")

    def test_running_out_of_script_raises_index_error(self) -> None:
        provider = providers.MockProvider(responses=["only one"])
        provider.send("system", [])
        with self.assertRaises(IndexError):
            provider.send("system", [])

    def test_no_responses_defaults_to_empty_script(self) -> None:
        provider = providers.MockProvider()
        with self.assertRaises(IndexError):
            provider.send("system", [])


class MockProviderFixtureTests(unittest.TestCase):
    def test_selects_responses_for_case_id(self) -> None:
        provider = providers.MockProvider(
            responses_by_case={"DT-1": ["response a"], "DT-2": ["response b"]},
            case_id="DT-2",
        )
        self.assertEqual(provider.send("system", []), "response b")

    def test_missing_case_id_in_fixtures_raises_configuration_error(self) -> None:
        with self.assertRaises(providers.ProviderConfigurationError):
            providers.MockProvider(responses_by_case={"DT-1": ["x"]}, case_id="DT-99")

    def test_case_id_required_with_responses_by_case(self) -> None:
        with self.assertRaises(ValueError):
            providers.MockProvider(responses_by_case={"DT-1": ["x"]})

    def test_both_responses_and_responses_by_case_rejected(self) -> None:
        with self.assertRaises(ValueError):
            providers.MockProvider(
                responses=["x"], responses_by_case={"DT-1": ["x"]}, case_id="DT-1"
            )


class AnthropicProviderConfigurationTests(unittest.TestCase):
    def test_missing_package_raises_configuration_error(self) -> None:
        with mock.patch.dict(sys.modules, {"anthropic": None}):
            with self.assertRaises(providers.ProviderConfigurationError) as ctx:
                providers.AnthropicProvider(model="claude-sonnet-4-6", api_key="sk-test")
            self.assertIn("anthropic", str(ctx.exception).lower())

    def test_missing_package_error_recommends_a_virtual_environment(self) -> None:
        """Regression test for finding 3: the installation guidance in
        this error message must point at a virtual environment, not
        at installing into the system Python via --break-system-packages."""
        with mock.patch.dict(sys.modules, {"anthropic": None}):
            with self.assertRaises(providers.ProviderConfigurationError) as ctx:
                providers.AnthropicProvider(model="claude-sonnet-4-6", api_key="sk-test")
            message = str(ctx.exception)
            self.assertIn("venv", message)
            self.assertNotIn("--break-system-packages", message)

    def test_missing_api_key_raises_configuration_error(self) -> None:
        fake_anthropic = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            with mock.patch.dict("os.environ", {}, clear=True):
                with self.assertRaises(providers.ProviderConfigurationError) as ctx:
                    providers.AnthropicProvider(model="claude-sonnet-4-6", api_key=None)
                self.assertIn("api key", str(ctx.exception).lower())

    def test_api_key_from_environment_is_used(self) -> None:
        fake_anthropic = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-from-env"}):
                providers.AnthropicProvider(model="claude-sonnet-4-6")
                fake_anthropic.Anthropic.assert_called_once_with(api_key="sk-from-env")

    def test_explicit_api_key_overrides_environment(self) -> None:
        fake_anthropic = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-from-env"}):
                providers.AnthropicProvider(model="claude-sonnet-4-6", api_key="sk-explicit")
                fake_anthropic.Anthropic.assert_called_once_with(api_key="sk-explicit")

    def test_send_extracts_text_blocks(self) -> None:
        fake_anthropic = mock.MagicMock()
        fake_client = mock.MagicMock()
        fake_anthropic.Anthropic.return_value = fake_client

        text_block = mock.MagicMock()
        text_block.type = "text"
        text_block.text = "the reply"
        fake_response = mock.MagicMock()
        fake_response.content = [text_block]
        fake_client.messages.create.return_value = fake_response

        with mock.patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            provider = providers.AnthropicProvider(model="claude-sonnet-4-6", api_key="sk-test")
            result = provider.send("system prompt", [providers.Message(role="user", content="hi")])

        self.assertEqual(result, "the reply")
        fake_client.messages.create.assert_called_once()
        _, kwargs = fake_client.messages.create.call_args
        self.assertEqual(kwargs["system"], "system prompt")
        self.assertEqual(kwargs["messages"], [{"role": "user", "content": "hi"}])


class ProviderRegistryTests(unittest.TestCase):
    def test_mock_and_anthropic_are_registered(self) -> None:
        self.assertIn("mock", providers.PROVIDERS)
        self.assertIn("anthropic", providers.PROVIDERS)
        self.assertIs(providers.PROVIDERS["mock"], providers.MockProvider)
        self.assertIs(providers.PROVIDERS["anthropic"], providers.AnthropicProvider)


if __name__ == "__main__":
    unittest.main()
