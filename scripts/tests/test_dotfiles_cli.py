import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import threading
import time
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
    self.assertEqual(len(result.stdout.splitlines()), 1)
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

  def test_both_artifacts_embed_their_configuration_source_user_and_candidate_tools(self):
    for configuration in ('default', 'private'):
      with self.subTest(configuration=configuration):
        metadata = json.loads(self.evaluate(configuration, 'environment.etc."dotfiles/build.json".text'))
        self.assertEqual(metadata['configuration'], configuration)
        self.assertEqual(metadata['username'], self.evaluate(configuration, 'system.primaryUser'))
        self.assertEqual(metadata['homeDirectory'], self.evaluate(configuration, f'users.users."{metadata["username"]}".home'))
        self.assertTrue(metadata['source'].startswith('/nix/store/'))
        self.assertTrue((Path(metadata['source']) / 'mise.toml').is_file())
        self.assertTrue(metadata['hermesCheck'].startswith('/nix/store/'))
        self.assertTrue(metadata['mise'].startswith('/nix/store/'))
        self.assertTrue(metadata['mise'].endswith('/bin/mise'))

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
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    base = Path(self.directory.name).resolve()
    self.module.STORE = base / 'store'
    self.module.PROFILE = base / 'profile'
    self.module.CURRENT = base / 'current'
    self.system = self.module.STORE / 'fixture-system'
    (self.system / 'etc/dotfiles').mkdir(parents=True)
    (self.system / 'sw/bin').mkdir(parents=True)
    (self.system / 'systemConfig').write_text(str(self.system))
    (self.system / 'activate').write_text('#!/bin/sh\nexit 0\n')
    (self.system / 'activate').chmod(0o755)
    self.target.update(configuration='private', source=str(self.module.STORE / 'source'),
                       mise=str(self.module.STORE / 'mise/bin/mise'))
    (self.module.STORE / 'source').mkdir()
    for executable in ('nix-env', 'darwin-rebuild'):
      path = self.system / 'sw/bin' / executable
      path.write_text('#!/bin/sh\nexit 0\n')
      path.chmod(0o755)
    self.target['hermesCheck'] = str(self.module.STORE / 'check-hermes')
    for name in ('hermesCheck', 'mise'):
      path = Path(self.target[name])
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text('#!/bin/sh\nexit 0\n')
      path.chmod(0o755)
    self.save_metadata()
    self.nix = self.patch('nix', side_effect=self.nix_response)
    self.real_popen = subprocess.Popen
    self.run = self.patch('subprocess.run', side_effect=self.run_command)
    self.patch('os.geteuid', return_value=501)
    self.patch('os.getuid', return_value=501)
    self.patch('pwd.getpwuid', return_value=SimpleNamespace(
      pw_name='fixture-user', pw_dir='/Users/fixture-user'))
    self.patch('sys.stdin.isatty', return_value=True)
    self.patch('sys.stdout', new_callable=io.StringIO)
    self.patch('sys.stderr', new_callable=io.StringIO)
    env = patch.dict(os.environ, {'APP_SANDBOX_CONTAINER_ID': '', 'HOME': '/Users/fixture-user'})
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

  def save_metadata(self):
    (self.system / 'etc/dotfiles/build.json').write_text(json.dumps(self.target))

  def run_command(self, command, **kwargs):
    if len(command) > 1 and 'nix-env' in command[1]:
      self.module.PROFILE.symlink_to(self.system)
    if len(command) > 1 and 'darwin-rebuild' in command[1]:
      self.module.CURRENT.symlink_to(self.system)
    return subprocess.CompletedProcess(command, 0)

  def invoke(self, *args):
    with patch('sys.argv', ['dotfiles.py', 'switch', str(self.system), *args]):
      self.module.main()

  def test_explicit_artifact_is_applied_without_evaluation_or_build(self):
    self.invoke()
    self.nix.assert_not_called()
    commands = [call.args[0] for call in self.run.call_args_list]
    self.assertEqual(commands, [
      [self.target['hermesCheck']],
      ['/usr/bin/sudo', '-v'],
      ['/usr/bin/sudo', str(self.system / 'sw/bin/nix-env'), '-p', str(self.module.PROFILE), '--set', str(self.system)],
      ['/usr/bin/sudo', str(self.system / 'sw/bin/darwin-rebuild'), 'activate'],
    ])
    self.assertIn('Configuration: private', self.module.sys.stdout.getvalue())

  def test_missing_or_invalid_artifact_is_rejected_before_changes(self):
    for kind in ('missing', 'metadata', 'self-reference', 'executable'):
      with self.subTest(kind=kind):
        path = self.system
        if kind == 'missing':
          path = self.module.STORE / 'garbage-collected'
        elif kind == 'metadata':
          (self.system / 'etc/dotfiles/build.json').unlink()
        elif kind == 'self-reference':
          (self.system / 'systemConfig').write_text('/wrong-system')
        else:
          (self.system / 'activate').chmod(0o644)
        with patch('sys.argv', ['dotfiles.py', 'switch', str(path)]):
          with self.assertRaises((OSError, ValueError)):
            self.module.main()
        self.nix.assert_not_called()
        self.run.assert_not_called()
        self.save_metadata()
        (self.system / 'systemConfig').write_text(str(self.system))
        (self.system / 'activate').chmod(0o755)

  def test_malformed_metadata_is_rejected_before_changes(self):
    for metadata in ([], {'configuration': 42}, dict(self.target, mise='/bin/sh'),
                     dict(self.target, configuration='private.config')):
      with self.subTest(metadata=metadata):
        (self.system / 'etc/dotfiles/build.json').write_text(json.dumps(metadata))
        with self.assertRaises(ValueError):
          self.invoke()
        self.run.assert_not_called()
        self.nix.assert_not_called()

  def test_missing_artifact_and_old_configuration_syntax_are_rejected(self):
    for arguments in ([], ['--configuration', 'private']):
      with self.subTest(arguments=arguments), patch('sys.argv', ['dotfiles.py', 'switch', *arguments]):
        with self.assertRaises(SystemExit) as error:
          self.module.main()
        self.assertEqual(error.exception.code, 2)
        self.nix.assert_not_called()
        self.run.assert_not_called()

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
        self.save_metadata()
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

  def test_home_environment_mismatch_is_rejected_before_changes(self):
    with patch.dict(os.environ, {'HOME': '/Users/other'}):
      with self.assertRaisesRegex(ValueError, 'HOME'):
        self.invoke()
    self.run.assert_not_called()
    self.nix.assert_not_called()

  def test_profile_and_activation_failures_report_partial_state(self):
    for failing in ('nix-env', 'darwin-rebuild'):
      with self.subTest(failing=failing):
        def run(command, **kwargs):
          if len(command) > 1 and failing in command[1]:
            raise subprocess.CalledProcessError(7, command)
          return self.run_command(command, **kwargs)
        self.run.side_effect = run
        with self.assertRaises(subprocess.CalledProcessError) as error:
          self.invoke()
        self.assertEqual(error.exception.returncode, 7)
        self.assertFalse(self.module.CURRENT.exists())
        self.assertIn('Completed:', self.module.sys.stderr.getvalue())
        self.assertIn('current-system:', self.module.sys.stderr.getvalue())
        if self.module.PROFILE.is_symlink():
          self.module.PROFILE.unlink()

  def test_activation_success_with_wrong_current_system_is_failure(self):
    def run(command, **kwargs):
      result = self.run_command(command, **kwargs)
      if len(command) > 1 and 'darwin-rebuild' in command[1]:
        self.module.CURRENT.unlink()
        self.module.CURRENT.symlink_to(self.module.STORE / 'wrong')
      return result
    self.run.side_effect = run
    with self.assertRaisesRegex(ValueError, 'does not match'):
      self.invoke()

  def test_rebuild_symlink_is_invoked_through_candidate_not_its_realpath(self):
    rebuild = self.system / 'sw/bin/darwin-rebuild'
    executable = self.module.STORE / 'shared-rebuild'
    rebuild.rename(executable)
    rebuild.symlink_to(executable)
    self.invoke()
    self.assertEqual(self.run.call_args.args[0], ['/usr/bin/sudo', str(rebuild), 'activate'])

  def start_fake_refresh(self, code=None):
    real_popen = self.real_popen
    self.processes = []
    self.module.SUDO_REFRESH_INTERVAL = 0.01
    self.module.SUDO_REFRESH_TIMEOUT = 1
    program = 'import time; time.sleep(10)' if code is None else f'import sys; sys.exit({code})'
    def popen(command, **kwargs):
      self.assertEqual(command, ['/usr/bin/sudo', '-n', '-v'])
      self.assertEqual(kwargs, {})
      process = real_popen(['/usr/bin/python3', '-c', program])
      self.processes.append(process)
      return process
    self.patch('subprocess.Popen', side_effect=popen)

  def wait_for_refresh(self, failed=False):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
      if self.processes and (not failed or 'sudo cache refresh failed:' in self.module.sys.stderr.getvalue()):
        return
      time.sleep(0.01)
    self.fail('fake refresh did not reach expected state')

  def test_sigquit_reaps_refresh_like_other_catchable_termination_signals(self):
    self.start_fake_refresh()
    previous = signal.getsignal(signal.SIGQUIT)
    def run(command, **kwargs):
      if command[-1] == 'activate':
        self.wait_for_refresh()
        self.assertTrue(callable(signal.getsignal(signal.SIGQUIT)), 'SIGQUIT must be handled before sending it')
        os.kill(os.getpid(), signal.SIGQUIT)
      return self.run_command(command, **kwargs)
    self.run.side_effect = run
    with self.assertRaises(SystemExit) as error:
      self.invoke()
    self.assertEqual(error.exception.code, 128 + signal.SIGQUIT)
    self.assertEqual(signal.getsignal(signal.SIGQUIT), previous)
    self.assertTrue(all(p.poll() is not None for p in self.processes))

  def test_cache_refresh_failure_waits_for_activation_and_stops(self):
    self.start_fake_refresh(code=4)
    activated = []
    def run(command, **kwargs):
      if len(command) > 1 and 'darwin-rebuild' in command[1]:
        self.wait_for_refresh(failed=True)
        activated.append(True)
      return self.run_command(command, **kwargs)
    self.run.side_effect = run
    with self.assertRaisesRegex(ValueError, 'reauthentication required'):
      self.invoke()
    self.assertEqual(activated, [True])
    self.assertEqual(self.module.CURRENT.resolve(), self.system)
    self.assertTrue(all(p.poll() is not None for p in self.processes))

  def test_late_cache_failure_during_result_verification_is_not_success(self):
    self.start_fake_refresh(code=4)
    real_resolve = Path.resolve
    def resolve(path, *args, **kwargs):
      if path == self.module.CURRENT:
        self.wait_for_refresh(failed=True)
      return real_resolve(path, *args, **kwargs)
    with patch.object(Path, 'resolve', resolve):
      with self.assertRaisesRegex(ValueError, 'reauthentication required'):
        self.invoke()
    self.assertTrue(all(p.poll() is not None for p in self.processes))

  def test_cache_refresh_timeout_stops_before_activation(self):
    self.start_fake_refresh()
    self.module.SUDO_REFRESH_TIMEOUT = 0.05
    def run(command, **kwargs):
      if len(command) > 1 and 'nix-env' in command[1]:
        self.wait_for_refresh(failed=True)
      return self.run_command(command, **kwargs)
    self.run.side_effect = run
    with self.assertRaisesRegex(ValueError, 'reauthentication required'):
      self.invoke()
    self.assertFalse(self.module.CURRENT.exists())
    self.assertTrue(all(p.poll() is not None for p in self.processes))

  def test_refresh_subprocess_is_reaped_on_exit_exception_interrupt_and_signals(self):
    for ending in ('success', 'exception', 'interrupt', signal.SIGTERM, signal.SIGHUP):
      with self.subTest(ending=ending):
        self.start_fake_refresh()
        previous_handlers = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGHUP)}
        def run(command, **kwargs):
          if len(command) > 1 and 'darwin-rebuild' in command[1]:
            self.wait_for_refresh()
            if ending == 'exception':
              raise OSError('fixture activation error')
            if ending == 'interrupt':
              raise KeyboardInterrupt()
            if ending in (signal.SIGTERM, signal.SIGHUP):
              os.kill(os.getpid(), ending)
          return self.run_command(command, **kwargs)
        self.run.side_effect = run
        if ending == 'success':
          self.invoke()
        else:
          with self.assertRaises((OSError, KeyboardInterrupt, SystemExit)):
            self.invoke()
        self.assertTrue(all(p.poll() is not None for p in self.processes))
        self.assertFalse(any(t.name == 'dotfiles-sudo-refresh' for t in threading.enumerate()))
        for sig, handler in previous_handlers.items():
          self.assertEqual(signal.getsignal(sig), handler)
        for link in (self.module.PROFILE, self.module.CURRENT):
          if link.is_symlink():
            link.unlink()

  def test_authentication_failure_does_not_register_or_activate(self):
    def run(command, **kwargs):
      if command == ['/usr/bin/sudo', '-v']:
        raise subprocess.CalledProcessError(1, command)
      return self.run_command(command, **kwargs)
    self.run.side_effect = run
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    self.assertFalse(self.module.PROFILE.exists())
    self.assertFalse(self.module.CURRENT.exists())

  def test_failed_service_check_prevents_activation(self):
    self.run.side_effect = subprocess.CalledProcessError(1, ['/fixture/check-hermes'])
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    self.assertEqual(self.run.call_count, 1)
    self.assertEqual(self.run.call_args.args[0], [self.target['hermesCheck']])


