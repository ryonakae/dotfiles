import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'scripts/macos-settings.sh'


class MacOSSettingsTests(unittest.TestCase):
  def setUp(self):
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.base = Path(self.directory.name)
    self.log = self.base / 'commands.jsonl'
    sudo = self.base / 'sudo'
    sudo.write_text('#!/usr/bin/env python3\n'
                    'import json, os, sys\n'
                    'with open(os.environ["COMMAND_LOG"], "a") as f:\n'
                    '  f.write(json.dumps(sys.argv[1:]) + "\\n")\n'
                    'if "-getRestartPowerFailure" in sys.argv:\n'
                    '  print(os.environ.get("POWER_SUPPORT", "Restart After Power Failure: On"))\n'
                    'sys.exit(int(os.environ.get("SUDO_EXIT", "0")))\n')
    sudo.chmod(0o755)
    self.env = dict(os.environ, PATH=str(self.base) + ':' + os.environ['PATH'],
                    COMMAND_LOG=str(self.log))

  def run_profile(self, *profiles, answer='apply\n'):
    return subprocess.run(['/bin/bash', str(SCRIPT), *profiles], env=self.env,
                          input=answer, text=True, capture_output=True, timeout=10)

  def commands(self):
    return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

  def test_work_applies_distinct_battery_and_charger_settings(self):
    result = self.run_profile('work')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(self.commands(), [
      ['-n', '/usr/bin/pmset', '-a', 'lowpowermode', '0'],
      ['-n', '/usr/bin/pmset', '-b', 'lessbright', '1', 'displaysleep', '2', 'disksleep', '0', 'womp', '0'],
      ['-n', '/usr/bin/pmset', '-c', 'sleep', '0', 'displaysleep', '20', 'disksleep', '10', 'womp', '1'],
    ])

  def test_private_preserves_desktop_power_settings(self):
    result = self.run_profile('private')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(self.commands(), [
      ['-n', '/usr/sbin/systemsetup', '-getRestartPowerFailure'],
      ['-n', '/usr/sbin/systemsetup', '-setRestartPowerFailure', 'on'],
      ['-n', '/usr/sbin/systemsetup', '-setComputerSleep', 'never'],
      ['-n', '/usr/sbin/systemsetup', '-setDisplaySleep', '20'],
      ['-n', '/usr/sbin/systemsetup', '-setHardDiskSleep', 'never'],
      ['-n', '/usr/sbin/systemsetup', '-setAllowPowerButtonToSleepComputer', 'off'],
    ])

  def test_private_refuses_unsupported_restart_after_power_failure(self):
    self.env['POWER_SUPPORT'] = 'Not supported on this machine'
    result = self.run_profile('private')
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual(self.commands(), [
      ['-n', '/usr/sbin/systemsetup', '-getRestartPowerFailure'],
    ])

  def test_cancelled_confirmation_and_invalid_profiles_make_no_changes(self):
    for profiles, answer in [(('private',), 'no\n'), (('unknown',), 'apply\n'),
                             ((), 'apply\n'), (('default', 'work'), 'apply\n')]:
      with self.subTest(profiles=profiles, answer=answer):
        result = self.run_profile(*profiles, answer=answer)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.commands(), [])

  def test_preapproved_profile_applies_without_prompt(self):
    result = self.run_profile('work', '--yes', answer='')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertNotIn("Type 'apply'", result.stdout + result.stderr)
    self.assertTrue(self.commands())

  def test_default_does_not_apply_power_overrides(self):
    result = self.run_profile('default', answer='')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(self.commands(), [])

  def test_privilege_failure_stops_remaining_changes(self):
    self.env['SUDO_EXIT'] = '1'
    result = self.run_profile('work')
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual(len(self.commands()), 1)


class MacOSDefaultsTests(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.macos = tomllib.loads((ROOT / 'mise.default.toml').read_text())['bootstrap']['macos']

  def test_preference_types_are_preserved(self):
    defaults = self.macos['defaults']
    self.assertIs(type(defaults['com.apple.dock']['autohide-delay']), float)
    self.assertIs(type(defaults['NSGlobalDomain']['KeyRepeat']), int)
    self.assertIs(defaults['NSGlobalDomain']['ApplePressAndHoldEnabled'], False)
    self.assertEqual(defaults['NSGlobalDomain']['AppleLanguages'], ['ja-JP', 'en-JP'])
    self.assertEqual(defaults['com.apple.finder']['NewWindowTarget'], 'PfHm')

  def test_dock_preserves_nested_file_dictionaries(self):
    dock = self.macos['defaults']['com.apple.dock']
    self.assertEqual(dock['persistent-apps'][0]['tile-data']['file-data'], {
      '_CFURLString': '/Applications/Spark Desktop.app', '_CFURLStringType': 0,
    })
    self.assertEqual(dock['persistent-others'][0]['tile-type'], 'directory-tile')
    self.assertEqual(dock['persistent-others'][0]['tile-data']['file-data'], {
      '_CFURLString': 'file:///Applications', '_CFURLStringType': 15,
    })

  def test_control_center_preferences_remain_current_host(self):
    self.assertEqual([e for e in self.macos['defaults_entries'] if e['domain'] == 'com.apple.controlcenter'], [
      {'domain': 'com.apple.controlcenter', 'key': 'BatteryShowPercentage', 'host': 'current', 'value': True},
      {'domain': 'com.apple.controlcenter', 'key': 'Sound', 'host': 'current', 'value': 18},
    ])


if __name__ == '__main__':
  unittest.main()
