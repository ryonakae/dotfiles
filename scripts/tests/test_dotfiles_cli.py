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
    (self.root / 'hosts' / 'default.nix').write_text('{ username = "fixture-user"; }\n')
    (self.root / 'hosts' / 'private.nix').write_text('{ username = "private-user"; }\n')
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
    darwinConfigurations.default.system = system (import ./hosts/default.nix);
    darwinConfigurations.private.system = system (import ./hosts/private.nix);
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
    result = self.cli('build', '--configuration', 'private')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual((Path(result.stdout.strip()) / 'username').read_text(), 'private-user')

  def test_configuration_name_cannot_select_an_attribute_path(self):
    for name in ('private.config', '"default"', 'default#other', '${builtins.abort "bad"}'):
      with self.subTest(name=name):
        result = self.cli('build', '--configuration', name)
        self.assertEqual(result.returncode, 2)
        self.assertIn('configuration', result.stderr)
        self.assertEqual(result.stdout, '')

  def test_unknown_configuration_does_not_fall_back_to_default(self):
    result = self.cli('build', '--configuration', 'missing')
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('missing', result.stderr)
    self.assertEqual(result.stdout, '')

  def test_update_rejects_configuration_selection(self):
    before = (self.root / 'flake.lock').read_bytes()
    result = self.cli('update', '--configuration', 'default')
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


