import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MISE = Path('/opt/homebrew/bin/mise')
ORIGIN = 'https://github.com/ryonakae/hermes-agent.git'
INSTALLER = '''#!/bin/bash
set -eu
stage= branch= dir=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --stage) stage="$2"; shift 2;;
    --branch) branch="$2"; shift 2;;
    --dir) dir="$2"; shift 2;;
    --hermes-home) test "$2" = "$HOME/.hermes"; shift 2;;
    --skip-browser|--skip-computer-use) shift;;
    *) exit 89;;
  esac
done
printf '%s\\n' "$stage" >> "$HOME/stages.log"
if [ "$stage" = "${FIXTURE_FAIL_STAGE:-}" ]; then exit 27; fi
case "$stage" in
  venv)
    test ! -e "$dir/venv"
    mkdir -p "$dir/venv/bin"
    printf '#!/bin/sh\\nexit 0\\n' > "$dir/venv/bin/hermes"
    chmod +x "$dir/venv/bin/hermes";;
  python-deps|node-deps)
    test -x "$dir/venv/bin/hermes"
    if [ "$stage" = node-deps ] && [ "${FIXTURE_DIRTY_NODE:-}" = 1 ]; then
      printf 'unexpected generated change\\n' > "$dir/revision"
    fi;;
  complete)
    printf '{"schemaVersion":1,"pinnedCommit":"%s","pinnedBranch":"%s","completedAt":"2026-10-14T00:00:00.000Z"}\\n' "$(git -C "$dir" rev-parse HEAD)" "$branch" > "$dir/.hermes-bootstrap-complete"
    printf 'git\\n' > "$dir/.install_method"
    if [ "${FIXTURE_FAIL_AFTER_COMPLETE:-}" = 1 ]; then exit 28; fi;;
  *) exit 88;;
esac
'''


