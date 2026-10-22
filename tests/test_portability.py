"""Configuration and diagnostic fixtures are synthetic; no app queries."""

from contextlib import ExitStack, redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import plistlib
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import things_readonly as adapter


class ConfigTests(unittest.TestCase):
    def load(self, text):
        path = Mock()
        path.open.return_value = io.StringIO(text)
        return adapter.load_config(path)

    def test_example_and_no_config(self):
        self.assertEqual(adapter.load_config()["default_limit"], 30)
        example = Path(__file__).resolve().parents[1] / "config.example.ini"
        self.assertEqual(adapter.load_config(example), {"default_limit": 10, "expected_app_version": ""})

    def test_invalid_or_unknown_settings_fail_without_echoing_values(self):
        cases = ["[adapter]\ndefault_limit=51", "[adapter]\ndefault_limit=0",
                 "[adapter]\ndefault_limit=invalid", "[adapter]\ncredential=SYNTHETIC_SECRET",
                 "[adapter]\nexpected_app_version=SYNTHETIC_SECRET /path",
                 "[DEFAULT]\ndefault_limit=1\n[adapter]\n", "[unknown]\n", "x" * 16385,
                 "[adapter]\ndefault_limit=2\ndefault_limit=3"]
        for text in cases:
            with self.subTest(text=text[:40]), self.assertRaises(adapter.AdapterError) as caught:
                self.load(text)
            self.assertNotIn("SYNTHETIC_SECRET", str(caught.exception))
        path = Mock()
        path.open.side_effect = PermissionError("SYNTHETIC_PRIVATE_PATH")
        with self.assertRaises(adapter.AdapterError) as caught:
            adapter.load_config(path)
        self.assertNotIn("SYNTHETIC_PRIVATE_PATH", str(caught.exception))

    def test_cli_overrides_config_limit(self):
        for extra, expected in (([], 7), (["--limit", "2"], 2)):
            with patch.object(adapter, "load_config", return_value={"default_limit": 7, "expected_app_version": "3.24"}), \
                    patch.object(adapter, "check_environment") as environment, \
                    patch.object(adapter, "read_page", return_value={}) as reader, redirect_stdout(io.StringIO()):
                self.assertEqual(adapter.main(["--list", "inbox"] + extra), 0)
                self.assertEqual(reader.call_args.args[0].limit, expected)
                environment.assert_called_once_with("3.24")

    def test_version_mismatch_stops_before_read(self):
        with patch.object(adapter, "check_environment", side_effect=adapter.AdapterError("version mismatch")), \
                patch.object(adapter, "read_page") as reader, redirect_stderr(io.StringIO()):
            self.assertEqual(adapter.main(["--list", "today"]), 1)
            reader.assert_not_called()

    def test_installed_version_comparison_uses_only_bundle_metadata(self):
        info = {"CFBundleIdentifier": adapter.BUNDLE_ID, "CFBundleExecutable": "Things3",
                "CFBundleShortVersionString": "3.24.1"}
        for expected, mismatch in (("3.24.1", False), ("99.0", True)):
            with patch.object(adapter.platform, "system", return_value="Darwin"), \
                    patch.object(adapter.Path, "is_file", return_value=True), \
                    patch.object(adapter.Path, "open", return_value=io.BytesIO(plistlib.dumps(info))), \
                    patch.object(adapter.subprocess, "run") as runner:
                if mismatch:
                    with self.assertRaisesRegex(adapter.AdapterError, "no read performed"):
                        adapter.check_environment(expected)
                else:
                    self.assertEqual(adapter.check_environment(expected), "3.24.1")
                runner.assert_not_called()


class DiagnosticTests(unittest.TestCase):
    def fixtures(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(adapter.platform, "system", return_value="Darwin"))
        stack.enter_context(patch.object(adapter.Path, "is_file", return_value=True))
        stack.enter_context(patch.object(adapter.os, "access", return_value=True))
        stack.enter_context(patch.object(adapter, "check_environment", return_value="3.24"))
        return {"default_limit": 10, "expected_app_version": ""}

    def response(self, registered=True):
        return SimpleNamespace(returncode=0, stdout=json.dumps({"standard_app_registered": registered,
                               "visible_running_instances": 0}), stderr="")

    def test_success_checks_registration_without_launching_or_task_events(self):
        settings = self.fixtures()
        runner = Mock(return_value=self.response())
        report = adapter.diagnose(settings, runner)
        self.assertTrue(report["prerequisites_met"])
        self.assertEqual(report["apple_events_access"], "not_probed")
        self.assertEqual(report["live_task_reads"], "not_probed")
        self.assertEqual(report["checks"]["installed_app"]["version_source"], "Info.plist")
        runner.assert_called_once()
        self.assertEqual(runner.call_args.args[0], ["/usr/bin/osascript", "-l", "JavaScript", "-e", adapter.DISCOVERY_SCRIPT])
        self.assertEqual(runner.call_args.kwargs["timeout"], 10)
        self.assertNotIn("shell", runner.call_args.kwargs)
        for disallowed in ("Application(", "tell application", "launchApplication", "openURL", "to dos", "setValue"):
            self.assertNotIn(disallowed, adapter.DISCOVERY_SCRIPT)

    def test_discovery_and_expected_version_fail_clearly(self):
        settings = self.fixtures()
        for registered, version in ((False, ""), (True, "99.0")):
            with self.subTest(registered=registered, version=version):
                settings["expected_app_version"] = version
                report = adapter.diagnose(settings, Mock(return_value=self.response(registered)))
                self.assertFalse(report["prerequisites_met"])

    def test_probe_failures_suppressed_without_retry(self):
        settings = self.fixtures()
        cases = [SimpleNamespace(returncode=1, stdout="", stderr="SYNTHETIC_PRIVATE_VALUE (-1743)"),
                 SimpleNamespace(returncode=0, stdout="SYNTHETIC_PRIVATE_VALUE", stderr=""),
                 subprocess.TimeoutExpired("synthetic", 10)]
        for case in cases:
            runner = Mock(side_effect=case) if isinstance(case, Exception) else Mock(return_value=case)
            report = adapter.diagnose(settings, runner)
            self.assertFalse(report["prerequisites_met"])
            self.assertNotIn("SYNTHETIC_PRIVATE_VALUE", json.dumps(report))
            self.assertEqual(runner.call_count, 1)

    def test_unsupported_platform_does_not_spawn_process(self):
        runner = Mock()
        with patch.object(adapter.platform, "system", return_value="Linux"):
            report = adapter.diagnose(adapter.load_config(), runner)
        self.assertFalse(report["prerequisites_met"])
        runner.assert_not_called()

    def test_doctor_main_never_calls_task_reader(self):
        for ready in (False, True):
            with patch.object(adapter, "diagnose", return_value={"prerequisites_met": ready}), \
                    patch.object(adapter, "read_page") as reader, redirect_stdout(io.StringIO()):
                self.assertEqual(adapter.main(["--doctor"]), 0 if ready else 1)
                reader.assert_not_called()


if __name__ == "__main__":
    unittest.main()
