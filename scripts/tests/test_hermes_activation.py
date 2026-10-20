import os
from pathlib import Path
import plistlib
import shlex
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'scripts/hermes_plists.py'
ADAPTER = ROOT / 'config/.local/libexec/hermes-gui-launchctl/launchctl'


class HermesActivationTests(unittest.TestCase):
  def setUp(self):
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.root = Path(self.directory.name)
    self.home = self.root / 'home with spaces'
    self.home.mkdir()
    self.plists = self.home / 'Library/LaunchAgents'
    self.service_log = self.root / 'service-operations'
    self.bin = self.root / 'bin'
    self.bin.mkdir()
    for name in ['launchctl', 'ps', 'hermes']:
      stub = self.bin / name
      stub.write_text('#!/bin/sh\nprintf forbidden >> "$SERVICE_LOG"\nexit 99\n')
      stub.chmod(0o755)
    self.env = dict(os.environ, HOME=str(self.home), SERVICE_LOG=str(self.service_log),
                    PATH=str(self.bin) + ':/usr/bin:/bin')

  def run_cli(self, answer='y\n', *arguments, prefix=None):
    command = [sys.executable, str(CLI), *arguments]
    if prefix:
      command = [sys.executable, '-c', prefix, str(CLI), *arguments]
    result = subprocess.run(command, env=self.env, cwd=self.root, input=answer,
                            capture_output=True, text=True, timeout=15)
    self.assertFalse(self.service_log.exists())
    return result

  def populate(self):
    result = self.run_cli()
    self.assertEqual(result.returncode, 0, result.stderr)

  def test_first_install_places_user_owned_regular_files_with_service_contract(self):
    self.populate()
    self.assertEqual(sorted(p.name for p in self.plists.iterdir()), ['ai.hermes.gateway.plist'])
    for name in ['gateway']:
      with self.subTest(service=name):
        path = self.plists / f'ai.hermes.{name}.plist'
        self.assertFalse(path.is_symlink())
        self.assertEqual(path.stat().st_uid, os.getuid())
        definition = plistlib.loads(path.read_bytes())
        self.assertEqual(definition['Label'], f'ai.hermes.{name}')
        self.assertEqual(definition['ProgramArguments'],
                         [str(self.home / f'.config/agent-safehouse/safe-hermes-{name}.sh')])
        self.assertEqual(definition['WorkingDirectory'], str(self.home / '.hermes'))
        self.assertIs(definition['Disabled'], True)
        self.assertIs(definition['RunAtLoad'], True)
        self.assertIs(definition['KeepAlive'], True)
        self.assertEqual(definition['StandardOutPath'], str(self.home / f'.hermes/logs/{name}.log'))
        self.assertEqual(definition['StandardErrorPath'], str(self.home / f'.hermes/logs/{name}.error.log'))
        environment = definition['EnvironmentVariables']
        self.assertEqual(environment['HOME'], str(self.home))
        self.assertEqual(environment['HERMES_HOME'], str(self.home / '.hermes'))
        self.assertEqual(environment['PATH'].split(':'), [
          str(self.home / '.local/bin'), str(self.home / '.local/share/mise/shims'),
          '/usr/bin', '/bin', '/usr/sbin', '/sbin', '/opt/homebrew/bin', '/usr/local/bin',
        ])
    self.assertFalse((self.home / '.hermes').exists())

  def test_identical_definitions_are_noop_without_confirmation(self):
    self.populate()
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_ino)
              for p in self.plists.iterdir()}
    result = self.run_cli(answer='')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_ino)
                             for p in self.plists.iterdir()})

  def test_placement_requires_confirmation_and_replaces_only_approved_changes(self):
    for answer in ['n\n', '\n', '']:
      with self.subTest(answer=answer):
        result = self.run_cli(answer=answer)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.plists.exists())
    self.populate()
    gateway = self.plists / 'ai.hermes.gateway.plist'
    expected = gateway.read_bytes()
    gateway.write_text('manual configuration')
    for answer in ['n\n', '']:
      result = self.run_cli(answer=answer)
      self.assertNotEqual(result.returncode, 0)
      self.assertEqual(gateway.read_text(), 'manual configuration')
    result = self.run_cli()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn('Replace differing', result.stdout)
    self.assertEqual(gateway.read_bytes(), expected)

  def test_symlinks_and_nonregular_files_are_rejected_even_with_confirmation(self):
    self.populate()
    gateway = self.plists / 'ai.hermes.gateway.plist'
    copied = self.root / 'matching.plist'
    copied.write_bytes(gateway.read_bytes())
    gateway.unlink()
    for kind in ['matching symlink', 'dangling symlink', 'directory']:
      with self.subTest(kind=kind):
        if kind == 'directory':
          gateway.mkdir()
        else:
          gateway.symlink_to(copied if kind == 'matching symlink' else self.root / 'missing')
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        if kind == 'directory':
          self.assertTrue(gateway.is_dir())
          gateway.rmdir()
        else:
          self.assertTrue(gateway.is_symlink())
          self.assertIn('symlink', result.stderr)
          gateway.unlink()

  def test_nonowner_definitions_are_rejected_even_when_contents_match(self):
    self.populate()
    before = {p.name: p.read_bytes() for p in self.plists.iterdir()}
    prefix = ('import os, pathlib, runpy, stat, sys\n'
              'original_lstat = pathlib.Path.lstat\n'
              'def file_lstat(path, *args, **kwargs):\n'
              '  info = original_lstat(path, *args, **kwargs)\n'
              '  if path.name == "ai.hermes.gateway.plist":\n'
              '    fields = list(info)\n'
              '    fields[stat.ST_UID] += 1\n'
              '    return os.stat_result(fields)\n'
              '  return info\n'
              'pathlib.Path.lstat = file_lstat\n'
              'sys.argv = sys.argv[1:]\n'
              'runpy.run_path(sys.argv[0], run_name="__main__")\n')
    result = self.run_cli(prefix=prefix)
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('user-owned', result.stderr)
    self.assertIn('ai.hermes.gateway.plist', result.stderr)
    self.assertEqual(before, {p.name: p.read_bytes() for p in self.plists.iterdir()})

  def test_comparison_failure_stops_before_any_definition_is_written(self):
    self.populate()
    gateway = self.plists / 'ai.hermes.gateway.plist'
    gateway.write_text('manual configuration')
    gateway.chmod(0o000)
    try:
      result = self.run_cli()
      self.assertNotEqual(result.returncode, 0)
    finally:
      gateway.chmod(0o644)
    self.assertEqual(gateway.read_text(), 'manual configuration')

  def test_symlinked_parent_directories_are_not_followed(self):
    library = self.home / 'Library'
    external = self.root / 'external library'
    external.mkdir()
    library.symlink_to(external, target_is_directory=True)
    result = self.run_cli()
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('symlink', result.stderr)
    self.assertFalse((external / 'LaunchAgents').exists())

  def test_definition_changed_during_confirmation_is_preserved(self):
    self.populate()
    gateway = self.plists / 'ai.hermes.gateway.plist'
    gateway.write_text('reviewed configuration')
    prefix = ('import builtins, os, pathlib, runpy, sys\n'
              'def confirm(prompt):\n'
              '  path = pathlib.Path(os.environ["HOME"]) / "Library/LaunchAgents/ai.hermes.gateway.plist"\n'
              '  path.write_text("changed after review")\n'
              '  return "y"\n'
              'builtins.input = confirm\n'
              'sys.argv = sys.argv[1:]\n'
              'runpy.run_path(sys.argv[0], run_name="__main__")\n')
    result = self.run_cli(prefix=prefix)
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('changed during confirmation', result.stderr)
    self.assertEqual(gateway.read_text(), 'changed after review')

  def test_approved_readonly_user_owned_file_can_be_replaced(self):
    self.populate()
    gateway = self.plists / 'ai.hermes.gateway.plist'
    expected = gateway.read_bytes()
    gateway.write_text('reviewed readonly configuration')
    gateway.chmod(0o444)
    result = self.run_cli()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(gateway.read_bytes(), expected)
    self.assertFalse(gateway.is_symlink())

  def test_gui_adapter_cannot_mutate_user_or_unrelated_jobs(self):
    launchctl = self.root / 'launchctl'
    launchctl.write_text('#!/bin/bash\nprintf "%s\\n" "$*" >> "$NATIVE_LOG"\nexit "${QUERY_EXIT:-113}"\n')
    launchctl.chmod(0o755)
    adapter = self.root / 'native-launchctl'
    adapter.write_text(ADAPTER.read_text().replace('/bin/launchctl', shlex.quote(str(launchctl))))
    adapter.chmod(0o755)
    log = self.root / 'native-queries'
    domain = f'gui/{os.getuid()}'
    for arguments, expected in [
      ([], 1), (['managername'], 0), (['print', f'user/{os.getuid()}/ai.hermes.gateway'], 113),
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


if __name__ == '__main__':
  unittest.main()
