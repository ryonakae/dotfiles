import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
NIX = shutil.which('nix') or '/nix/var/nix/profiles/default/bin/nix'


class ShellEntrypointTests(unittest.TestCase):
  def test_cli_starts_without_path_python_from_repo_or_another_project(self):
    with tempfile.TemporaryDirectory() as directory:
      project = Path(directory) / 'other project'
      project.mkdir()
      (project / '.python-version').write_text('unavailable-python\n')
      shims = Path(directory) / 'shims'
      shims.mkdir()
      python = shims / 'python3'
      python.write_text('#!/bin/sh\nprintf "mise Python is unavailable\\n" >&2\nexit 127\n')
      python.chmod(0o755)
      env = dict(os.environ, PATH=f'{shims}:/usr/bin:/bin')
      for cwd in (ROOT, project):
        with self.subTest(cwd=cwd):
          result = subprocess.run(
            ['/bin/bash', str(ROOT / 'scripts/dotfiles.sh'), '--help'],
            cwd=cwd, env=env, capture_output=True, text=True,
          )
          self.assertEqual(result.returncode, 0, result.stderr)
          self.assertIn('Build, apply, or update the locked macOS configuration', result.stdout)
          self.assertIn('--configuration', result.stdout)
          self.assertEqual(result.stderr, '')


