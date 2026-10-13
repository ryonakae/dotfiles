import json
import os
from pathlib import Path
import plistlib
import re
import shlex
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
    native_source = home + '.home.file.".local/libexec/hermes-gui-launchctl/launchctl".source'
    result = subprocess.run(
      [NIX, 'build', source, native_source, '--no-link', '--no-update-lock-file'],
      cwd=ROOT, capture_output=True, text=True, timeout=120)
    if result.returncode:
      raise AssertionError(result.stderr)
    cls.native_path = evaluate(native_source)
    cls.native_text = Path(cls.native_path).read_text()
    cls.check_path = evaluate(source)
    cls.check_text = Path(cls.check_path).read_text()
    cls.home_path = evaluate(home + '.home.homeDirectory')
    extra = evaluate(home + '.home.extraBuilderCommands')
    cls.definitions = re.search(r'ln -s (\S+) \$out/hermes-launch-agents', extra).group(1)
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
    self.service_log = self.root / 'service-operations'
    self.launchctl = self.root / 'launchctl'
    self.launchctl.write_text('#!/bin/bash\nprintf "%s\\n" "$*" >> "$SERVICE_LOG"\n'
                             'if [[ "$1" == managername ]]; then echo Background;\n'
                             'elif [[ "$1" == print ]]; then echo "ai.hermes.gateway running";\n'
                             'else exit 99; fi\n')
    self.launchctl.chmod(0o755)
    self.ps = self.root / 'ps'
    self.ps.write_text('#!/bin/bash\necho ps >> "$SERVICE_LOG"\necho "hermes gateway run"\n')
    self.ps.chmod(0o755)
    self.check = self.root / 'check-activation'
    self.check.write_text(self.render(self.check_text))
    self.check.chmod(0o755)
    self.env = dict(os.environ, HOME=str(self.home), SERVICE_LOG=str(self.service_log))

  def render(self, text):
    return (text.replace(self.home_path, str(self.home))
            .replace(self.definitions, str(self.candidates))
            .replace('/bin/launchctl', shlex.quote(str(self.launchctl)))
            .replace('/bin/ps', shlex.quote(str(self.ps)))
            .replace(self.check_path, str(self.check)))

  def populate(self):
    for source in self.candidates.glob('*.plist'):
      shutil.copyfile(source, self.plists / source.name)

  def run_phase(self, text, **environment):
    script = 'set -euo pipefail\nrun() { "$@"; }\nerrorEcho() { echo "$@" >&2; }\n' + self.render(text)
    return subprocess.run(['/bin/bash', '-c', script], env=dict(self.env, **environment),
                          capture_output=True, text=True, timeout=15)

  def test_only_gateway_is_automatically_restarted(self):
    for name, expected in [('gateway', True), ('dashboard', False)]:
      with self.subTest(service=name):
        definition = plistlib.loads((self.candidates / f'ai.hermes.{name}.plist').read_bytes())
        self.assertIs(definition['KeepAlive'], expected)

  def test_dashboard_bind_is_fixed_in_plist_without_changing_gateway_environment(self):
    dashboard = plistlib.loads((self.candidates / 'ai.hermes.dashboard.plist').read_bytes())
    self.assertEqual(dashboard['EnvironmentVariables']['HERMES_DASHBOARD_HOST'], '0.0.0.0')
    self.assertEqual(dashboard['EnvironmentVariables']['HERMES_DASHBOARD_PORT'], '9120')
    gateway = plistlib.loads((self.candidates / 'ai.hermes.gateway.plist').read_bytes())
    self.assertNotIn('HERMES_DASHBOARD_HOST', gateway['EnvironmentVariables'])
    self.assertNotIn('HERMES_DASHBOARD_PORT', gateway['EnvironmentVariables'])

  def test_generated_native_launchctl_adapter_cannot_mutate_user_or_unrelated_jobs(self):
    log = self.root / 'native-queries'
    launchctl = self.root / 'launchctl'
    launchctl.write_text('#!/bin/bash\nprintf "%s\\n" "$*" >> "$NATIVE_LOG"\nexit 113\n')
    launchctl.chmod(0o755)
    adapter = self.root / 'native-launchctl'
    adapter.write_text(self.native_text.replace('/bin/launchctl', shlex.quote(str(launchctl))))
    adapter.chmod(Path(self.native_path).stat().st_mode)
    domain = f'gui/{os.getuid()}'
    for arguments, expected in [
      (['managername'], 0), (['print', f'user/{os.getuid()}/ai.hermes.gateway'], 113),
      (['bootout', f'user/{os.getuid()}/ai.hermes.gateway'], 1),
      (['bootout', f'{domain}/ai.hermes.dashboard'], 1), (['list'], 1),
      (['bootstrap', domain, 'anything.plist'], 1),
      (['bootout', f'{domain}/ai.hermes.gateway'], 0),
    ]:
      with self.subTest(arguments=arguments):
        result = subprocess.run([str(adapter), *arguments],
                                env=dict(self.env, NATIVE_LOG=str(log)),
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, expected, result.stderr)
    self.assertEqual(log.read_text().splitlines(), [f'print {domain}/ai.hermes.gateway'])

  def test_unchanged_definitions_skip_reinstallation(self):
    self.populate()
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.plists.iterdir()}
    self.assertEqual(self.metadata['hermesCheck'], self.check_path)
    for phase in [self.check_text, self.before, self.install]:
      result = self.run_phase(phase)
      self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse(self.service_log.exists())
    self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.plists.iterdir()})

  def test_changed_definition_is_installed_without_stopping_running_services(self):
    self.populate()
    old = self.root / 'old-generation'
    shutil.copytree(self.plists, old / 'hermes-launch-agents')
    candidate = self.candidates / 'ai.hermes.gateway.plist'
    candidate.write_text(candidate.read_text().replace('safe-hermes-gateway.sh', 'changed-wrapper.sh'))
    for phase in [self.check_text, self.before, self.install]:
      result = self.run_phase(phase, oldGenPath=str(old))
      self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual((self.plists / candidate.name).read_bytes(), candidate.read_bytes())
    self.assertFalse(self.service_log.exists())

  def test_only_changed_definition_is_reinstalled(self):
    self.populate()
    old = self.root / 'old-generation'
    shutil.copytree(self.plists, old / 'hermes-launch-agents')
    dashboard = self.plists / 'ai.hermes.dashboard.plist'
    timestamp = dashboard.stat().st_mtime_ns
    candidate = self.candidates / 'ai.hermes.gateway.plist'
    candidate.write_text(candidate.read_text().replace('safe-hermes-gateway.sh', 'changed-wrapper.sh'))
    for phase in [self.before, self.install]:
      result = self.run_phase(phase, oldGenPath=str(old))
      self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual((self.plists / candidate.name).read_bytes(), candidate.read_bytes())
    self.assertEqual(dashboard.stat().st_mtime_ns, timestamp)

  def test_first_install_does_not_depend_on_gui_or_process_state(self):
    result = self.run_phase(self.check_text)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(list(self.plists.iterdir()), [])
    for phase in [self.before, self.install]:
      result = self.run_phase(phase)
      self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(len(list(self.plists.glob('*.plist'))), 2)
    self.assertFalse(self.service_log.exists())

  def test_manual_modification_is_not_overwritten(self):
    self.populate()
    gateway = self.plists / 'ai.hermes.gateway.plist'
    gateway.write_text('manual configuration')
    result = self.run_phase(self.before)
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
    self.assertFalse(self.service_log.exists())

  def test_comparison_error_is_not_treated_as_a_change(self):
    self.populate()
    (self.candidates / 'ai.hermes.gateway.plist').unlink()
    result = self.run_phase(self.check_text)
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('cannot compare', result.stderr)
    self.assertFalse(self.service_log.exists())


if __name__ == '__main__':
  unittest.main()
