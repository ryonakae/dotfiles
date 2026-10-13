import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
NIX = shutil.which('nix')


@unittest.skipUnless(NIX, 'Nix is required for generated Hermes activation tests')
class HermesActivationTests(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    prefix = f'git+{ROOT.as_uri()}#darwinConfigurations.private.config'
    home = prefix + '.home-manager.users."ryo.nakae"'

    def evaluate(attribute):
      result = subprocess.run(
        [NIX, 'eval', attribute, '--json', '--no-update-lock-file'],
        cwd=ROOT, capture_output=True, text=True, timeout=60)
      if result.returncode:
        raise AssertionError(result.stderr)
      return json.loads(result.stdout)

    source = home + '.xdg.configFile."hermes/check-activation.sh".source'
    result = subprocess.run(
      [NIX, 'build', source, '--no-link', '--no-update-lock-file'],
      cwd=ROOT, capture_output=True, text=True, timeout=120)
    if result.returncode:
      raise AssertionError(result.stderr)
    cls.check_path = evaluate(source)
    cls.check_text = Path(cls.check_path).read_text()
    cls.home_path = evaluate(home + '.home.homeDirectory')
    extra = evaluate(home + '.home.extraBuilderCommands')
    cls.definitions = re.search(r'ln -s (\S+) \$out/hermes-launch-agents', extra).group(1)
    cls.stop_path = evaluate(home + '.xdg.configFile."hermes/check-stopped.sh".source')
    cls.before = evaluate(home + '.home.activation.checkHermesServices.data')
    cls.install = evaluate(home + '.home.activation.installHermesPlists.data')
    cls.metadata = json.loads(evaluate(prefix + '.environment.etc."dotfiles/build.json".text'))

  def setUp(self):
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.root = Path(self.directory.name)
    self.home = self.root / 'home'
    self.plists = self.home / 'Library/LaunchAgents'
    self.plists.mkdir(parents=True)
    self.candidates = self.root / 'candidates'
    self.candidates.mkdir()
    for source in Path(self.definitions).glob('*.plist'):
      shutil.copyfile(source, self.candidates / source.name)
    self.stop_log = self.root / 'stop-checks'
    self.stop = self.root / 'check-stopped'
    self.stop.write_text('#!/bin/bash\nprintf checked >> "$STOP_LOG"\nexit "${STOP_EXIT:-0}"\n')
    self.stop.chmod(0o755)
    self.check = self.root / 'check-activation'
    self.check.write_text(self.render(self.check_text))
    self.check.chmod(0o755)
    self.env = dict(os.environ, HOME=str(self.home), STOP_LOG=str(self.stop_log), STOP_EXIT='23')

  def render(self, text):
    return (text.replace(self.home_path, str(self.home))
            .replace(self.definitions, str(self.candidates))
            .replace(self.stop_path, str(self.stop))
            .replace(self.check_path, str(self.check)))

  def populate(self):
    for source in self.candidates.glob('*.plist'):
      shutil.copyfile(source, self.plists / source.name)

  def run_phase(self, text, **environment):
    script = 'set -euo pipefail\nrun() { "$@"; }\nerrorEcho() { echo "$@" >&2; }\n' + self.render(text)
    return subprocess.run(['/bin/bash', '-c', script], env=dict(self.env, **environment),
                          capture_output=True, text=True, timeout=15)

  def test_unchanged_definitions_skip_stop_check_and_reinstallation(self):
    self.populate()
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.plists.iterdir()}
    self.assertEqual(self.metadata['hermesCheck'], self.check_path)
    for phase in [self.check_text, self.before, self.install]:
      result = self.run_phase(phase)
      self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse(self.stop_log.exists())
    self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.plists.iterdir()})

  def test_changed_definition_requires_stopped_services_before_writing(self):
    self.populate()
    gateway = self.plists / 'ai.hermes.gateway.plist'
    previous = gateway.read_bytes()
    candidate = self.candidates / gateway.name
    candidate.write_text(candidate.read_text().replace('safe-hermes-gateway.sh', 'changed-wrapper.sh'))
    for phase in [self.check_text, self.install]:
      result = self.run_phase(phase)
      self.assertEqual(result.returncode, 23, result.stderr)
      self.assertEqual(gateway.read_bytes(), previous)
    self.assertTrue(self.stop_log.exists())

  def test_stopped_services_update_only_changed_definition(self):
    self.populate()
    old = self.root / 'old-generation'
    shutil.copytree(self.plists, old / 'hermes-launch-agents')
    dashboard = self.plists / 'ai.hermes.dashboard.plist'
    timestamp = dashboard.stat().st_mtime_ns
    candidate = self.candidates / 'ai.hermes.gateway.plist'
    candidate.write_text(candidate.read_text().replace('safe-hermes-gateway.sh', 'changed-wrapper.sh'))
    for phase in [self.before, self.install]:
      result = self.run_phase(phase, STOP_EXIT='0', oldGenPath=str(old))
      self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual((self.plists / candidate.name).read_bytes(), candidate.read_bytes())
    self.assertEqual(dashboard.stat().st_mtime_ns, timestamp)

  def test_first_install_requires_stopped_services(self):
    result = self.run_phase(self.check_text)
    self.assertEqual(result.returncode, 23, result.stderr)
    self.assertEqual(list(self.plists.iterdir()), [])
    for phase in [self.before, self.install]:
      result = self.run_phase(phase, STOP_EXIT='0')
      self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(len(list(self.plists.glob('*.plist'))), 2)

  def test_manual_modification_is_not_overwritten(self):
    self.populate()
    gateway = self.plists / 'ai.hermes.gateway.plist'
    gateway.write_text('manual configuration')
    result = self.run_phase(self.before, STOP_EXIT='0')
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('Unmanaged or modified', result.stderr)
    self.assertEqual(gateway.read_text(), 'manual configuration')

  def test_symlink_is_rejected_even_when_contents_match(self):
    self.populate()
    gateway = self.plists / 'ai.hermes.gateway.plist'
    gateway.unlink()
    gateway.symlink_to(self.candidates / gateway.name)
    for phase in [self.check_text, self.before, self.install]:
      result = self.run_phase(phase)
      self.assertNotEqual(result.returncode, 0)
      self.assertIn('symlink', result.stderr)
    self.assertFalse(self.stop_log.exists())

  def test_comparison_error_is_not_treated_as_a_change(self):
    self.populate()
    (self.candidates / 'ai.hermes.gateway.plist').unlink()
    result = self.run_phase(self.check_text)
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('cannot compare', result.stderr)
    self.assertFalse(self.stop_log.exists())


if __name__ == '__main__':
  unittest.main()