class HermesInstallTests(unittest.TestCase):
  def setUp(self):
    self.assertTrue(MISE.is_file(), 'real mise is required')
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.base = Path(self.directory.name).resolve()
    self.home = self.base / 'home with spaces'
    self.root = self.base / 'checkout with spaces'
    self.remote = self.base / 'upstream'
    self.home.mkdir()
    self.root.mkdir()
    self.env = {
      'HOME': str(self.home), 'PATH': os.environ['PATH'],
      'GIT_CONFIG_NOSYSTEM': '1',
      'GIT_CONFIG_GLOBAL': str(self.base / 'gitconfig'),
      'GIT_AUTHOR_NAME': 'Fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
      'GIT_COMMITTER_NAME': 'Fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid',
      'MISE_DATA_DIR': str(self.base / 'custom data'),
      'MISE_CACHE_DIR': str(self.base / 'cache'),
      'MISE_STATE_DIR': str(self.base / 'state'),
      'MISE_CONFIG_DIR': str(self.base / 'config'),
      'MISE_SYSTEM_CONFIG_DIR': str(self.base / 'system'),
      'MISE_GLOBAL_CONFIG_FILE': str(self.base / 'global.toml'),
      'MISE_TRUSTED_CONFIG_PATHS': str(self.root),
      'MISE_ENV_CACHE': '0',
    }
    self.git('config', '--global', f'url.{self.remote}.insteadOf', ORIGIN)
    self.git('init', '--quiet', '--initial-branch=ryonakae', self.remote)
    (self.remote / 'scripts').mkdir()
    (self.remote / 'scripts/install.sh').write_text(INSTALLER)
    (self.remote / '.gitignore').write_text(
      '/venv/\n/node_modules/\n.hermes-bootstrap-complete\n.install_method\n')
    (self.remote / 'revision').write_text('initial\n')
    self.git('-C', self.remote, 'add', '.')
    self.git('-C', self.remote, 'commit', '--quiet', '-m', 'Initial fixture')
    self.target = self.home / '.hermes/hermes-agent'
    self.marker = self.target / '.hermes-bootstrap-complete'
    self.log = self.home / 'stages.log'
    (self.root / 'mise.toml').write_text('[settings]\nexperimental = true\n')
    for profile in ('default', 'private', 'work'):
      (self.root / f'mise.{profile}.toml').write_text('')
    declaration = ROOT / 'mise.hermes.toml'
    shutil.copyfile(declaration, self.root / declaration.name)
    spec = importlib.util.spec_from_file_location('hermes_install', ROOT / 'scripts/hermes-install.py')
    self.module = importlib.util.module_from_spec(spec)
    with patch('sys.dont_write_bytecode', True):
      spec.loader.exec_module(self.module)
    self.module.ROOT = self.root
    self.module.MISE = MISE
    self.real_run = subprocess.run
    self.commands = []
    self.output = io.StringIO()

  def git(self, *args):
    return subprocess.run(['git', *map(str, args)], env=self.env, check=True,
                          text=True, capture_output=True, timeout=10).stdout.strip()

  def command(self, command, **kwargs):
    self.commands.append((command, kwargs))
    if command[0] == str(MISE):
      # Cache/trust are process-boundary test fixtures, not production bypasses.
      env = dict(kwargs['env'])
      for key in ('MISE_CACHE_DIR', 'MISE_STATE_DIR', 'MISE_TRUSTED_CONFIG_PATHS'):
        env[key] = self.env[key]
      kwargs['env'] = env
    kwargs.setdefault('capture_output', True)
    return self.real_run(command, **kwargs)

  def invoke(self, mode='install', answer=None, answers=None, uid=501, interactive=True, options=(), **environment):
    self.commands.clear()
    self.prompts = []
    self.output = io.StringIO()
    responses = iter(answers) if answers is not None else None

    def confirm(prompt):
      self.prompts.append(prompt)
      response = next(responses) if responses is not None else (mode if answer is None else answer)
      return response(prompt) if callable(response) else response
    with patch.dict(os.environ, dict(self.env, **environment), clear=True), \
         patch.object(self.module.subprocess, 'run', side_effect=self.command), \
         patch('os.geteuid', return_value=uid), patch('os.getuid', return_value=uid), \
         patch('pwd.getpwuid', return_value=SimpleNamespace(pw_dir=str(self.home))), \
         patch('sys.stdin.isatty', return_value=interactive), \
         patch('builtins.input', side_effect=confirm), \
         patch('sys.argv', ['hermes-install.py', mode, *options]), \
         patch('sys.stdout', self.output), patch('sys.stderr', self.output):
      try:
        self.module.main()
      except SystemExit as error:
        return error.code
    return 0

  def stages(self):
    return self.log.read_text().splitlines() if self.log.exists() else []

  def assert_ok(self, status):
    self.assertEqual(status, 0, self.output.getvalue())

  def advance(self):
    (self.remote / 'revision').write_text('updated\n')
    self.git('-C', self.remote, 'commit', '--quiet', '-am', 'Upstream update')
    return self.git('-C', self.remote, 'rev-parse', 'HEAD')

  def test_fresh_install_uses_standard_stages_and_marker(self):
    self.assert_ok(self.invoke())
    self.assertEqual(self.stages(), ['venv', 'python-deps', 'node-deps', 'complete'])
    record = json.loads(self.marker.read_text())
    self.assertEqual(record['pinnedCommit'], self.git('-C', self.target, 'rev-parse', 'HEAD'))
    self.assertEqual(record['pinnedBranch'], 'ryonakae')
    self.assertTrue(os.access(self.target / 'venv/bin/hermes', os.X_OK))
    commands = [command for command, _ in self.commands]
    self.assertIn([str(MISE), '-C', str(self.root), '-E', 'hermes',
                   'bootstrap', 'repos', 'apply', '--yes'], commands)
    node = next(c for c in commands if 'node-deps' in c)
    self.assertIn('--skip-browser', node)
    self.assertIn('--skip-computer-use', node)
    for forbidden in ('prerequisites', 'repository', 'path', 'config', 'setup', 'gateway', 'desktop'):
      self.assertFalse(any('--stage' in c and c[c.index('--stage') + 1] == forbidden for c in commands))

  def test_completed_install_is_noop_even_when_upstream_advances(self):
    self.assert_ok(self.invoke())
    before = self.marker.read_bytes()
    head = self.git('-C', self.target, 'rev-parse', 'HEAD')
    self.advance()
    self.assert_ok(self.invoke(answer='not needed'))
    self.assertEqual(self.marker.read_bytes(), before)
    self.assertEqual(self.git('-C', self.target, 'rev-parse', 'HEAD'), head)
    self.assertEqual(self.stages(), ['venv', 'python-deps', 'node-deps', 'complete'])
    self.assertFalse(any(c[0] in (str(MISE), '/bin/bash') for c, _ in self.commands))

  def test_explicit_update_advances_ref_and_preserves_existing_venv(self):
    self.assert_ok(self.invoke())
    executable = self.target / 'venv/bin/hermes'
    before = executable.stat().st_ino
    updated = self.advance()
    self.assert_ok(self.invoke('update'))
    self.assertEqual(self.git('-C', self.target, 'rev-parse', 'HEAD'), updated)
    self.assertEqual(executable.stat().st_ino, before)
    self.assertEqual(self.stages(), ['venv', 'python-deps', 'node-deps', 'complete',
                                    'python-deps', 'node-deps', 'complete'])
    self.assertEqual(json.loads(self.marker.read_text())['pinnedCommit'], updated)
    self.assertTrue(any(c[-3:] == ['update', str(self.target), '--yes'] for c, _ in self.commands))

  def test_symlink_managed_paths_stop_even_for_completed_install(self):
    self.assert_ok(self.invoke())
    for relative in ('.hermes', '.hermes/hermes-agent',
                     '.hermes/hermes-agent/scripts',
                     '.hermes/hermes-agent/scripts/install.sh',
                     '.hermes/hermes-agent/.git',
                     '.hermes/hermes-agent/venv',
                     '.hermes/hermes-agent/venv/bin',
                     '.hermes/hermes-agent/venv/bin/hermes',
                     '.hermes/hermes-agent/.hermes-bootstrap-complete'):
      with self.subTest(path=relative):
        path = self.home / relative
        saved = self.base / 'saved'
        path.rename(saved)
        path.symlink_to(saved, target_is_directory=saved.is_dir())
        try:
          self.assertNotEqual(self.invoke(), 0)
          self.assertIn('symlink', self.output.getvalue())
          self.assertTrue(path.is_symlink())
          self.assertFalse(any(c[0] in (str(MISE), '/bin/bash') for c, _ in self.commands))
        finally:
          path.unlink()
          saved.rename(path)

  def test_confirmation_precedes_every_mutation_and_update_requires_install(self):
    self.assertNotEqual(self.invoke(answer='no'), 0)
    self.assertFalse((self.home / '.hermes').exists())
    self.assertEqual(self.commands, [])
    self.assertNotEqual(self.invoke('update'), 0)
    self.assertEqual(self.commands, [])
    self.assert_ok(self.invoke())
    marker = self.marker.read_bytes()
    self.assertNotEqual(self.invoke('update', answer='no'), 0)
    self.assertEqual(self.marker.read_bytes(), marker)
    self.assertFalse(any(c[0] in (str(MISE), '/bin/bash') for c, _ in self.commands))

  def test_unknown_checkout_marker_origin_branch_and_dirty_work_are_preserved(self):
    self.assert_ok(self.invoke())
    valid = self.marker.read_bytes()
    for mode in ('install', 'update'):
      for record in ('not json', '{}', '[]',
                     valid.decode().replace('"schemaVersion":1', '"schemaVersion":2'),
                     valid.decode().replace('ryonakae', 'main'),
                     valid.decode().replace('2026-10-14T00:00:00.000Z', 'not a date'),
                     valid.decode().replace(self.git('-C', self.target, 'rev-parse', 'HEAD'), '0' * 40)):
        with self.subTest(mode=mode, record=record):
          self.marker.write_text(record)
          self.assertNotEqual(self.invoke(mode), 0)
          self.assertEqual(self.marker.read_text(), record)
          self.assertFalse(any(c[0] in (str(MISE), '/bin/bash') for c, _ in self.commands))
    self.marker.write_bytes(valid)
    self.git('-C', self.target, 'remote', 'set-url', 'origin', 'https://example.invalid/unknown.git')
    self.assertNotEqual(self.invoke('update'), 0)
    self.assertIn('origin', self.output.getvalue())
    self.assertEqual(self.marker.read_bytes(), valid)
    self.git('-C', self.target, 'remote', 'set-url', 'origin', ORIGIN)
    self.git('-C', self.target, 'checkout', '--quiet', '-b', 'other')
    self.assertNotEqual(self.invoke('update'), 0)
    self.assertIn('branch', self.output.getvalue())
    self.git('-C', self.target, 'checkout', '--quiet', 'ryonakae')
    for path in (self.target / 'revision', self.target / 'untracked'):
      path.write_text('local work\n')
      self.assertNotEqual(self.invoke('update'), 0)
      self.assertIn('dirty', self.output.getvalue())
      self.assertEqual(path.read_text(), 'local work\n')
      self.assertEqual(self.marker.read_bytes(), valid)

  def test_incomplete_checkout_never_recreates_existing_venv(self):
    self.assert_ok(self.invoke())
    self.marker.unlink()
    executable = self.target / 'venv/bin/hermes'
    before = executable.stat().st_ino
    for mode in ('install', 'update'):
      self.assertNotEqual(self.invoke(mode), 0)
      self.assertIn('incomplete', self.output.getvalue())
      self.assertFalse(any(c[0] in (str(MISE), '/bin/bash') for c, _ in self.commands))
      self.assertEqual(executable.stat().st_ino, before)
    self.assertEqual(self.stages(), ['venv', 'python-deps', 'node-deps', 'complete'])

  def test_non_executable_entrypoint_is_not_treated_as_complete(self):
    self.assert_ok(self.invoke())
    (self.target / 'venv/bin/hermes').chmod(0o644)
    for mode in ('install', 'update'):
      self.assertNotEqual(self.invoke(mode), 0)
      self.assertIn('executable', self.output.getvalue())
      self.assertFalse(any(c[0] in (str(MISE), '/bin/bash') for c, _ in self.commands))

  def test_failed_update_invalidates_old_marker_even_without_new_commit(self):
    self.assert_ok(self.invoke())
    head = self.git('-C', self.target, 'rev-parse', 'HEAD')
    self.assertNotEqual(self.invoke('update', FIXTURE_FAIL_STAGE='python-deps'), 0)
    self.assertIn('python-deps', self.output.getvalue())
    self.assertFalse(self.marker.exists())
    self.assertEqual(self.git('-C', self.target, 'rev-parse', 'HEAD'), head)
    self.assertEqual(self.stages(), ['venv', 'python-deps', 'node-deps', 'complete', 'python-deps'])
    self.assertNotEqual(self.invoke(), 0)
    self.assertFalse(any(c[0] in (str(MISE), '/bin/bash') for c, _ in self.commands))

  def test_failed_fresh_stage_stops_without_retry_or_marker(self):
    self.assertNotEqual(self.invoke(FIXTURE_FAIL_STAGE='node-deps'), 0)
    self.assertEqual(self.stages(), ['venv', 'python-deps', 'node-deps'])
    self.assertFalse(self.marker.exists())
    self.assertIn('node-deps', self.output.getvalue())
    before = (self.target / 'venv/bin/hermes').stat().st_ino
    self.assertNotEqual(self.invoke(), 0)
    self.assertEqual((self.target / 'venv/bin/hermes').stat().st_ino, before)
    self.assertEqual(self.stages(), ['venv', 'python-deps', 'node-deps'])

  def test_diverged_history_stops_standard_update_without_reset(self):
    self.assert_ok(self.invoke())
    (self.target / 'revision').write_text('local commit\n')
    self.git('-C', self.target, 'commit', '--quiet', '-am', 'Local commit')
    local = self.git('-C', self.target, 'rev-parse', 'HEAD')
    record = json.loads(self.marker.read_text())
    record['pinnedCommit'] = local
    self.marker.write_text(json.dumps(record))
    self.advance()
    self.assertNotEqual(self.invoke('update'), 0)
    self.assertEqual(self.git('-C', self.target, 'rev-parse', 'HEAD'), local)
    self.assertEqual((self.target / 'revision').read_text(), 'local commit\n')
    self.assertFalse(self.marker.exists())
    self.assertEqual(self.stages(), ['venv', 'python-deps', 'node-deps', 'complete'])

  def test_revision_and_stages_are_confirmed_before_installer_execution(self):
    self.assertNotEqual(self.invoke(answers=['install', 'no']), 0)
    head = self.git('-C', self.target, 'rev-parse', 'HEAD')
    self.assertTrue(any(head in prompt and 'venv' in prompt and 'complete' in prompt
                        for prompt in self.prompts))
    self.assertEqual(self.stages(), [])
    self.assertFalse((self.target / 'venv').exists())
    self.assertFalse(self.marker.exists())
    self.assertNotEqual(self.invoke(), 0)
    self.assertEqual(self.prompts, [])

  def test_preapproved_install_runs_stages_without_prompts(self):
    self.assert_ok(self.invoke(options=['--yes']))
    self.assertEqual(self.prompts, [])
    self.assertEqual(self.stages()[-1], 'complete')
    self.assertTrue(self.marker.exists())

  def test_root_safehouse_and_noninteractive_mutation_are_rejected(self):
    for options in ({'uid': 0}, {'APP_SANDBOX_CONTAINER_ID': 'agent-safehouse'}, {'interactive': False}):
      with self.subTest(options=options):
        self.assertNotEqual(self.invoke(**options), 0)
        self.assertEqual(self.commands, [])
        self.assertEqual(self.prompts, [])
        self.assertFalse((self.home / '.hermes').exists())

  def test_real_mise_tasks_dispatch_to_clt_script_operations(self):
    (self.root / 'scripts').mkdir()
    (self.root / 'scripts/hermes-install.py').write_text(
      'import json, os, pathlib, sys\n'
      'pathlib.Path(os.environ["HOME"], "task.json").write_text(json.dumps(sys.argv[1:]))\n')
    for operation in ('install', 'update'):
      result = self.real_run([str(MISE), '-C', str(self.root), '-E', 'hermes',
                              'run', f'hermes:{operation}'],
                             env=self.env, cwd=self.base, text=True, capture_output=True, timeout=30)
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertEqual(json.loads((self.home / 'task.json').read_text()), [operation])
      self.assertIn('/usr/bin/python3', result.stderr)
    self.assertFalse(self.target.exists())

  def test_real_default_repos_update_does_not_advance_hermes_checkout(self):
    self.assert_ok(self.invoke())
    before = self.git('-C', self.target, 'rev-parse', 'HEAD')
    source = (ROOT / 'mise.default.toml').read_text()
    declaration = tomllib.loads(source)
    self.assertNotIn('~/.hermes/hermes-agent', declaration['bootstrap']['repos'])
    for branch in ('main', 'master'):
      self.git('-C', self.remote, 'branch', branch)
    for repository in declaration['bootstrap']['repos'].values():
      self.git('config', '--global', '--add', f'url.{self.remote}.insteadOf', repository['url'])
    (self.root / 'mise.default.toml').write_text(source)
    updated = self.advance()
    result = self.real_run([str(MISE), '-C', str(self.root), '-E', 'default',
                            'bootstrap', 'repos', 'update', '--yes'],
                           env=self.env, cwd=self.base, capture_output=True, text=True, timeout=30)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(self.git('-C', self.target, 'rev-parse', 'HEAD'), before)
    self.assertNotEqual(before, updated)
    self.assert_ok(self.invoke('update'))
    self.assertEqual(self.git('-C', self.target, 'rev-parse', 'HEAD'), updated)

  def test_inherited_mise_selection_cannot_add_repos_and_data_directory_is_preserved(self):
    unwanted = self.home / 'must not clone'
    hostile = '[bootstrap.repos]\n' + f'"{unwanted}" = {{ url = "{ORIGIN}", ref = "ryonakae" }}\n'
    for path in (self.root / 'mise.work.toml', self.base / 'mise.toml',
                 self.base / 'override.toml', self.home / '.config/mise/conf.d/hostile.toml'):
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(hostile)
    self.assert_ok(self.invoke(MISE_ENV='work,default',
                               MISE_OVERRIDE_CONFIG_FILENAMES='override.toml',
                               MISE_DEFAULT_CONFIG_FILENAME='override.toml',
                               MISE_GLOBAL_CONFIG_FILE=str(self.base / 'override.toml'),
                               MISE_SYSTEM_CONFIG_FILE=str(self.base / 'override.toml')))
    self.assertFalse(unwanted.exists())
    for command, options in self.commands:
      self.assertEqual(options['env']['MISE_DATA_DIR'], self.env['MISE_DATA_DIR'])
      if command[0] == str(MISE):
        self.assertEqual(options['env']['MISE_ENV'], 'hermes')
        self.assertEqual(options['env']['MISE_GLOBAL_CONFIG_FILE'], str(self.root / 'mise.toml'))
        self.assertEqual(options['env']['MISE_SYSTEM_CONFIG_FILE'], str(self.root / 'mise.toml'))
        self.assertEqual(options['env']['MISE_CEILING_PATHS'], str(self.root.parent))
        self.assertNotIn('MISE_OVERRIDE_CONFIG_FILENAMES', options['env'])

  def test_failed_complete_cannot_leave_a_valid_published_marker(self):
    self.assertNotEqual(self.invoke(FIXTURE_FAIL_AFTER_COMPLETE='1'), 0)
    self.assertFalse(self.marker.exists())
    self.assertIn('complete', self.output.getvalue())
    self.assertNotEqual(self.invoke(), 0)
    self.assertEqual(self.prompts, [])

  def test_unexpected_dependency_changes_are_preserved_without_completing(self):
    self.assertNotEqual(self.invoke(FIXTURE_DIRTY_NODE='1'), 0)
    self.assertEqual(self.stages(), ['venv', 'python-deps', 'node-deps'])
    self.assertEqual((self.target / 'revision').read_text(), 'unexpected generated change\n')
    self.assertFalse(self.marker.exists())

  def test_unknown_checkout_and_temporary_marker_are_not_overwritten(self):
    self.target.mkdir(parents=True)
    sentinel = self.target / 'unknown'
    sentinel.write_text('unmanaged data\n')
    self.assertNotEqual(self.invoke(), 0)
    self.assertEqual(sentinel.read_text(), 'unmanaged data\n')
    self.assertEqual(self.commands, [])
    sentinel.unlink()
    self.target.rmdir()
    self.assert_ok(self.invoke())
    temporary = self.target / '.hermes-bootstrap-complete.tmp'
    temporary.write_text('interrupted publish\n')
    self.assertNotEqual(self.invoke('update'), 0)
    self.assertEqual(temporary.read_text(), 'interrupted publish\n')
    self.assertEqual(self.commands, [])

  def test_data_config_shell_files_and_service_definitions_are_untouched(self):
    sentinels = []
    for name in ('.hermes/config.yaml', '.hermes/.env', '.hermes/memories/local',
                 '.hermes/sessions/local', '.hermes/hooks/local', '.hermes/cron/local',
                 '.hermes/skills/local', '.zshrc', '.bashrc',
                 'Library/LaunchAgents/ai.hermes.gateway.plist',
                 'Library/LaunchAgents/ai.hermes.dashboard.plist'):
      path = self.home / name
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text('unmanaged fixture\n')
      sentinels.append((path, path.stat().st_ino))
    self.assert_ok(self.invoke())
    self.assert_ok(self.invoke('update'))
    for path, inode in sentinels:
      self.assertEqual(path.stat().st_ino, inode)
      self.assertEqual(path.read_text(), 'unmanaged fixture\n')
    self.assertTrue(all(c[0] in ('git', str(MISE), '/bin/bash') for c, _ in self.commands))

  def test_state_changed_during_confirmation_is_not_mutated(self):
    self.assert_ok(self.invoke())

    def replace_marker(prompt):
      self.marker.write_text('unknown state introduced while confirming\n')
      return 'update'

    self.assertNotEqual(self.invoke('update', answers=[replace_marker, 'update']), 0)
    self.assertEqual(self.marker.read_text(), 'unknown state introduced while confirming\n')
    self.assertFalse(any(c[0] in (str(MISE), '/bin/bash') for c, _ in self.commands))

  def test_git_directory_overrides_cannot_redirect_checkout_operations(self):
    self.assert_ok(self.invoke())
    external = self.base / 'unmanaged git checkout'
    self.git('clone', '--quiet', ORIGIN, external)
    before = self.git('-C', external, 'rev-parse', 'HEAD')
    marker = self.marker.read_bytes()
    self.assertNotEqual(self.invoke('update', GIT_DIR=str(external / '.git'),
                                   GIT_WORK_TREE=str(external)), 0)
    self.assertEqual(self.marker.read_bytes(), marker)
    self.assertEqual(self.git('-C', external, 'rev-parse', 'HEAD'), before)
    self.assertEqual(self.commands, [])


if __name__ == '__main__':
  unittest.main()
