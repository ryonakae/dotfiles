import importlib.util
import io
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MISE = shutil.which('mise')


class DotfilesLinksTests(unittest.TestCase):
  def setUp(self):
    self.assertIsNotNone(MISE, 'mise is required for dotfile integration tests')
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.base = Path(self.directory.name).resolve()
    self.repo = self.base / 'checkout with spaces'
    self.home = self.base / 'home with spaces'
    self.repo.mkdir()
    self.home.mkdir()
    (self.home / '.agents/skills').mkdir(parents=True)
    self.env = {
      'HOME': str(self.home),
      'PATH': os.environ['PATH'],
      'MISE_CONFIG_DIR': str(self.base / 'config'),
      'MISE_SYSTEM_CONFIG_DIR': str(self.base / 'system'),
      'MISE_GLOBAL_CONFIG_FILE': str(self.base / 'global.toml'),
      'MISE_DATA_DIR': str(self.base / 'data'),
      'MISE_CACHE_DIR': str(self.base / 'cache'),
      'MISE_STATE_DIR': str(self.base / 'state'),
      'MISE_TRUSTED_CONFIG_PATHS': str(self.repo),
      'MISE_OFFLINE': '1',
      'MISE_ENV_CACHE': '0',
    }
    (self.repo / 'mise.toml').write_text((ROOT / 'mise.toml').read_text())
    subprocess.run(['git', 'init', '--quiet', str(self.repo)], env=self.env, check=True)
    tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z', '--', 'config'],
                             capture_output=True, text=True, check=True).stdout
    for name in tracked.split('\0'):
      if name and (ROOT / name).exists() and not name.startswith('config/.agents/skills/'):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('')
    subprocess.run(['git', '-C', str(self.repo), 'add', '--', 'config'],
                   env=self.env, check=True)

  def source(self, name, content='fixture\n', tracked=True):
    path = self.repo / 'config' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    if tracked:
      subprocess.run(['git', '-C', str(self.repo), 'add', '--', str(path)],
                     env=self.env, check=True)
    return path

  def mise(self, *args):
    return subprocess.run([MISE, '-C', str(self.repo), 'dot', *args],
                          cwd=self.base, env=self.env, capture_output=True,
                          text=True, timeout=30)

  def test_setup_trusts_only_the_reviewed_declaration_in_isolated_home(self):
    self.env.pop('MISE_TRUSTED_CONFIG_PATHS')
    self.assertNotIn('CI', self.env)
    self.assertNotIn('MISE_YES', self.env)
    for name in ('.config/fish/config.fish', '.config/mise/config.base.toml'):
      self.source(name)
    spec = importlib.util.spec_from_file_location('dotfiles', ROOT / 'scripts/dotfiles.py')
    module = importlib.util.module_from_spec(spec)
    with patch('sys.dont_write_bytecode', True):
      spec.loader.exec_module(module)
    module.ROOT = self.repo
    module.STORE = self.base / 'store'
    module.PROFILE = self.base / 'profile'
    module.CURRENT = self.base / 'current'
    system = module.STORE / 'system'
    (system / 'etc/dotfiles').mkdir(parents=True)
    (system / 'sw/bin').mkdir(parents=True)
    (system / 'systemConfig').write_text(str(system))
    snapshot = module.STORE / 'snapshot'
    snapshot.mkdir()
    (snapshot / 'mise.toml').write_bytes((self.repo / 'mise.toml').read_bytes())
    mise = module.STORE / 'mise/bin/mise'
    mise.parent.mkdir(parents=True)
    mise.write_text(f'#!/bin/sh\nexec "{Path(MISE).resolve()}" "$@"\n')
    check = module.STORE / 'check-hermes'
    check.write_text('#!/bin/sh\nexit 0\n')
    for path in (system / 'activate', system / 'sw/bin/nix-env', system / 'sw/bin/darwin-rebuild'):
      path.write_text('#!/bin/sh\nexit 0\n')
      path.chmod(0o755)
    mise.chmod(0o755)
    check.chmod(0o755)
    module.BREW = self.base / 'brew'
    module.BREW.write_text('#!/bin/sh\nexit 0\n')
    module.BREW.chmod(0o755)
    username = pwd.getpwuid(os.getuid()).pw_name
    target = dict(configuration='default', source=str(snapshot), username=username,
                  homeDirectory=str(self.home), hermesCheck=str(check), mise=str(mise))
    (system / 'etc/dotfiles/build.json').write_text(json.dumps(target))
    real_run = subprocess.run
    commands = []
    def run(command, **kwargs):
      commands.append(command)
      if command[0] == str(mise):
        result = real_run(command, env=self.env, input='y\n', capture_output=True,
                          text=True, **kwargs)
        print(result.stdout)
        return result
      if command[0] == str(check) or command[:2] == ['/usr/bin/sudo', '-v']:
        return subprocess.CompletedProcess(command, 0)
      if command[1] == str(system / 'sw/bin/nix-env'):
        module.PROFILE.symlink_to(system)
      elif command[1] == str(system / 'sw/bin/darwin-rebuild'):
        module.CURRENT.symlink_to(system)
      else:
        self.fail(f'Unexpected subprocess: {command}')
      return subprocess.CompletedProcess(command, 0)
    def nix(*args, **kwargs):
      if args[:2] == ('flake', 'metadata'):
        return {'path': str(snapshot)}
      if args[0] == 'eval':
        return target
      if args[:2] == ('flake', 'check'):
        return ''
      if args[0] == 'build':
        return [{'outputs': {'out': str(system)}}]
      self.fail(f'Unexpected Nix command: {args}')
    with patch.dict(os.environ, dict(self.env, APP_SANDBOX_CONTAINER_ID=''), clear=True), \
         patch.object(module, 'nix', side_effect=nix), \
         patch.object(module.subprocess, 'run', side_effect=run), \
         patch.object(module.pwd, 'getpwuid', return_value=SimpleNamespace(pw_name=username, pw_dir=str(self.home))), \
         patch.object(module.sys.stdin, 'isatty', return_value=True), \
         patch('builtins.input', side_effect=['switch', 'trust', 'apply']), \
         patch('sys.argv', ['dotfiles.py', 'setup']), \
         patch('sys.stdout', new_callable=io.StringIO):
      module.main()
    trust = [command for command in commands if 'trust' in command]
    self.assertEqual(trust, [[str(mise), '-C', str(self.repo), 'trust', str(self.repo / 'mise.toml')]])
    self.assertEqual((self.home / '.config/fish/config.fish').readlink(), self.repo / 'config/.config/fish/config.fish')
    self.assertEqual((self.home / '.config/mise/config.toml').readlink(), self.repo / 'config/.config/mise/config.base.toml')

  def test_initial_operations_do_not_walk_unmanaged_home_directories(self):
    blocked = ['Library', 'Documents']
    sentinels = []
    for name in blocked:
      path = self.home / name
      path.mkdir(parents=True)
      sentinel = path / 'unmanaged.txt'
      sentinel.write_text('unmanaged state\n')
      sentinels.append(sentinel)
      path.chmod(0)
      self.addCleanup(path.chmod, 0o700)
      with self.assertRaises(PermissionError, msg=f'{path} must reject directory access'):
        list(path.iterdir())

    source = self.source('.vimrc')
    target = self.home / '.vimrc'
    self.env['MISE_DEBUG'] = '1'
    for operation in [('apply', '--dry-run'), ('apply', '--yes'), ('unapply', '--yes')]:
      with self.subTest(operation=operation):
        self.assertFalse((self.base / 'state/dotfiles').exists())
        result = self.mise(*operation)
        self.assertEqual(result.returncode, 0, result.stderr)
        walking_errors = [line for line in result.stderr.splitlines()
                          if 'files: walking' in line and 'Permission denied' in line]
        self.assertEqual(walking_errors, [], '\n'.join(walking_errors))
        if operation == ('apply', '--dry-run'):
          self.assertFalse(target.is_symlink())
        elif operation == ('apply', '--yes'):
          self.assertEqual(target.readlink(), source)
        else:
          self.assertFalse(target.is_symlink())
        shutil.rmtree(self.base / 'state/dotfiles', ignore_errors=True)

    for sentinel in sentinels:
      sentinel.parent.chmod(0o700)
      self.assertEqual(sentinel.read_text(), 'unmanaged state\n')

  def test_apply_links_directly_and_edits_reach_source_from_another_cwd(self):
    source = self.source('.vimrc')
    target = self.home / '.vimrc'
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertTrue(target.is_symlink())
    self.assertEqual(target.readlink(), source)
    target.write_text('edited through home\n')
    self.assertEqual(source.read_text(), 'edited through home\n')
    before = target.lstat().st_ino
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(target.lstat().st_ino, before)

  def test_karabiner_directory_link_exposes_source_edits_without_a_json_link(self):
    source = self.source('.config/karabiner/karabiner.json', '{"profiles": []}\n')
    target = self.home / '.config/karabiner'
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertTrue(target.is_symlink())
    self.assertEqual(target.readlink(), source.parent)
    self.assertFalse((target / 'karabiner.json').is_symlink())
    source.write_text('{"profiles": [{"name": "edited"}]}\n')
    self.assertEqual((target / 'karabiner.json').read_text(),
                     '{"profiles": [{"name": "edited"}]}\n')

  def test_rm_wrapper_is_a_direct_managed_link(self):
    source = self.source('.local/bin/rm', '#!/bin/sh\nexit 23\n')
    source.chmod(0o755)
    target = self.home / '.local/bin/rm'
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(target.readlink(), source)
    self.assertEqual(subprocess.run([str(target)]).returncode, 23)

  def test_functions_follow_git_membership_without_touching_local_files(self):
    source = self.source('.config/fish/functions/shared.fish')
    self.source('.config/fish/functions/untracked.fish', tracked=False)
    target = self.home / '.config/fish/functions'
    target.mkdir(parents=True)
    local = target / 'local.fish'
    local.write_text('local settings\n')
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual((target / 'shared.fish').readlink(), source)
    self.assertFalse((target / 'untracked.fish').exists())
    added = self.source('.config/fish/functions/added.fish')
    subprocess.run(['git', '-C', str(self.repo), 'rm', '--cached', '--quiet', '--', str(source)],
                   env=self.env, check=True)
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse((target / 'shared.fish').is_symlink())
    self.assertEqual((target / 'added.fish').readlink(), added)
    self.assertEqual(local.read_text(), 'local settings\n')

  def test_apply_preserves_conflicting_real_file_and_unapply_preserves_replacement(self):
    source = self.source('.vimrc')
    target = self.home / '.vimrc'
    target.write_text('local settings\n')
    result = self.mise('apply', '--yes')
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual(target.read_text(), 'local settings\n')
    self.assertEqual(source.read_text(), 'fixture\n')
    target.unlink()
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    result = self.mise('unapply', str(target), '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse(target.is_symlink())
    self.assertTrue(source.is_file())
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    target.unlink()
    target.write_text('replacement\n')
    result = self.mise('unapply', str(target), '--yes')
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual(target.read_text(), 'replacement\n')

  def test_agent_instructions_share_one_direct_source(self):
    source = self.source('.agents/AGENTS.md')
    targets = ['.agents/AGENTS.md', '.claude/CLAUDE.md', '.codex/AGENTS.md',
               '.gemini/GEMINI.md', '.pi/agent/AGENTS.md']
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    for name in targets:
      with self.subTest(target=name):
        self.assertEqual((self.home / name).readlink(), source)

  def test_local_skill_links_preserve_external_siblings_and_share_with_antigravity(self):
    source = self.source('.agents/skills/ask-codex/SKILL.md')
    self.source('.agents/skills/.disabled/disabled/SKILL.md')
    self.source('.agents/skills/local-only/SKILL.md', tracked=False)
    shared = self.home / '.agents/skills'
    shared.mkdir(parents=True, exist_ok=True)
    external = shared / 'external'
    external.mkdir()
    (external / 'SKILL.md').write_text('external skill\n')
    targets = [shared / 'ask-codex', self.home / '.claude/skills/ask-codex',
               self.home / '.gemini/antigravity-cli/skills']
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual((targets[0] / 'SKILL.md').readlink(), source)
    self.assertEqual((targets[1] / 'SKILL.md').readlink(), source)
    self.assertEqual(targets[2].readlink(), shared)
    self.assertFalse((shared / '.disabled').exists())
    self.assertFalse((shared / 'local-only/SKILL.md').exists())
    self.assertEqual((targets[2] / 'external/SKILL.md').read_text(), 'external skill\n')

  def test_apply_excludes_nix_generated_files_examples_tests_and_state(self):
    excluded = [
      'nix/home/packages.nix',
      '.config/agent-safehouse/safe-hermes-gateway.sh',
      '.config/agent-safehouse/safe-hermes-dashboard.sh',
      '.config/hermes/check-stopped.sh',
      '.config/herdr/scripts/tests/test_helper.py',
      '.config/tool/config.toml.example',
    ]
    untracked = ['.config/fish/fish_variables', '.pi/agent/sessions/last.json',
                 '.config/fish/functions/local-only.fish']
    for name in excluded:
      self.source(name)
    for name in untracked:
      self.source(name, tracked=False)
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    for name in [*excluded, *untracked, '.config/mise/config.base.toml']:
      with self.subTest(path=name):
        self.assertFalse(os.path.lexists(self.home / name))
    self.assertEqual((self.home / '.config/mise/config.toml').readlink(),
                     self.repo / 'config/.config/mise/config.base.toml')

  def test_claude_specific_skill_entry_overrides_shared_glob(self):
    shared = self.source('.agents/skills/ask-codex/SKILL.md')
    self.source('.agents/skills/ask-codex/references/shared.md')
    claude = self.source('.claude/skills/ask-codex/SKILL.md')
    with (self.repo / 'mise.toml').open('a') as config:
      config.write('\n[dotfiles."~/.claude/skills/ask-codex"]\n'
                   'source = "config/.claude/skills/ask-codex"\n'
                   'mode = "symlink-each"\nmanifest = "git"\n')
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual((self.home / '.agents/skills/ask-codex/SKILL.md').readlink(), shared)
    target = self.home / '.claude/skills/ask-codex'
    self.assertEqual((target / 'SKILL.md').readlink(), claude)
    self.assertFalse((target / 'references/shared.md').exists())
    result = self.mise('unapply', str(target), '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse((target / 'SKILL.md').is_symlink())
    self.assertTrue(claude.is_file())
    self.assertTrue((self.home / '.agents/skills/ask-codex/SKILL.md').is_symlink())


if __name__ == '__main__':
  unittest.main()
