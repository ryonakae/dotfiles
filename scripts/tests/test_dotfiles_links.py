import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


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
    self.source('.agents/AGENTS.md')
    self.source('.config/mise/config.base.toml', content='')

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
    result = self.mise('unapply', str(self.home), '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertFalse(target.is_symlink())
    self.assertTrue(source.is_file())
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    target.unlink()
    target.write_text('replacement\n')
    self.mise('unapply', str(self.home), '--yes')
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

  def test_home_walk_excludes_nix_generated_files_examples_tests_and_state(self):
    excluded = [
      'nix/home/packages.nix',
      '.config/agent-safehouse/safe-hermes-gateway.sh',
      '.config/agent-safehouse/safe-hermes-dashboard.sh',
      '.config/hermes/check-stopped.sh',
      '.config/herdr/scripts/tests/test_helper.py',
      '.config/tool/config.toml.example',
      '.config/fish/fish_variables',
      '.pi/agent/sessions/last.json',
    ]
    for name in excluded:
      self.source(name)
    self.source('.config/fish/functions/local-only.fish', tracked=False)
    result = self.mise('apply', '--yes')
    self.assertEqual(result.returncode, 0, result.stderr)
    for name in [*excluded, '.config/mise/config.base.toml',
                 '.config/fish/functions/local-only.fish']:
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
