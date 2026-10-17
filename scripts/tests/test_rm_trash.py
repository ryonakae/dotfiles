import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / 'config/.local/bin/rm'
TRASH = '/opt/homebrew/opt/macos-trash/bin/trash'


class RmTrashTests(unittest.TestCase):
  def setUp(self):
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.home = Path(self.directory.name) / 'home with spaces'
    self.bin = self.home / '.local/bin'
    self.bin.mkdir(parents=True)
    self.work = self.home / 'work'
    self.work.mkdir()
    self.trash = self.home / 'brew bin/trash'
    self.trash.parent.mkdir()
    self.trash.write_text('#!' + sys.executable + '\n'
      'import json, os, sys\n'
      'print(json.dumps({"args": sys.argv[1:]}))\n'
      'sys.exit(int(os.environ.get("FAKE_TRASH_EXIT", "0")))\n')
    self.trash.chmod(0o755)
    self.system_rm = self.home / 'system-rm'
    self.system_rm.write_text('#!' + sys.executable + '\n'
      'import json, sys\n'
      'print(json.dumps({"args": sys.argv[1:]}))\n'
      'sys.exit(31)\n')
    self.system_rm.chmod(0o755)
    self.wrapper = self.bin / 'rm'
    self.wrapper.write_text(WRAPPER.read_text().replace(TRASH, str(self.trash))
                            .replace('"/bin/rm"', '"' + str(self.system_rm) + '"'))
    self.wrapper.chmod(0o755)
    self.env = dict(os.environ, HOME=str(self.home), PATH='/usr/bin:/bin',
                    APP_SANDBOX_CONTAINER_ID='agent-safehouse')

  def rm(self, *args, env=None):
    return subprocess.run([str(self.wrapper), *args], env=env or self.env, cwd=self.work,
                          capture_output=True, text=True, timeout=10)

  def trashed(self, result):
    return json.loads(result.stdout)['args'] if result.stdout else None

  def make(self, *names):
    for name in names:
      (self.work / name).write_text('data')

  def test_outside_safehouse_uses_system_rm_unchanged(self):
    args = ['-rf', '--', 'argument with spaces', '']
    for marker in [None, '', 'other-container']:
      with self.subTest(marker=marker):
        env = dict(self.env)
        if marker is None:
          env.pop('APP_SANDBOX_CONTAINER_ID')
        else:
          env['APP_SANDBOX_CONTAINER_ID'] = marker
        result = self.rm(*args, env=env)
        self.assertEqual(result.returncode, 31, result.stderr)
        self.assertEqual(self.trashed(result), args)

  def test_passes_separator_and_keeps_hyphen_names(self):
    self.make('name with spaces', '-option-like', '--', '-')
    result = self.rm('-f', '--', 'name with spaces', '-option-like', '--', '-')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(self.trashed(result),
                     ['--', 'name with spaces', './-option-like', './--', './-'])

  def test_options_stop_at_first_operand(self):
    self.make('file', '-f')
    result = self.rm('file', '-f')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(self.trashed(result), ['--', 'file', './-f'])

  def test_refuses_root_and_dot_operands_but_moves_the_rest(self):
    (self.work / 'dir').mkdir()
    self.make('keep')
    for operand in ['/', '//', '.', '..', './', 'dir/.', 'dir/..', '/..']:
      with self.subTest(operand=operand):
        result = self.rm('-rf', operand, 'keep')
        self.assertEqual(result.returncode, 1)
        self.assertIn('rm:', result.stderr)
        self.assertEqual(self.trashed(result), ['--', 'keep'])

  def test_missing_and_empty_operands_depend_on_force(self):
    self.make('keep')
    result = self.rm('-f', '', 'missing', 'keep')
    self.assertEqual((result.returncode, result.stderr), (0, ''))
    self.assertEqual(self.trashed(result), ['--', 'keep'])
    result = self.rm('-f', '', 'missing')
    self.assertEqual((result.returncode, result.stderr), (0, ''))
    self.assertIsNone(self.trashed(result))
    for operand in ['', 'missing']:
      with self.subTest(operand=operand):
        result = self.rm(operand, 'keep')
        self.assertEqual(result.returncode, 1)
        self.assertIn('No such file or directory', result.stderr)
        self.assertEqual(self.trashed(result), ['--', 'keep'])

  def test_without_operands(self):
    result = self.rm('-f')
    self.assertEqual((result.returncode, result.stdout), (0, ''))
    result = self.rm()
    self.assertEqual((result.returncode, result.stdout), (1, ''))
    self.assertIn('usage', result.stderr)

  def test_rejects_unsupported_options_without_moving(self):
    self.make('keep')
    for option in ['-i', '-I', '-W', '-fi', '-rI', '--force', '--recursive', '-z']:
      with self.subTest(option=option):
        result = self.rm(option, 'keep')
        self.assertEqual(result.returncode, 1)
        self.assertIsNone(self.trashed(result))
    result = self.rm('-dfPRrvx', 'keep')
    self.assertEqual((result.returncode, result.stdout.count('\n')), (0, 1), result.stderr)
    self.assertEqual(self.trashed(result), ['--', 'keep'])

  def test_directories_follow_rm_options(self):
    (self.work / 'full').mkdir()
    (self.work / 'full/child').write_text('data')
    (self.work / 'empty').mkdir()
    (self.work / 'link').symlink_to('full')
    (self.work / 'broken').symlink_to('missing-target')
    for args, code, moved in [
      (['full'], 1, None),
      (['-f', 'full'], 1, None),
      (['-r', 'full'], 0, ['--', 'full']),
      (['-R', 'full/'], 0, ['--', 'full/']),
      (['-d', 'empty'], 0, ['--', 'empty']),
      (['-d', 'full'], 1, None),
      (['link'], 0, ['--', 'link']),
      (['broken'], 0, ['--', 'broken']),
    ]:
      with self.subTest(args=args):
        result = self.rm(*args)
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertEqual(self.trashed(result), moved)

  def test_trash_failure_returns_error(self):
    self.make('keep')
    result = self.rm('keep', env=dict(self.env, FAKE_TRASH_EXIT='5'))
    self.assertEqual(result.returncode, 1)
    self.assertEqual(self.trashed(result), ['--', 'keep'])

  def test_missing_trash_leaves_target_and_does_not_use_path_shadow(self):
    self.trash.unlink()
    self.make('keep.txt')
    shadow = self.bin / 'trash'
    shadow.write_text('#!/bin/sh\nexit 0\n')
    shadow.chmod(0o755)
    env = dict(self.env, PATH=str(self.bin) + ':/usr/bin:/bin')
    result = self.rm('-f', 'keep.txt', env=env)
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual((self.work / 'keep.txt').read_text(), 'data')

  def test_fish_and_child_shell_resolve_the_managed_rm(self):
    self.make('argument with spaces')
    command = [shutil.which('fish'), '--no-config', '-c',
               'source "$argv[1]"; /bin/sh -c \'rm -f -- "argument with spaces"\'',
               str(ROOT / 'config/.config/fish/config.fish')]
    result = subprocess.run(command, env=self.env, cwd=self.work,
                            capture_output=True, text=True, timeout=10)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(self.trashed(result), ['--', 'argument with spaces'])


if __name__ == '__main__':
  unittest.main()
