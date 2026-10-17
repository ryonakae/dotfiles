import importlib.util
import io
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


class SetupCliTests(unittest.TestCase):
  def setUp(self):
    spec = importlib.util.spec_from_file_location('dotfiles', ROOT / 'scripts/dotfiles.py')
    self.module = importlib.util.module_from_spec(spec)
    with patch('sys.dont_write_bytecode', True):
      spec.loader.exec_module(self.module)
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    base = Path(self.directory.name).resolve()
    self.root = base / 'checkout with spaces'
    self.root.mkdir()
    self.home = base / 'home'
    self.home.mkdir()
    (self.root / 'brew').mkdir()
    (self.root / 'scripts').mkdir()
    (self.root / 'mise.toml').write_text('[settings]\nexperimental = true\n')
    for profile in ('default', 'private', 'work'):
      (self.root / f'mise.{profile}.toml').write_text(f'# {profile}\n')
      (self.root / 'brew' / f'Brewfile.{profile}').write_text(f'# {profile}\n')
    for name in ('.config/fish/config.fish', '.config/mise/config.base.toml'):
      path = self.root / 'config' / name
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text('fixture\n')
    (self.root / 'mise.hermes.toml').write_text('# Hermes lifecycle\n')
    for name in ('hermes_plists.py', 'hermes-install.py', 'macos-settings.sh'):
      (self.root / 'scripts' / name).write_text('fixture\n')
    prefix = base / 'homebrew'
    (prefix / 'bin').mkdir(parents=True)
    for name in ('brew', 'mise', 'uv'):
      path = prefix / 'bin' / name
      path.write_text('#!/bin/sh\nexit 0\n')
      path.chmod(0o755)
    self.module.ROOT = self.root
    self.module.BREW = prefix / 'bin/brew'
    self.module.MISE = prefix / 'bin/mise'
    self.module.TARGET_USER = 'fixture-user'
    self.module.TARGET_HOME = self.home
    self.real_popen = subprocess.Popen
    self.run = self.patch('subprocess.run', side_effect=self.run_command)
    self.patch('os.geteuid', return_value=501)
    self.patch('os.getuid', return_value=501)
    self.patch('pwd.getpwuid', return_value=SimpleNamespace(pw_name='fixture-user', pw_dir=str(self.home)))
    self.patch('sys.stdin.isatty', return_value=True)
    self.patch('sys.stdout', new_callable=io.StringIO)
    self.patch('sys.stderr', new_callable=io.StringIO)
    prompt = patch('builtins.input', side_effect=self.confirm)
    self.prompt = prompt.start()
    self.addCleanup(prompt.stop)
    environment = patch.dict(os.environ, {'HOME': str(self.home), 'APP_SANDBOX_CONTAINER_ID': '', 'MISE_ENV': 'work'})
    environment.start()
    self.addCleanup(environment.stop)

  def patch(self, name, **kwargs):
    owner = self.module
    *parents, attribute = name.split('.')
    for parent in parents:
      owner = getattr(owner, parent)
    patcher = patch.object(owner, attribute, **kwargs)
    result = patcher.start()
    self.addCleanup(patcher.stop)
    return result

  def confirm(self, prompt):
    for answer in ('setup', 'install', 'trust', 'apply'):
      if f"'{answer}'" in prompt:
        return answer
    self.fail(f'Unexpected prompt: {prompt}')

  def run_command(self, command, **kwargs):
    if command[0] == str(self.module.MISE) and command[-3:] == ['dot', 'apply', '--yes']:
      if 'default' in command[command.index('-E') + 1].split(','):
        for destination, source in (('.config/fish/config.fish', '.config/fish/config.fish'),
                                    ('.config/mise/config.toml', '.config/mise/config.base.toml')):
          link = self.home / destination
          link.parent.mkdir(parents=True, exist_ok=True)
          if not link.is_symlink():
            link.symlink_to(self.root / 'config' / source)
    return subprocess.CompletedProcess(command, 0, stdout='/fixture/clt\n')

  def invoke(self, *profiles):
    with patch('sys.argv', ['dotfiles.py', 'setup', *profiles]):
      self.module.main()

  def commands(self):
    return [call.args[0] for call in self.run.call_args_list]

  def test_all_configuration_arguments_are_validated_before_commands(self):
    for profiles in ((), ('private', 'missing'), ('default', 'default'), ('../work',)):
      with self.subTest(profiles=profiles):
        with self.assertRaises(SystemExit) as error:
          self.invoke(*profiles)
        self.assertEqual(error.exception.code, 2)
        self.run.assert_not_called()
        self.prompt.assert_not_called()

  def test_private_only_installs_hermes_without_default_tools_or_runtimes(self):
    self.invoke('private')
    mise = [str(self.module.MISE), '-C', str(self.root), '-E', 'private']
    hermes_mise = [str(self.module.MISE), '-C', str(self.root), '-E', 'hermes']
    self.assertEqual(self.commands(), [
      ['/usr/bin/xcode-select', '-p'],
      ['/usr/bin/sudo', '-v'],
      [str(self.module.BREW), 'bundle', '--file=' + str(self.root / 'brew/Brewfile.private')],
      [*mise, 'trust', str(self.root / 'mise.toml')],
      [*mise, 'trust', str(self.root / 'mise.private.toml')],
      [*mise, 'bootstrap', 'repos', 'update', '--yes'],
      [*mise, 'dot', 'apply', '--dry-run'],
      [*mise, 'dot', 'apply', '--yes'],
      [*hermes_mise, 'trust', str(self.root / 'mise.hermes.toml')],
      [*hermes_mise, 'run', 'hermes:install'],
      ['/usr/bin/python3', str(self.root / 'scripts/hermes_plists.py')],
      ['/usr/bin/sudo', '-v'],
      [*mise, 'bootstrap', 'macos', 'defaults', 'apply', '--yes'],
      ['/bin/bash', str(self.root / 'scripts/macos-settings.sh'), 'private'],
    ])
    dryrun = next(c for c in self.run.call_args_list if '--dry-run' in c.args[0])
    self.assertEqual(dryrun.kwargs['timeout'], 60)
    for call in self.run.call_args_list:
      if call.args[0][0] == str(self.module.MISE):
        self.assertEqual(call.kwargs['cwd'], self.root)
        self.assertEqual(call.kwargs['env']['MISE_ENV'], 'hermes' if call.args[0][:5] == hermes_mise else 'private')
    self.assertIn('Setup complete:', self.module.sys.stdout.getvalue())
    self.assertFalse(any(t.name == 'dotfiles-sudo-refresh' for t in threading.enumerate()))

  def test_default_only_installs_runtimes_without_hermes(self):
    for name in ('mise.hermes.toml', 'scripts/hermes-install.py', 'scripts/hermes_plists.py'):
      (self.root / name).unlink()
    self.invoke('default')
    commands = self.commands()
    self.assertTrue(any(c[-5:] == ['node', 'python', 'ruby', 'bun', 'aqua:aws/aws-cli'] for c in commands))
    self.assertFalse(any('hermes:install' in c or c[0] == '/usr/bin/python3' for c in commands))
    self.assertEqual([c[-1] for c in commands if 'trust' in c],
                     [str(self.root / 'mise.toml'), str(self.root / 'mise.default.toml')])

  def test_default_creates_shared_skill_directory_before_dry_run(self):
    skills = self.home / '.agents/skills'
    seen = []
    def run(command, **kwargs):
      if '--dry-run' in command:
        seen.append(skills.is_dir())
      return self.run_command(command, **kwargs)
    self.run.side_effect = run
    self.invoke('default')
    self.assertEqual(seen, [True])

  def test_default_is_explicit_and_installs_home_runtimes_before_first_hermes(self):
    self.invoke('private', 'default')
    commands = self.commands()
    bundles = [c for c in commands if 'bundle' in c]
    self.assertEqual([c[-1] for c in bundles], [
      '--file=' + str(self.root / 'brew/Brewfile.private'),
      '--file=' + str(self.root / 'brew/Brewfile.default'),
    ])
    hermes_mise = [str(self.module.MISE), '-C', str(self.root), '-E', 'hermes']
    hermes_task = [*hermes_mise, 'run', 'hermes:install']
    hermes_trust = [*hermes_mise, 'trust', str(self.root / 'mise.hermes.toml')]
    for command in commands:
      if '-E' in command:
        expected = 'hermes' if command in (hermes_task, hermes_trust) else 'private,default'
        self.assertEqual(command[command.index('-E') + 1], expected)
    installs = [c for c in commands if 'install' in c]
    self.assertEqual(installs, [
      [str(self.module.MISE), '-C', str(self.home), 'install', 'node', 'python', 'ruby', 'bun', 'aqua:aws/aws-cli'],
    ])
    self.assertIn(hermes_task, commands)
    self.assertIn(hermes_trust, commands)
    self.assertLess(commands.index(installs[0]), commands.index(hermes_trust))
    self.assertLess(commands.index(hermes_trust), commands.index(hermes_task))
    plists = ['/usr/bin/python3', str(self.root / 'scripts/hermes_plists.py')]
    self.assertLess(commands.index(hermes_task), commands.index(plists))
    self.assertLess(commands.index(plists), next(i for i, c in enumerate(commands) if 'defaults' in c))
    self.assertEqual([c[-1] for c in commands if c[0] == '/bin/bash'], ['private', 'default'])
    for call in self.run.call_args_list:
      if 'install' in call.args[0]:
        self.assertEqual(call.kwargs['cwd'], self.home)
        self.assertEqual(call.kwargs['env']['MISE_ENV'], '')
        self.assertEqual(call.kwargs['env']['MISE_GLOBAL_CONFIG_FILE'], str(self.root / 'config/.config/mise/config.base.toml'))
        self.assertEqual(call.kwargs['env']['MISE_CEILING_PATHS'], str(self.home))
      elif call.args[0] in (hermes_task, hermes_trust):
        self.assertEqual(call.kwargs['cwd'], self.root)
        self.assertEqual(call.kwargs['env']['MISE_ENV'], 'hermes')
        self.assertEqual(call.kwargs['env']['MISE_GLOBAL_CONFIG_FILE'], str(self.root / 'mise.toml'))
    self.assertEqual((self.home / '.config/mise/config.toml').readlink(), self.root / 'config/.config/mise/config.base.toml')

  def test_custom_mise_data_directory_is_shared_by_runtime_and_hermes_operations(self):
    data = str(self.home / 'custom mise data')
    with patch.dict(os.environ, {'MISE_DATA_DIR': data, 'MISE_CONFIG_FILE': '/unselected/mise.toml'}):
      self.invoke('default', 'private')
    calls = [call for call in self.run.call_args_list
             if call.args[0][0] == str(self.module.MISE)]
    self.assertTrue(calls)
    for call in calls:
      self.assertEqual(call.kwargs['env'].get('MISE_DATA_DIR'), data)
      self.assertNotIn('MISE_CONFIG_FILE', call.kwargs['env'])
    self.assertTrue(any('node' in call.args[0] for call in calls))
    self.assertEqual(sum('hermes:install' in call.args[0] for call in calls), 1)

  def test_declared_host_user_and_home_must_match_account_and_environment(self):
    for mismatch in ('username', 'declared home', 'environment home'):
      with self.subTest(mismatch=mismatch):
        self.module.TARGET_USER = 'other-user' if mismatch == 'username' else 'fixture-user'
        self.module.TARGET_HOME = self.home / 'other' if mismatch == 'declared home' else self.home
        with patch.dict(os.environ, {'HOME': str(self.home / 'other' if mismatch == 'environment home' else self.home)}):
          with self.assertRaisesRegex(ValueError, 'configured user'):
            self.invoke('private')
        self.run.assert_not_called()
        self.prompt.assert_not_called()

  def test_root_safehouse_and_noninteractive_setup_are_rejected_before_changes(self):
    for guard in ('root', 'Safehouse', 'noninteractive'):
      with self.subTest(guard=guard):
        self.module.os.geteuid.return_value = 0 if guard == 'root' else 501
        self.module.sys.stdin.isatty.return_value = guard != 'noninteractive'
        with patch.dict(os.environ, {'APP_SANDBOX_CONTAINER_ID': 'agent-safehouse' if guard == 'Safehouse' else ''}):
          with self.assertRaises(SystemExit) as error:
            self.invoke('private')
        self.assertEqual(error.exception.code, 2)
        self.run.assert_not_called()
        self.prompt.assert_not_called()

  def test_missing_setup_foundation_is_installed_without_default_profile(self):
    for name in ('mise', 'uv'):
      (self.module.BREW.parent / name).unlink()
    original = self.run_command
    def run(command, **kwargs):
      if command == [str(self.module.BREW), 'install', 'mise', 'uv']:
        for name in ('mise', 'uv'):
          path = self.module.BREW.parent / name
          path.write_text('#!/bin/sh\nexit 0\n')
          path.chmod(0o755)
      return original(command, **kwargs)
    self.run.side_effect = run
    self.invoke('private')
    commands = self.commands()
    foundation = [str(self.module.BREW), 'install', 'mise', 'uv']
    self.assertIn(foundation, commands)
    self.assertLess(commands.index(foundation), next(i for i, c in enumerate(commands) if 'bundle' in c))
    self.assertEqual([c for c in commands if 'install' in c], [foundation])
    self.assertFalse(any('Brewfile.default' in ' '.join(c) for c in commands))

  def test_new_mac_uses_confirmed_official_installer_then_only_missing_foundation(self):
    prefix = self.module.BREW.parents[1]
    for name in ('brew', 'mise', 'uv'):
      (prefix / 'bin' / name).unlink()
    (prefix / 'bin').rmdir()
    prefix.rmdir()
    installer = '# fixture official installer\n'
    def run(command, **kwargs):
      if command[0] == '/usr/bin/curl':
        return subprocess.CompletedProcess(command, 0, stdout=installer)
      if command == ['/bin/bash', '-c', installer]:
        (prefix / 'bin').mkdir(parents=True)
        self.module.BREW.write_text('#!/bin/sh\nexit 0\n')
        self.module.BREW.chmod(0o755)
      if command == [str(self.module.BREW), 'install', 'mise', 'uv']:
        for name in ('mise', 'uv'):
          path = prefix / 'bin' / name
          path.write_text('#!/bin/sh\nexit 0\n')
          path.chmod(0o755)
      return self.run_command(command, **kwargs)
    self.run.side_effect = run
    self.invoke('private')
    commands = self.commands()
    download = ['/usr/bin/curl', '-fsSL', 'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh']
    self.assertIn(download, commands)
    self.assertIn(['/bin/bash', '-c', installer], commands)
    self.assertLess(commands.index(download), commands.index(['/bin/bash', '-c', installer]))
    self.assertTrue(any("'install'" in c.args[0] for c in self.prompt.call_args_list))
    self.assertLess(commands.index(['/bin/bash', '-c', installer]), commands.index([str(self.module.BREW), 'install', 'mise', 'uv']))
    self.assertIn(f'eval "$({self.module.BREW} shellenv)"', self.module.sys.stdout.getvalue())

  def test_all_selected_declarations_exist_before_any_command_and_report_preflight_failure(self):
    for missing in ('brew/Brewfile.private', 'mise.private.toml', 'mise.hermes.toml', 'scripts/hermes-install.py'):
      with self.subTest(missing=missing):
        path = self.root / missing
        before = path.read_bytes()
        path.unlink()
        with self.assertRaises(FileNotFoundError):
          self.invoke('default', 'private')
        self.run.assert_not_called()
        self.prompt.assert_not_called()
        self.assertIn('Setup stopped at preflight. Completed: none', self.module.sys.stderr.getvalue())
        path.write_bytes(before)

  def test_declaration_changes_after_each_confirmation_stop_before_that_stage(self):
    for word, changed in (('setup', 'brew/Brewfile.private'), ('trust', 'mise.private.toml'),
                          ('apply', 'mise.toml')):
      with self.subTest(word=word):
        self.run.reset_mock()
        path = self.root / changed
        before = path.read_bytes()
        def confirm(prompt):
          answer = self.confirm(prompt)
          if answer == word:
            path.write_text('concurrently changed\n')
          return answer
        self.prompt.side_effect = confirm
        with self.assertRaisesRegex(ValueError, 'changed after confirmation'):
          self.invoke('private')
        commands = self.commands()
        forbidden = {'setup': 'bundle', 'trust': 'trust', 'apply': '--yes'}[word]
        if word == 'apply':
          self.assertFalse(any('dot' in c and forbidden in c for c in commands))
        else:
          self.assertFalse(any(forbidden in c for c in commands))
        path.write_bytes(before)

  def test_cancelling_each_approval_does_not_run_the_declined_operation(self):
    for word in ('setup', 'trust', 'apply'):
      with self.subTest(word=word):
        self.run.reset_mock()
        self.prompt.side_effect = lambda prompt: 'no' if f"'{word}'" in prompt else self.confirm(prompt)
        with self.assertRaisesRegex(ValueError, 'cancelled'):
          self.invoke('private')
        commands = self.commands()
        if word == 'setup':
          self.assertEqual(commands, [['/usr/bin/xcode-select', '-p']])
        elif word == 'trust':
          self.assertFalse(any('trust' in c for c in commands))
        else:
          self.assertEqual(commands[-1][-3:], ['dot', 'apply', '--dry-run'])

  def test_each_command_failure_stops_later_stages_and_reports_partial_completion(self):
    for failing in ('clt', 'sudo', 'bundle', 'trust', 'repos', 'dry-run', 'apply',
                    'runtimes', 'hermes-trust', 'hermes-install', 'plist', 'defaults', 'supplement'):
      with self.subTest(failing=failing):
        self.run.reset_mock()
        self.module.sys.stdout.truncate(0)
        self.module.sys.stdout.seek(0)
        def run(command, **kwargs):
          hit = {
            'clt': command[0] == '/usr/bin/xcode-select',
            'sudo': command == ['/usr/bin/sudo', '-v'],
            'bundle': 'bundle' in command,
            'trust': 'trust' in command,
            'repos': 'repos' in command,
            'dry-run': '--dry-run' in command,
            'apply': 'dot' in command and '--yes' in command,
            'runtimes': command[-5:] == ['node', 'python', 'ruby', 'bun', 'aqua:aws/aws-cli'],
            'hermes-trust': 'trust' in command and command[-1] == str(self.root / 'mise.hermes.toml'),
            'hermes-install': 'hermes:install' in command,
            'plist': command[0] == '/usr/bin/python3',
            'defaults': 'defaults' in command,
            'supplement': command[0] == '/bin/bash',
          }[failing]
          if hit:
            raise subprocess.CalledProcessError(17, command)
          return self.run_command(command, **kwargs)
        self.run.side_effect = run
        with self.assertRaises(subprocess.CalledProcessError) as error:
          self.invoke('default', 'private')
        self.assertEqual(error.exception.returncode, 17)
        self.assertEqual(self.commands()[-1], error.exception.cmd)
        self.assertIn('Setup stopped at', self.module.sys.stderr.getvalue())
        self.assertIn('Completed:', self.module.sys.stderr.getvalue())
        self.assertNotIn('Setup complete:', self.module.sys.stdout.getvalue())
        self.assertFalse(any(t.name == 'dotfiles-sudo-refresh' for t in threading.enumerate()))

  def test_hermes_trust_cancellation_and_changed_files_stop_before_task(self):
    for changed in (None, 'mise.hermes.toml', 'scripts/hermes-install.py'):
      with self.subTest(changed=changed):
        self.run.reset_mock()
        path = self.root / changed if changed else None
        before = path.read_bytes() if path else None
        def confirm(prompt):
          if 'Hermes lifecycle' in prompt:
            if path:
              path.write_text('changed after setup confirmation\n')
            else:
              return 'no'
          return self.confirm(prompt)
        self.prompt.side_effect = confirm
        with self.assertRaisesRegex(ValueError, 'changed after confirmation|cancelled'):
          self.invoke('private')
        self.assertFalse(any('hermes:install' in c or 'defaults' in c for c in self.commands()))
        self.assertFalse(any('trust' in c and c[-1] == str(self.root / 'mise.hermes.toml') for c in self.commands()))
        if path:
          path.write_bytes(before)

  def test_dry_run_timeout_preserves_existing_home_and_does_not_apply(self):
    marker = self.home / 'unmanaged-file'
    marker.write_text('preserve me\n')
    def run(command, **kwargs):
      if '--dry-run' in command:
        raise subprocess.TimeoutExpired(command, 60)
      return self.run_command(command, **kwargs)
    self.run.side_effect = run
    with self.assertRaises(subprocess.TimeoutExpired):
      self.invoke('private')
    self.assertEqual(marker.read_text(), 'preserve me\n')
    self.assertEqual(self.commands()[-1][-1], '--dry-run')
    self.assertFalse(any('install' in c or 'defaults' in c for c in self.commands()))

  def test_wrong_or_indirect_default_runtime_link_stops_installation(self):
    for kind in ('wrong', 'indirect'):
      with self.subTest(kind=kind):
        self.run.reset_mock()
        def run(command, **kwargs):
          result = self.run_command(command, **kwargs)
          if command[-3:] == ['dot', 'apply', '--yes']:
            link = self.home / '.config/mise/config.toml'
            link.unlink()
            if kind == 'indirect':
              intermediary = self.home / 'indirect'
              intermediary.symlink_to(self.root / 'config/.config/mise/config.base.toml')
              link.symlink_to(intermediary)
            else:
              link.symlink_to(self.home / 'unknown-copy')
          return result
        self.run.side_effect = run
        with self.assertRaisesRegex(ValueError, 'live checkout'):
          self.invoke('default')
        self.assertFalse(any('install' in c for c in self.commands()))
        (self.home / '.config/mise/config.toml').unlink()

  def test_unknown_existing_homebrew_prefix_is_not_passed_to_installer(self):
    self.module.BREW.unlink()
    marker = self.module.BREW.parents[1] / 'unknown'
    marker.write_text('retain\n')
    with self.assertRaisesRegex(ValueError, 'unknown existing Homebrew'):
      self.invoke('private')
    self.run.assert_not_called()
    self.assertEqual(marker.read_text(), 'retain\n')

  def test_work_only_ignores_unselected_declarations_and_default_runtimes(self):
    (self.root / 'mise.default.toml').unlink()
    (self.root / 'brew/Brewfile.default').unlink()
    (self.root / 'mise.hermes.toml').unlink()
    (self.root / 'scripts/hermes-install.py').unlink()
    (self.root / 'scripts/hermes_plists.py').unlink()
    self.invoke('work')
    self.assertFalse(any('install' in c for c in self.commands()))
    self.assertEqual([c[-1] for c in self.commands() if c[0] == '/bin/bash'], ['work'])
    self.assertEqual([c[-1] for c in self.commands() if 'trust' in c], [str(self.root / 'mise.toml'), str(self.root / 'mise.work.toml')])

  def test_other_cwd_and_inherited_mise_configuration_cannot_expand_setup_scope(self):
    other = self.home / 'other project'
    other.mkdir()
    (other / 'mise.toml').write_text('[tools]\nnode = "99"\n')
    original_cwd = Path.cwd()
    try:
      os.chdir(other)
      with patch.dict(os.environ, {'MISE_ENV': 'default,work', 'MISE_CONFIG_FILE': str(other / 'mise.toml'),
                                    'MISE_GLOBAL_CONFIG_FILE': str(other / 'mise.toml'), 'MISE_NO_CONFIG': '1'}):
        self.invoke('private')
    finally:
      os.chdir(original_cwd)
    for call in self.run.call_args_list:
      if call.args[0][0] == str(self.module.MISE):
        self.assertEqual(call.kwargs['cwd'], self.root)
        environment = call.kwargs['env']
        self.assertEqual(environment['MISE_ENV'], call.args[0][call.args[0].index('-E') + 1])
        self.assertIn(environment['MISE_ENV'], ('private', 'hermes'))
        self.assertEqual(environment['MISE_GLOBAL_CONFIG_FILE'], str(self.root / 'mise.toml'))
        self.assertEqual(environment['MISE_SYSTEM_CONFIG_FILE'], str(self.root / 'mise.toml'))
        self.assertEqual(environment['MISE_CEILING_PATHS'], str(self.root.parent))
        self.assertNotIn('MISE_CONFIG_FILE', environment)
        self.assertNotIn('MISE_NO_CONFIG', environment)

  def start_fake_refresh(self, code=None):
    self.processes = []
    self.module.SUDO_REFRESH_INTERVAL = 0.01
    self.module.SUDO_REFRESH_TIMEOUT = 1
    program = 'import time; time.sleep(10)' if code is None else f'import sys; sys.exit({code})'
    def popen(command, **kwargs):
      self.assertEqual(command, ['/usr/bin/sudo', '-n', '-v'])
      self.assertEqual(kwargs, {})
      process = self.real_popen(['/usr/bin/python3', '-c', program])
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

  def test_refresh_failure_or_timeout_warns_and_reauthenticates_at_next_sudo_stage(self):
    for ending in ('failure', 'timeout'):
      with self.subTest(ending=ending):
        self.run.reset_mock()
        self.module.sys.stderr.truncate(0)
        self.module.sys.stderr.seek(0)
        self.start_fake_refresh(code=4 if ending == 'failure' else None)
        if ending == 'timeout':
          self.module.SUDO_REFRESH_TIMEOUT = 0.05
        def run(command, **kwargs):
          if 'bundle' in command:
            self.wait_for_refresh(failed=True)
          return self.run_command(command, **kwargs)
        self.run.side_effect = run
        self.invoke('private')
        commands = self.commands()
        bundle = next(i for i, c in enumerate(commands) if 'bundle' in c)
        defaults = next(i for i, c in enumerate(commands) if 'defaults' in c)
        self.assertIn(['/usr/bin/sudo', '-v'], commands[bundle + 1:defaults])
        self.assertIn('Setup complete:', self.module.sys.stdout.getvalue())
        self.assertIn('sudo may ask for the password again', self.module.sys.stderr.getvalue())
        self.assertTrue(all(p.poll() is not None for p in self.processes))
        self.assertFalse(any(t.name == 'dotfiles-sudo-refresh' for t in threading.enumerate()))

  def test_refresh_is_reaped_on_success_exception_interrupt_and_termination_signals(self):
    for ending in ('success', 'exception', 'interrupt', signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
      with self.subTest(ending=ending):
        self.start_fake_refresh()
        previous = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT)}
        def run(command, **kwargs):
          if 'bundle' in command:
            self.wait_for_refresh()
            if ending == 'exception':
              raise OSError('fixture operation failed')
            if ending == 'interrupt':
              raise KeyboardInterrupt()
            if ending in previous:
              os.kill(os.getpid(), ending)
          elif command[0] == str(self.module.MISE) and 'defaults' not in command:
            self.assertFalse(any(t.name == 'dotfiles-sudo-refresh' for t in threading.enumerate()))
          return self.run_command(command, **kwargs)
        self.run.side_effect = run
        if ending == 'success':
          self.invoke('private')
        else:
          with self.assertRaises((OSError, KeyboardInterrupt, SystemExit)):
            self.invoke('private')
        self.assertTrue(all(p.poll() is not None for p in self.processes))
        self.assertFalse(any(t.name == 'dotfiles-sudo-refresh' for t in threading.enumerate()))
        for signum, handler in previous.items():
          self.assertEqual(signal.getsignal(signum), handler)


class ShellEntrypointTests(unittest.TestCase):
  def test_help_works_without_path_python_from_repo_or_other_project(self):
    with tempfile.TemporaryDirectory() as directory:
      project = Path(directory) / 'other project'
      project.mkdir()
      (project / '.python-version').write_text('unavailable-python\n')
      shims = Path(directory) / 'shims'
      shims.mkdir()
      python = shims / 'python3'
      python.write_text('#!/bin/sh\nprintf "mise Python is unavailable\\n" >&2\nexit 127\n')
      python.chmod(0o755)
      env = dict(os.environ, PATH=f'{shims}:/usr/bin:/bin', MISE_ENV='work')
      for cwd in (ROOT, project):
        with self.subTest(cwd=cwd):
          result = subprocess.run(['/bin/bash', str(ROOT / 'scripts/dotfiles.sh'), '--help'], cwd=cwd, env=env, capture_output=True, text=True)
          self.assertEqual(result.returncode, 0, result.stderr)
          self.assertIn('Set up explicitly selected macOS configurations', result.stdout)
          self.assertIn('setup', result.stdout)
          self.assertEqual(result.stderr, '')


if __name__ == '__main__':
  unittest.main()