@unittest.skipUnless(Path(NIX).is_file(), 'Nix is required for CLI integration tests')
class DotfilesCliTests(unittest.TestCase):
  def setUp(self):
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.root = Path(self.directory.name) / 'repo'
    self.root.mkdir()
    (self.root / 'scripts').mkdir()
    for name in ('dotfiles.sh', 'dotfiles.py'):
      shutil.copy(ROOT / 'scripts' / name, self.root / 'scripts' / name)
    for name in ('hosts', 'public', 'replacement'):
      (self.root / name).mkdir()
      (self.root / name / 'value').write_text(name)
    (self.root / 'hosts' / 'mac.nix').write_text('{ username = "fixture-user"; }\n')
    (self.root / 'hosts' / 'work.nix').write_text('{ username = "work-user"; }\n')
    (self.root / 'flake.nix').write_text('''{
  inputs.public = { url = "path:./public"; flake = false; };
  outputs = { self, public }: let
    system = host: builtins.derivation {
      name = "dotfiles-cli-test";
      system = "aarch64-darwin";
      builder = "/bin/sh";
      args = [ "-c" ''
        /bin/mkdir -p "$out"
        printf '%s' '${host.username}' > "$out/username"
        printf '%s' '${self}' > "$out/source"
      '' ];
    };
  in {
    darwinConfigurations.mac.system = system (import ./hosts/mac.nix);
    darwinConfigurations."work-mac".system = system (import ./hosts/work.nix);
  };
}
''')
    self.env = dict(os.environ, PATH=str(Path(NIX).parent) + ':' + os.environ['PATH'])
    self.command('git', 'init', '--quiet')
    self.command('git', 'add', '.')
    self.command(NIX, '--extra-experimental-features', 'nix-command flakes',
                 'flake', 'lock', str(self.root))
    self.command('git', 'add', 'flake.lock')

  def command(self, *args):
    return subprocess.run(args, cwd=self.root, env=self.env,
                          capture_output=True, text=True, check=True)

  def cli(self, *args):
    return subprocess.run(['/bin/bash', str(self.root / 'scripts/dotfiles.sh'),
                           *args], cwd=self.root, env=self.env,
                          capture_output=True, text=True)

  def test_build_uses_tracked_nix_host_without_changing_lock_or_importing_untracked_files(self):
    lock = (self.root / 'flake.lock').read_bytes()
    (self.root / 'untracked-secret.txt').write_text('DUMMY_SECRET=not-a-real-secret\n')
    result = self.cli('build')
    self.assertEqual(result.returncode, 0, result.stderr)
    output = Path(result.stdout.strip())
    self.assertEqual((output / 'username').read_text(), 'fixture-user')
    self.assertEqual((self.root / 'flake.lock').read_bytes(), lock)
    self.assertFalse((Path((output / 'source').read_text()) / 'untracked-secret.txt').exists())

  def test_explicit_configuration_uses_the_named_host(self):
    result = self.cli('build', '--configuration', 'work-mac')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual((Path(result.stdout.strip()) / 'username').read_text(), 'work-user')

  def test_configuration_name_cannot_select_an_attribute_path(self):
    for name in ('work.mac', '"mac"', 'mac#other', '${builtins.abort "bad"}'):
      with self.subTest(name=name):
        result = self.cli('build', '--configuration', name)
        self.assertEqual(result.returncode, 2)
        self.assertIn('configuration', result.stderr)
        self.assertEqual(result.stdout, '')

  def test_unknown_configuration_does_not_fall_back_to_mac(self):
    result = self.cli('build', '--configuration', 'missing')
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('missing', result.stderr)
    self.assertEqual(result.stdout, '')

  def test_update_rejects_configuration_selection(self):
    before = (self.root / 'flake.lock').read_bytes()
    result = self.cli('update', '--configuration', 'mac')
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual((self.root / 'flake.lock').read_bytes(), before)

  def test_changed_public_url_requires_explicit_update(self):
    lock = (self.root / 'flake.lock').read_bytes()
    flake = self.root / 'flake.nix'
    flake.write_text(flake.read_text().replace('path:./public', 'path:./replacement'))
    result = self.cli('build')
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('lock', result.stderr.lower())
    self.assertEqual((self.root / 'flake.lock').read_bytes(), lock)

  def test_missing_public_lock_entry_requires_explicit_update(self):
    lockfile = self.root / 'flake.lock'
    lock = json.loads(lockfile.read_text())
    del lock['nodes']['public']
    del lock['nodes']['root']['inputs']['public']
    lockfile.write_text(json.dumps(lock))
    before = lockfile.read_bytes()
    result = self.cli('build')
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('lock', result.stderr.lower())
    self.assertEqual(lockfile.read_bytes(), before)

  def test_explicit_update_repairs_changed_public_input_without_building(self):
    flake = self.root / 'flake.nix'
    flake.write_text(flake.read_text().replace('path:./public', 'path:./replacement'))
    result = self.cli('update', 'public')
    self.assertEqual(result.returncode, 0, result.stderr)
    lock = json.loads((self.root / 'flake.lock').read_text())
    self.assertEqual(lock['nodes']['public']['original']['path'], './replacement')
    self.assertNotIn('/nix/store/', result.stdout)