@unittest.skipUnless(Path(NIX).is_file(), 'Nix is required for configuration evaluation tests')
class NixConfigurationTests(unittest.TestCase):
  def evaluate(self, configuration, option):
    result = subprocess.run([
      NIX, '--extra-experimental-features', 'nix-command flakes',
      'eval', f'git+{ROOT.as_uri()}#darwinConfigurations.{configuration}.config.{option}',
      '--no-update-lock-file', '--json',
    ], cwd=ROOT, capture_output=True, text=True)
    self.assertEqual(result.returncode, 0, result.stderr)
    return json.loads(result.stdout)

  def test_both_configurations_allow_fish_for_manual_login_shell_selection(self):
    for configuration in ('default', 'private'):
      with self.subTest(configuration=configuration):
        shells = self.evaluate(configuration, 'environment.etc.shells.text')
        self.assertIn('/run/current-system/sw/bin/fish', shells.splitlines())

  def test_default_and_private_configurations_merge_their_application_sets(self):
    common_casks = {'blender', 'coteditor', 'framer'}
    private_casks = {
      'air-video-server-hd',
      'autodesk-fusion',
      'eagle',
      'freecad',
      'kicad',
      'parallels',
      'private-internet-access',
      'qmk-toolbox',
      'timemachineeditor',
    }

    default_casks = {
      cask['name'] for cask in self.evaluate('default', 'homebrew.casks')
    }
    private_configuration_casks = {
      cask['name'] for cask in self.evaluate('private', 'homebrew.casks')
    }
    default_mas_apps = self.evaluate('default', 'homebrew.masApps')
    private_mas_apps = self.evaluate('private', 'homebrew.masApps')

    self.assertTrue(common_casks <= default_casks)
    self.assertTrue(default_casks <= private_configuration_casks)
    self.assertEqual(private_configuration_casks - default_casks, private_casks)
    self.assertNotIn('CotEditor', default_mas_apps)
    self.assertEqual(
      {name: private_mas_apps.get(name) for name in default_mas_apps},
      default_mas_apps,
    )
    self.assertEqual(
      {name: app_id for name, app_id in private_mas_apps.items() if name not in default_mas_apps},
      {'EdgeView 2': 1206246482},
    )


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

  def invoke(self, *args):
    with patch('sys.argv', ['dotfiles.py', 'switch', *args]):
      self.module.main()

  def test_default_configuration_is_used_for_validation_build_and_switch(self):
    self.invoke()
    self.assert_configuration_used('default')

  def test_named_configuration_is_used_for_validation_build_and_switch(self):
    self.invoke('--configuration', 'private')
    self.assert_configuration_used('private')

  def assert_configuration_used(self, configuration):
    commands = [call.args for call in self.nix.call_args_list]
    self.assertIn(('eval', f'path:/nix/store/fixture-source#darwinConfigurations.{configuration}.config'),
                  [args[:2] for args in commands])
    self.assertIn(('build', f'path:/nix/store/fixture-source#darwinConfigurations.{configuration}.system'),
                  [args[:2] for args in commands])
    self.assertTrue(all('--no-update-lock-file' in args for args in commands))
    self.assertEqual(self.run.call_args_list[0].args[0], ['/fixture/check-hermes'])
    self.assertEqual(self.run.call_args_list[1].args[0], [
      '/usr/bin/sudo', '/nix/store/fixture-system/sw/bin/darwin-rebuild',
      'switch', '--flake', f'path:/nix/store/fixture-source#{configuration}', '--no-update-lock-file',
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


class ShellBackupTests(unittest.TestCase):
  def setUp(self):
    spec = importlib.util.spec_from_file_location('dotfiles', ROOT / 'scripts/dotfiles.py')
    self.module = importlib.util.module_from_spec(spec)
    with patch('sys.dont_write_bytecode', True):
      spec.loader.exec_module(self.module)
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.root = Path(self.directory.name)
    self.etc = self.root / 'etc'
    self.etc.mkdir()
    self.system = self.root / 'system'
    (self.system / 'etc').mkdir(parents=True)
    for name in ('bashrc', 'zshrc'):
      (self.system / 'etc' / name).symlink_to('/fixture/generated-' + name)
    self.module.ETC = self.etc
    self.activated = False
    self.real_run = subprocess.run
    self.target = {
      'username': 'fixture-user', 'homeDirectory': '/Users/fixture-user',
      'hermesCheck': '/fixture/check-hermes',
    }
    patches = [
      patch.object(self.module, 'nix', side_effect=self.nix_response),
      patch.object(self.module.os, 'geteuid', return_value=501),
      patch.object(self.module.pwd, 'getpwuid', return_value=SimpleNamespace(
        pw_name='fixture-user', pw_dir='/Users/fixture-user')),
      patch.object(self.module.sys.stdin, 'isatty', return_value=True),
      patch.dict(os.environ, {'APP_SANDBOX_CONTAINER_ID': ''}),
      patch('sys.stdout', new_callable=io.StringIO),
      patch('sys.stderr', new_callable=io.StringIO),
    ]
    for patcher in patches:
      patcher.start()
      self.addCleanup(patcher.stop)
    self.prompts = patch('builtins.input', side_effect=['switch', 'backup'])
    self.prompt = self.prompts.start()
    self.addCleanup(self.prompts.stop)
    runner = patch.object(self.module.subprocess, 'run', side_effect=self.run_command)
    self.run = runner.start()
    self.addCleanup(runner.stop)

  def nix_response(self, *args, **kwargs):
    if args[:2] == ('flake', 'metadata'):
      return {'path': '/nix/store/fixture-source'}
    if args[0] == 'eval':
      return self.target
    if args[:2] == ('flake', 'check'):
      return ''
    if args[0] == 'build':
      return [{'outputs': {'out': str(self.system)}}]
    self.fail(f'Unexpected Nix command: {args}')

  def run_command(self, command, **kwargs):
    if command == ['/fixture/check-hermes']:
      return subprocess.CompletedProcess(command, 0)
    if 'darwin-rebuild' in command[1]:
      self.activated = True
      return subprocess.CompletedProcess(command, 0)
    self.assertEqual(command[:2], ['/usr/bin/sudo', '/usr/bin/python3'])
    return self.real_run(command[1:], **kwargs)

  def invoke(self, action='switch'):
    with patch('sys.argv', ['dotfiles.py', action]):
      self.module.main()

  def test_confirmed_shell_files_are_preserved_before_activation(self):
    contents = {'bashrc': '# bash fixture\n', 'zshrc': '# zsh fixture\n'}
    for name, content in contents.items():
      (self.etc / name).write_text(content)
      (self.etc / name).chmod(0o444)
    self.invoke()
    for name, content in contents.items():
      self.assertFalse(os.path.lexists(self.etc / name))
      backup = self.etc / (name + '.before-nix-darwin')
      self.assertEqual(backup.read_text(), content)
      self.assertEqual(backup.stat().st_mode & 0o777, 0o444)
      self.assertIn(content.strip(), self.module.sys.stdout.getvalue())
    self.assertEqual(self.prompt.call_count, 2)
    self.assertTrue(self.activated)

  def test_declining_backup_preserves_active_files_and_prevents_activation(self):
    source = self.etc / 'bashrc'
    source.write_text('custom settings\n')
    self.prompt.side_effect = ['switch', 'no']
    with self.assertRaisesRegex(ValueError, 'cancelled'):
      self.invoke()
    self.assertEqual(source.read_text(), 'custom settings\n')
    self.assertFalse(os.path.lexists(str(source) + '.before-nix-darwin'))
    self.assertFalse(self.activated)

  def test_existing_backup_file_directory_or_broken_link_stops_before_any_move(self):
    for kind in ('file', 'directory', 'link'):
      with self.subTest(kind=kind):
        for name in ('bashrc', 'zshrc'):
          (self.etc / name).write_text('active\n')
        backup = self.etc / 'zshrc.before-nix-darwin'
        if kind == 'file':
          backup.write_text('previous backup\n')
        elif kind == 'directory':
          backup.mkdir()
        else:
          backup.symlink_to(self.etc / 'missing')
        with self.assertRaisesRegex(ValueError, 'Backup already exists'):
          self.invoke()
        for name in ('bashrc', 'zshrc'):
          self.assertEqual((self.etc / name).read_text(), 'active\n')
        self.assertFalse(os.path.lexists(self.etc / 'bashrc.before-nix-darwin'))
        self.assertFalse(self.activated)
        if kind == 'directory':
          backup.rmdir()
        else:
          if kind == 'file':
            self.assertEqual(backup.read_text(), 'previous backup\n')
          else:
            self.assertTrue(backup.is_symlink())
          backup.unlink()
        self.prompt.side_effect = ['switch', 'backup']

  def test_managed_links_and_previously_backed_up_files_need_no_backup_prompt(self):
    source = self.etc / 'bashrc'
    source.symlink_to(self.etc / 'static/bashrc')
    backup = self.etc / 'zshrc.before-nix-darwin'
    backup.write_text('preserved\n')
    self.invoke()
    self.assertEqual(os.readlink(source), str(self.etc / 'static/bashrc'))
    self.assertEqual(backup.read_text(), 'preserved\n')
    self.assertEqual(self.prompt.call_count, 1)
    self.assertTrue(self.activated)

  def test_unknown_link_or_directory_is_not_moved(self):
    source = self.etc / 'bashrc'
    for kind in ('link', 'directory'):
      with self.subTest(kind=kind):
        if kind == 'link':
          source.symlink_to(self.etc / 'missing')
        else:
          source.mkdir()
        with self.assertRaises(ValueError):
          self.invoke()
        self.assertTrue(os.path.lexists(source))
        self.assertFalse(os.path.lexists(str(source) + '.before-nix-darwin'))
        self.assertFalse(self.activated)
        source.unlink() if kind == 'link' else source.rmdir()
        self.prompt.side_effect = ['switch', 'backup']

  def test_backup_created_during_confirmation_is_not_overwritten(self):
    source = self.etc / 'bashrc'
    source.write_text('active\n')
    backup = self.etc / 'bashrc.before-nix-darwin'

    def confirm(prompt):
      if "'backup'" in prompt:
        backup.write_text('concurrent backup\n')
        return 'backup'
      return 'switch'

    self.prompt.side_effect = confirm
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    self.assertEqual(source.read_text(), 'active\n')
    self.assertEqual(backup.read_text(), 'concurrent backup\n')
    self.assertFalse(self.activated)

  def test_file_changed_during_confirmation_is_not_moved(self):
    source = self.etc / 'bashrc'
    source.write_text('before\n')

    def confirm(prompt):
      if "'backup'" in prompt:
        source.write_text('after\n')
        return 'backup'
      return 'switch'

    self.prompt.side_effect = confirm
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    self.assertEqual(source.read_text(), 'after\n')
    self.assertFalse(os.path.lexists(str(source) + '.before-nix-darwin'))
    self.assertFalse(self.activated)

  def test_failed_backup_prevents_activation(self):
    (self.etc / 'bashrc').write_text('active\n')

    def run(command, **kwargs):
      if command[:2] == ['/usr/bin/sudo', '/usr/bin/python3']:
        raise subprocess.CalledProcessError(1, command)
      return self.run_command(command, **kwargs)

    self.run.side_effect = run
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    self.assertEqual((self.etc / 'bashrc').read_text(), 'active\n')
    self.assertFalse(self.activated)

  def test_late_source_replacement_is_preserved_and_blocks_activation(self):
    source = self.etc / 'bashrc'
    source.write_text('approved\n')

    def run(command, **kwargs):
      if command[:2] != ['/usr/bin/sudo', '/usr/bin/python3']:
        return self.run_command(command, **kwargs)
      program = '''import ctypes, os
real_cdll = ctypes.CDLL
def replacing_cdll(*args, **kwargs):
  libc = real_cdll(*args, **kwargs)
  real_rename = libc.renamex_np
  def replacing_rename(source, destination, flags):
    replacement = source + b'.replacement'
    with open(replacement, 'w') as file:
      file.write('concurrent settings\\n')
    os.replace(replacement, source)
    return real_rename(source, destination, flags)
  libc.renamex_np = replacing_rename
  return libc
ctypes.CDLL = replacing_cdll
''' + command[3]
      result = self.real_run([command[1], '-c', program, command[4]],
                             capture_output=True, text=True)
      result.check_returncode()
      return result

    self.run.side_effect = run
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    copies = [p.read_text() for p in self.etc.iterdir() if p.is_file()]
    self.assertIn('concurrent settings\n', copies)
    self.assertFalse(self.activated)

  def test_backup_created_at_move_time_is_not_overwritten(self):
    source = self.etc / 'bashrc'
    source.write_text('approved\n')

    def run(command, **kwargs):
      if command[:2] != ['/usr/bin/sudo', '/usr/bin/python3']:
        return self.run_command(command, **kwargs)
      program = '''import ctypes
real_cdll = ctypes.CDLL
def racing_cdll(*args, **kwargs):
  libc = real_cdll(*args, **kwargs)
  real_rename = libc.renamex_np
  def racing_rename(source, destination, flags):
    with open(destination, 'x') as file:
      file.write('concurrent backup\\n')
    return real_rename(source, destination, flags)
  libc.renamex_np = racing_rename
  return libc
ctypes.CDLL = racing_cdll
''' + command[3]
      result = self.real_run([command[1], '-c', program, command[4]],
                             capture_output=True, text=True)
      result.check_returncode()
      return result

    self.run.side_effect = run
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    self.assertEqual(source.read_text(), 'approved\n')
    self.assertEqual((self.etc / 'bashrc.before-nix-darwin').read_text(), 'concurrent backup\n')
    self.assertFalse(self.activated)

  def test_partial_backup_failure_keeps_preserved_data_and_prevents_activation(self):
    for name in ('bashrc', 'zshrc'):
      (self.etc / name).write_text(name + '\n')
    errors = []

    def run(command, **kwargs):
      if command[:2] != ['/usr/bin/sudo', '/usr/bin/python3']:
        return self.run_command(command, **kwargs)
      program = '''import ctypes, errno
real_cdll = ctypes.CDLL
def failing_cdll(*args, **kwargs):
  libc = real_cdll(*args, **kwargs)
  real_rename = libc.renamex_np
  def failing_rename(source, destination, flags):
    if source.endswith(b'/zshrc'):
      ctypes.set_errno(errno.EIO)
      return -1
    return real_rename(source, destination, flags)
  libc.renamex_np = failing_rename
  return libc
ctypes.CDLL = failing_cdll
''' + command[3]
      result = self.real_run([command[1], '-c', program, command[4]],
                             capture_output=True, text=True)
      errors.append(result.stderr)
      result.check_returncode()
      return result

    self.run.side_effect = run
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    self.assertFalse(os.path.lexists(self.etc / 'bashrc'))
    self.assertEqual((self.etc / 'bashrc.before-nix-darwin').read_text(), 'bashrc\n')
    self.assertEqual((self.etc / 'zshrc').read_text(), 'zshrc\n')
    self.assertFalse(os.path.lexists(self.etc / 'zshrc.before-nix-darwin'))
    self.assertIn('Inspect both paths before retrying', errors[0])
    self.assertFalse(self.activated)

  def test_failed_service_check_does_not_back_up_shell_files(self):
    source = self.etc / 'bashrc'
    source.write_text('active\n')
    self.run.side_effect = subprocess.CalledProcessError(1, ['/fixture/check-hermes'])
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    self.assertEqual(source.read_text(), 'active\n')
    self.assertFalse(os.path.lexists(str(source) + '.before-nix-darwin'))
    self.assertFalse(self.activated)

  def test_build_does_not_prompt_or_change_shell_files(self):
    source = self.etc / 'bashrc'
    source.write_text('active\n')
    self.invoke('build')
    self.assertEqual(source.read_text(), 'active\n')
    self.assertFalse(os.path.lexists(str(source) + '.before-nix-darwin'))
    self.prompt.assert_not_called()
    self.run.assert_not_called()

  def test_files_not_managed_by_candidate_are_untouched(self):
    (self.system / 'etc/bashrc').unlink()
    source = self.etc / 'bashrc'
    source.write_text('not managed\n')
    self.invoke()
    self.assertEqual(source.read_text(), 'not managed\n')
    self.assertEqual(self.prompt.call_count, 1)
    self.assertTrue(self.activated)


if __name__ == '__main__':
  unittest.main()