class SetupTests(unittest.TestCase):
  patch = SwitchSafetyTests.patch
  save_metadata = SwitchSafetyTests.save_metadata

  def setUp(self):
    SwitchSafetyTests.setUp(self)
    self.module.ROOT = Path(self.directory.name).resolve() / 'checkout with spaces'
    self.module.ROOT.mkdir()
    self.home = Path(self.directory.name).resolve() / 'home'
    self.home.mkdir()
    self.target['homeDirectory'] = str(self.home)
    self.target['configuration'] = 'default'
    self.save_metadata()
    self.module.pwd.getpwuid.return_value.pw_dir = str(self.home)
    environment = patch.dict(os.environ, {'HOME': str(self.home)})
    environment.start()
    self.addCleanup(environment.stop)
    self.declaration = '[dotfiles]\n"~/.config/fish/config.fish" = "config/.config/fish/config.fish"\n'
    (self.module.ROOT / 'mise.toml').write_text(self.declaration)
    (Path(self.target['source']) / 'mise.toml').write_text(self.declaration)
    for name in ('.config/fish/config.fish', '.config/mise/config.base.toml'):
      source = self.module.ROOT / 'config' / name
      source.parent.mkdir(parents=True, exist_ok=True)
      source.write_text('fixture\n')
    self.module.BREW = Path(self.directory.name) / 'brew'
    self.module.BREW.write_text('#!/bin/sh\nexit 0\n')
    self.module.BREW.chmod(0o755)
    self.prompt.side_effect = ['switch', 'trust', 'apply']

  def nix_response(self, *args, **kwargs):
    if args[:2] == ('flake', 'metadata'):
      return {'path': self.target['source']}
    if args[0] == 'eval':
      return self.target
    if args[:2] == ('flake', 'check'):
      return ''
    if args[0] == 'build':
      return [{'outputs': {'out': str(self.system)}}]
    self.fail(f'Unexpected Nix command: {args}')

  def run_command(self, command, **kwargs):
    if command[0] == self.target['mise'] and command[-1] == 'apply':
      for destination, source in (('.config/fish/config.fish', '.config/fish/config.fish'),
                                  ('.config/mise/config.toml', '.config/mise/config.base.toml')):
        link = self.home / destination
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(self.module.ROOT / 'config' / source)
    return SwitchSafetyTests.run_command(self, command, **kwargs)

  def invoke(self, *args):
    with patch('sys.argv', ['dotfiles.py', 'setup', *args]):
      self.module.main()

  def test_setup_builds_once_applies_that_artifact_and_links_live_checkout(self):
    self.target['configuration'] = 'private'
    self.save_metadata()
    self.invoke('--configuration', 'private')
    self.assertEqual([c.args[0] for c in self.nix.call_args_list], ['flake', 'eval', 'flake', 'build'])
    commands = [c.args[0] for c in self.run.call_args_list]
    self.assertIn(['/usr/bin/sudo', str(self.system / 'sw/bin/darwin-rebuild'), 'activate'], commands)
    self.assertEqual(commands[-4:], [
      [self.target['mise'], '-C', str(self.module.ROOT), 'trust', str(self.module.ROOT / 'mise.toml')],
      [self.target['mise'], '-C', str(self.module.ROOT), 'dot', 'apply', '--dry-run'],
      [self.target['mise'], '-C', str(self.module.ROOT), 'dot', 'apply'],
      [self.target['mise'], '-C', str(self.home), 'install'],
    ])
    self.assertEqual(self.run.call_args_list[-3].kwargs['timeout'], 60)
    self.assertEqual(self.run.call_args_list[-1].kwargs['cwd'], self.home)
    self.assertFalse(any(t.name == 'dotfiles-sudo-refresh' for t in threading.enumerate()))
    self.assertEqual((self.home / '.config/fish/config.fish').readlink(),
                     self.module.ROOT / 'config/.config/fish/config.fish')

  def test_failed_runtime_install_preserves_placement_and_reports_install_only_resume(self):
    def run(command, **kwargs):
      if command == [self.target['mise'], '-C', str(self.home), 'install']:
        self.assertFalse(any(t.name == 'dotfiles-sudo-refresh' for t in threading.enumerate()))
        self.assertEqual((self.home / '.config/mise/config.toml').readlink(),
                         self.module.ROOT / 'config/.config/mise/config.base.toml')
        raise subprocess.CalledProcessError(12, command)
      return self.run_command(command, **kwargs)
    self.run.side_effect = run
    with self.assertRaises(subprocess.CalledProcessError) as error:
      self.invoke()
    self.assertEqual(error.exception.returncode, 12)
    self.assertIn('link verification', self.module.sys.stderr.getvalue())
    self.assertIn('Resume runtime installation only', self.module.sys.stderr.getvalue())
    self.assertNotIn('Resume with standard mise trust', self.module.sys.stderr.getvalue())
    self.assertNotIn('Setup complete:', self.module.sys.stdout.getvalue())
    self.assertEqual(sum(c.args[0][-1] == 'activate' for c in self.run.call_args_list), 1)
    self.assertEqual(sum(c.args[0][-1] == 'install' for c in self.run.call_args_list), 1)

  def test_setup_guards_run_before_snapshot_or_build(self):
    for guard in ('root', 'sandbox', 'terminal'):
      with self.subTest(guard=guard):
        self.module.os.geteuid.return_value = 0 if guard == 'root' else 501
        self.module.sys.stdin.isatty.return_value = guard != 'terminal'
        with patch.dict(os.environ, {'APP_SANDBOX_CONTAINER_ID': 'agent-safehouse' if guard == 'sandbox' else ''}):
          with self.assertRaises(SystemExit) as error:
            self.invoke()
          self.assertEqual(error.exception.code, 2)
        self.nix.assert_not_called()
        self.run.assert_not_called()

  def test_snapshot_target_mismatch_prevents_build(self):
    self.module.pwd.getpwuid.return_value.pw_name = 'other-user'
    with self.assertRaisesRegex(ValueError, 'configured user'):
      self.invoke()
    self.assertNotIn('build', [c.args[0] for c in self.nix.call_args_list])
    self.run.assert_not_called()

  def test_invalid_built_artifact_reports_completed_build_before_stopping(self):
    (self.system / 'etc/dotfiles/build.json').unlink()
    with self.assertRaisesRegex(ValueError, 'no dotfiles metadata'):
      self.invoke()
    self.run.assert_not_called()
    self.assertIn('Completed: build', self.module.sys.stderr.getvalue())

  def test_build_failure_prevents_application(self):
    def nix(*args, **kwargs):
      if args[0] == 'build':
        raise subprocess.CalledProcessError(3, ['nix', *args])
      return self.nix_response(*args, **kwargs)
    self.nix.side_effect = nix
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    self.run.assert_not_called()

  def test_declaration_changed_during_build_stops_before_switch(self):
    def nix(*args, **kwargs):
      if args[0] == 'build':
        (self.module.ROOT / 'mise.toml').write_text('changed\n')
      return self.nix_response(*args, **kwargs)
    self.nix.side_effect = nix
    with self.assertRaisesRegex(ValueError, 'changed since'):
      self.invoke()
    self.run.assert_not_called()

  def test_declaration_changed_during_trust_confirmation_is_not_trusted(self):
    def confirm(prompt):
      if "'trust'" in prompt:
        (self.module.ROOT / 'mise.toml').write_text('changed\n')
        return 'trust'
      return 'switch'
    self.prompt.side_effect = confirm
    with self.assertRaisesRegex(ValueError, 'changed since'):
      self.invoke()
    self.assertFalse(any(c.args[0][0] == self.target['mise'] for c in self.run.call_args_list))
    self.assertIn('Nix application succeeded', self.module.sys.stderr.getvalue())

  def test_cancellation_at_each_confirmation_stops_later_stages(self):
    for stage, responses, last in (
        ('switch', ['no'], None),
        ('trust', ['switch', 'no'], 'activate'),
        ('apply', ['switch', 'trust', 'no'], '--dry-run')):
      with self.subTest(stage=stage):
        self.prompt.side_effect = responses
        self.run.reset_mock()
        with self.assertRaisesRegex(ValueError, 'cancelled'):
          self.invoke()
        if last is None:
          self.run.assert_not_called()
        else:
          self.assertEqual(self.run.call_args.args[0][-1], last)
        for link in (self.module.PROFILE, self.module.CURRENT):
          if link.is_symlink():
            link.unlink()

  def test_failed_activation_prevents_all_mise_operations(self):
    def run(command, **kwargs):
      if command[-1] == 'activate':
        raise subprocess.CalledProcessError(9, command)
      return self.run_command(command, **kwargs)
    self.run.side_effect = run
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    self.assertFalse(any(c.args[0][0] == self.target['mise'] for c in self.run.call_args_list))

  def test_missing_homebrew_after_activation_prevents_trust(self):
    self.module.BREW.unlink()
    with self.assertRaisesRegex(ValueError, 'required tool missing'):
      self.invoke()
    self.assertFalse(any(c.args[0][0] == self.target['mise'] for c in self.run.call_args_list))

  def test_mise_failures_and_dry_run_timeout_stop_without_reswitch(self):
    for stage in ('trust', 'dry-run', 'timeout', 'apply'):
      with self.subTest(stage=stage):
        self.prompt.side_effect = ['switch', 'trust', 'apply']
        self.run.reset_mock()
        def run(command, **kwargs):
          if command[0] == self.target['mise']:
            self.assertFalse(any(t.name == 'dotfiles-sudo-refresh' for t in threading.enumerate()))
            operation = 'trust' if 'trust' in command else 'dry-run' if '--dry-run' in command else 'apply'
            if operation == stage or stage == 'timeout' and operation == 'dry-run':
              if stage == 'timeout':
                raise subprocess.TimeoutExpired(command, 60)
              raise subprocess.CalledProcessError(8, command)
          return self.run_command(command, **kwargs)
        self.run.side_effect = run
        with self.assertRaises((subprocess.CalledProcessError, subprocess.TimeoutExpired)):
          self.invoke()
        self.assertEqual(sum(c.args[0][-1] == 'activate' for c in self.run.call_args_list), 1)
        self.assertIn('Resume with standard mise', self.module.sys.stderr.getvalue())
        if stage != 'apply':
          self.assertFalse((self.home / '.config/fish/config.fish').exists())
        for link in (self.module.PROFILE, self.module.CURRENT):
          if link.is_symlink():
            link.unlink()

  def test_representative_link_must_link_directly_to_checkout_not_an_intermediary(self):
    def run(command, **kwargs):
      result = self.run_command(command, **kwargs)
      if command[0] == self.target['mise'] and command[-1] == 'apply':
        link = self.home / '.config/fish/config.fish'
        alias = self.home / 'indirect'
        alias.symlink_to(link.readlink())
        link.unlink()
        link.symlink_to(alias)
      return result
    self.run.side_effect = run
    with self.assertRaisesRegex(ValueError, 'live checkout'):
      self.invoke()

  def test_apply_success_with_wrong_representative_link_is_failure(self):
    def run(command, **kwargs):
      result = self.run_command(command, **kwargs)
      if command[0] == self.target['mise'] and command[-1] == 'apply':
        link = self.home / '.config/fish/config.fish'
        link.unlink()
        link.symlink_to(self.system / 'store-copy')
      return result
    self.run.side_effect = run
    with self.assertRaisesRegex(ValueError, 'live checkout'):
      self.invoke()
    self.assertIn('mise apply', self.module.sys.stderr.getvalue())
    self.assertFalse(any(c.args[0][-1] == 'install' for c in self.run.call_args_list))