class SwitchSafetyTests(unittest.TestCase):
  def setUp(self):
    spec = importlib.util.spec_from_file_location('dotfiles', ROOT / 'scripts/dotfiles.py')
    self.module = importlib.util.module_from_spec(spec)
    with patch('sys.dont_write_bytecode', True):
      spec.loader.exec_module(self.module)
    self.target = {
      'username': 'fixture-user',
      'homeDirectory': '/Users/fixture-user',
      'hermesCheck': '/fixture/check-hermes',
    }
    self.nix = self.patch('nix', side_effect=self.nix_response)
    self.run = self.patch('subprocess.run')
    self.patch('os.geteuid', return_value=501)
    self.patch('os.getuid', return_value=501)
    self.patch('os.path.lexists', return_value=False)
    self.patch('pwd.getpwuid', return_value=SimpleNamespace(
      pw_name='fixture-user', pw_dir='/Users/fixture-user'))
    self.patch('sys.stdin.isatty', return_value=True)
    self.patch('sys.stdout', new_callable=io.StringIO)
    self.patch('sys.stderr', new_callable=io.StringIO)
    env = patch.dict(os.environ, {'APP_SANDBOX_CONTAINER_ID': ''})
    env.start()
    self.addCleanup(env.stop)
    prompt = patch('builtins.input', return_value='switch')
    self.prompt = prompt.start()
    self.addCleanup(prompt.stop)

  def patch(self, name, **kwargs):
    owner = self.module
    *parents, attribute = name.split('.')
    for parent in parents:
      owner = getattr(owner, parent)
    patcher = patch.object(owner, attribute, **kwargs)
    result = patcher.start()
    self.addCleanup(patcher.stop)
    return result

  def nix_response(self, *args, **kwargs):
    if args[:2] == ('flake', 'metadata'):
      return {'path': '/nix/store/fixture-source'}
    if args[0] == 'eval':
      return self.target
    if args[0] == 'build':
      return [{'outputs': {'out': '/nix/store/fixture-system'}}]
    if args[:2] == ('flake', 'check'):
      return ''
    self.fail(f'Unexpected Nix command: {args}')

  def invoke(self):
    with patch('sys.argv', ['dotfiles.py', 'switch', '--configuration', 'work-mac']):
      self.module.main()

  def test_named_configuration_is_used_for_validation_build_and_switch(self):
    self.invoke()
    commands = [call.args for call in self.nix.call_args_list]
    self.assertIn(('eval', 'path:/nix/store/fixture-source#darwinConfigurations.work-mac.config'),
                  [args[:2] for args in commands])
    self.assertIn(('build', 'path:/nix/store/fixture-source#darwinConfigurations.work-mac.system'),
                  [args[:2] for args in commands])
    self.assertTrue(all('--no-update-lock-file' in args for args in commands))
    self.assertEqual(self.run.call_args_list[0].args[0], ['/fixture/check-hermes'])
    self.assertEqual(self.run.call_args_list[1].args[0], [
      '/usr/bin/sudo', '/nix/store/fixture-system/sw/bin/darwin-rebuild',
      'switch', '--flake', 'path:/nix/store/fixture-source#work-mac', '--no-update-lock-file',
    ])
    self.assertEqual(self.run.call_count, 2)

  def test_root_is_rejected_before_nix_or_activation(self):
    self.module.os.geteuid.return_value = 0
    self.assert_rejected_before_nix()

  def test_safehouse_is_rejected_before_nix_or_activation(self):
    with patch.dict(os.environ, {'APP_SANDBOX_CONTAINER_ID': 'agent-safehouse'}):
      self.assert_rejected_before_nix()

  def test_noninteractive_switch_is_rejected_before_nix_or_activation(self):
    self.module.sys.stdin.isatty.return_value = False
    self.assert_rejected_before_nix()

  def assert_rejected_before_nix(self):
    with self.assertRaises(SystemExit) as error:
      self.invoke()
    self.assertEqual(error.exception.code, 2)
    self.nix.assert_not_called()
    self.run.assert_not_called()

  def test_target_user_or_home_mismatch_prevents_build_and_activation(self):
    for field, value in (('username', 'other-user'), ('homeDirectory', '/Users/other-user')):
      with self.subTest(field=field):
        before = self.target[field]
        self.target[field] = value
        self.nix.reset_mock()
        with self.assertRaisesRegex(ValueError, 'configured user'):
          self.invoke()
        self.assertNotIn('build', [call.args[0] for call in self.nix.call_args_list])
        self.run.assert_not_called()
        self.target[field] = before

  def test_cancelled_confirmation_does_not_run_service_check_or_activation(self):
    self.prompt.return_value = ''
    with self.assertRaisesRegex(ValueError, 'cancelled'):
      self.invoke()
    self.run.assert_not_called()

  def test_failed_service_check_prevents_activation(self):
    self.run.side_effect = subprocess.CalledProcessError(1, ['/fixture/check-hermes'])
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    self.assertEqual(self.run.call_count, 1)
    self.assertEqual(self.run.call_args.args[0], ['/fixture/check-hermes'])


if __name__ == '__main__':
  unittest.main()
