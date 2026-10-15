import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
MISE = shutil.which('mise')
FISH = shutil.which('fish')


class DotfilesSourcesTests(unittest.TestCase):
  def setUp(self):
    self.assertIsNotNone(MISE, 'mise is required for repository integration tests')
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.base = Path(self.directory.name).resolve()
    self.home = self.base / 'home with spaces'
    self.repo = self.base / 'checkout with spaces'
    self.home.mkdir()
    self.repo.mkdir()
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
      'MISE_ENV_CACHE': '0',
      'GIT_CONFIG_NOSYSTEM': '1',
      'GIT_CONFIG_GLOBAL': os.devnull,
      'GIT_AUTHOR_NAME': 'Fixture',
      'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
      'GIT_COMMITTER_NAME': 'Fixture',
      'GIT_COMMITTER_EMAIL': 'fixture@example.invalid',
    }
    (self.repo / 'mise.toml').write_text((ROOT / 'mise.toml').read_text())

  def git(self, *args):
    return subprocess.run(['git', *map(str, args)], env=self.env, check=True,
                          capture_output=True, text=True, timeout=10)

  def mise(self, *args, profile='default'):
    return subprocess.run([MISE, '-C', str(self.repo), '-E', profile,
                           'bootstrap', 'repos', *args],
                          env=self.env, cwd=self.base, capture_output=True,
                          text=True, timeout=30)

  def fixture_remote(self):
    remote = self.base / 'upstream'
    self.git('init', '--quiet', '--initial-branch=main', remote)
    skill = remote / 'skills/selected/SKILL.md'
    skill.parent.mkdir(parents=True)
    skill.write_text('initial external skill\n')
    self.git('-C', remote, 'add', '.')
    self.git('-C', remote, 'commit', '--quiet', '-m', 'Initial fixture')
    target = self.home / '.local/share/agent-skill-sources/fixture'
    (self.repo / 'mise.default.toml').write_text(
      '[bootstrap.repos]\n'
      f'"~/.local/share/agent-skill-sources/fixture" = {{ url = "{remote}", ref = "main" }}\n')
    (self.repo / 'mise.private.toml').write_text('')
    return remote, target

  def test_branch_updates_are_visible_and_dirty_work_is_protected(self):
    remote, target = self.fixture_remote()
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    selected = target / 'skills/selected/SKILL.md'
    self.assertEqual(selected.read_text(), 'initial external skill\n')
    (remote / 'skills/selected/SKILL.md').write_text('branch update\n')
    self.git('-C', remote, 'commit', '--quiet', '-am', 'Branch update')
    result = self.mise('update', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(selected.read_text(), 'branch update\n')
    selected.write_text('local changes\n')
    (remote / 'skills/selected/SKILL.md').write_text('next branch update\n')
    self.git('-C', remote, 'commit', '--quiet', '-am', 'Next branch update')
    result = self.mise('update', '--yes')
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual(selected.read_text(), 'local changes\n')

  def test_origin_mismatch_is_preserved_and_private_does_not_clone_default(self):
    remote, target = self.fixture_remote()
    result = self.mise('apply', '--yes', profile='private')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse(target.exists())
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.git('-C', target, 'remote', 'set-url', 'origin', str(self.base / 'other'))
    before = self.git('-C', target, 'rev-parse', 'HEAD').stdout
    result = self.mise('update', '--yes')
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual(self.git('-C', target, 'rev-parse', 'HEAD').stdout, before)
    self.assertEqual(self.git('-C', target, 'remote', 'get-url', 'origin').stdout.strip(),
                     str(self.base / 'other'))

  def test_homebrew_vendor_activation_is_replaced_by_one_interactive_activation(self):
    self.assertIsNotNone(FISH, 'fish is required for startup integration tests')
    config = self.home / '.config/fish'
    (config / 'conf.d').mkdir(parents=True)
    (config / 'config.fish').write_text((ROOT / 'config/.config/fish/config.fish').read_text())
    snippet = ROOT / 'config/.config/fish/conf.d/mise-activate.fish'
    if snippet.exists():
      (config / 'conf.d/mise-activate.fish').write_text(snippet.read_text())
    bin_dir = self.home / '.local/bin'
    bin_dir.mkdir(parents=True)
    log = self.base / 'activation.log'
    mise = bin_dir / 'mise'
    mise.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$ACTIVATION_LOG"\n'
                    f'printf \'function mise; command "{mise}" $argv; end\\n\'\n')
    mise.chmod(0o755)
    zoxide = bin_dir / 'zoxide'
    zoxide.write_text('#!/bin/sh\nexit 0\n')
    zoxide.chmod(0o755)
    vendor = self.home / '.local/share/fish/vendor_conf.d'
    vendor.mkdir(parents=True)
    (vendor / 'mise-activate.fish').write_text(
      f'if [ "$MISE_FISH_AUTO_ACTIVATE" != "0" ]\n "{mise}" activate fish | source\nend\n')
    (vendor / 'vendor-probe.fish').write_text('set -g fixture_vendor_loaded 1\n')
    env = dict(self.env, PATH=f'{bin_dir}:{self.env["PATH"]}',
               XDG_CONFIG_HOME=str(self.home / '.config'),
               XDG_DATA_HOME=str(self.home / '.local/share'),
               TERM='xterm-256color', ACTIVATION_LOG=str(log))
    script = 'test "$fixture_vendor_loaded" = 1; or exit 15'
    result = subprocess.run([FISH, '--interactive', '-c', script],
                            env=env, cwd=self.home, capture_output=True,
                            text=True, timeout=10)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(log.read_text().splitlines(), ['activate fish'])
    log.unlink()
    result = subprocess.run([FISH, '-c', script], env=env, cwd=self.home,
                            capture_output=True, text=True, timeout=10)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse(log.exists())

  def test_fish_loads_plugin_functions_completions_and_interactive_conf(self):
    self.assertIsNotNone(FISH, 'fish is required for plugin integration tests')
    (Path(self.env['MISE_DATA_DIR']) / 'shims').mkdir(parents=True)
    config = self.home / '.config/fish'
    for name in ('bobthefish', 'fzf'):
      plugin = config / 'plugins' / name
      (plugin / 'functions').mkdir(parents=True)
      (plugin / 'completions').mkdir()
      (plugin / 'conf.d').mkdir()
      (plugin / 'functions' / f'fixture_{name}.fish').write_text(
        f'function fixture_{name}\n echo {name}\nend\n')
      (plugin / 'conf.d' / 'fixture.fish').write_text(
        f'set -g fixture_{name}_loaded 1\n')
    bin_dir = self.base / 'bin'
    bin_dir.mkdir()
    for name in ('mise', 'zoxide'):
      path = bin_dir / name
      path.write_text('#!/bin/sh\nexit 0\n')
      path.chmod(0o755)
    env = dict(self.env, PATH=f'{bin_dir}:{self.env["PATH"]}',
               XDG_CONFIG_HOME=str(self.home / '.config'), TERM='xterm-256color',
               DOTFILES_FISH_CONFIG=str(ROOT / 'config/.config/fish/config.fish'))
    script = ('source "$DOTFILES_FISH_CONFIG"; '
              'fixture_bobthefish; fixture_fzf; '
              'test "$fixture_bobthefish_loaded" = 1; or exit 11; '
              'test "$fixture_fzf_loaded" = 1; or exit 12; '
              'contains -- "$HOME/.config/fish/plugins/fzf/completions" $fish_complete_path; '
              'or exit 13')
    result = subprocess.run([FISH, '--no-config', '--interactive', '-c', script],
                            env=env, cwd=self.home, capture_output=True,
                            text=True, timeout=10)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn('bobthefish\nfzf\n', result.stdout)
    result = subprocess.run([FISH, '--no-config', '-c',
                             'source "$DOTFILES_FISH_CONFIG"; '
                             'set -q fixture_fzf_loaded; and exit 14; '
                             'contains -- "$MISE_DATA_DIR/shims" $PATH'],
                            env=env, cwd=self.home, capture_output=True,
                            text=True, timeout=10)
    self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
  unittest.main()