class ShellBackupTests(unittest.TestCase):
  patch = SwitchSafetyTests.patch
  save_metadata = SwitchSafetyTests.save_metadata

  def setUp(self):
    self.real_run = subprocess.run
    SwitchSafetyTests.setUp(self)
    self.root = Path(self.directory.name)
    self.etc = self.root / 'etc'
    self.etc.mkdir()
    for name in ('bashrc', 'zshrc'):
      (self.system / 'etc' / name).symlink_to('/fixture/generated-' + name)
    self.module.ETC = self.etc
    self.activated = False
    self.prompt.side_effect = ['switch', 'backup']

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
    if command == [self.target['hermesCheck']]:
      return subprocess.CompletedProcess(command, 0)
    if command == ['/usr/bin/sudo', '-v']:
      return subprocess.CompletedProcess(command, 0)
    if 'nix-env' in command[1]:
      self.module.PROFILE.symlink_to(self.system)
      return subprocess.CompletedProcess(command, 0)
    if 'darwin-rebuild' in command[1]:
      self.module.CURRENT.symlink_to(self.system)
      self.activated = True
      return subprocess.CompletedProcess(command, 0)
    self.assertEqual(command[:2], ['/usr/bin/sudo', '/usr/bin/python3'])
    return self.real_run(command[1:], **kwargs)

  def invoke(self, action='switch'):
    arguments = [str(self.system)] if action == 'switch' else []
    with patch('sys.argv', ['dotfiles.py', action, *arguments]):
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

  def test_authentication_failure_preserves_shell_files_after_backup_approval(self):
    source = self.etc / 'bashrc'
    source.write_text('active\n')
    def run(command, **kwargs):
      if command == ['/usr/bin/sudo', '-v']:
        self.assertEqual(self.prompt.call_count, 2)
        raise subprocess.CalledProcessError(1, command)
      return self.run_command(command, **kwargs)
    self.run.side_effect = run
    with self.assertRaises(subprocess.CalledProcessError):
      self.invoke()
    self.assertEqual(source.read_text(), 'active\n')
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
