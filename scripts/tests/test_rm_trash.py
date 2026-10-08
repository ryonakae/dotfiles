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


class RmTrashTests(unittest.TestCase):
  def setUp(self):
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.home = Path(self.directory.name) / 'home with spaces'
    self.bin = self.home / '.local/bin'
    self.bin.mkdir(parents=True)
    self.gtrash = self.home / 'brew bin/gtrash'
    self.gtrash.parent.mkdir()
    self.gtrash.write_text('#!' + sys.executable + '\n'
      'import json, os, sys\n'
      'print(json.dumps({"args": sys.argv[1:], "only_home": os.getenv("GTRASH_ONLY_HOME_TRASH"), '
      '"fallback": os.getenv("GTRASH_HOME_TRASH_FALLBACK_COPY")}))\n'
      'sys.exit(23)\n')
    self.gtrash.chmod(0o755)
    self.wrapper = self.bin / 'rm'
    self.wrapper.write_text(WRAPPER.read_text().replace('/opt/homebrew/bin/gtrash', str(self.gtrash)))
    self.wrapper.chmod(0o755)
    self.env = dict(os.environ, HOME=str(self.home), PATH='/usr/bin:/bin',
                    GTRASH_ONLY_HOME_TRASH='true', GTRASH_HOME_TRASH_FALLBACK_COPY='true')

  def test_forwards_arguments_and_failure_without_copy_fallback(self):
    args = ['-rf', '--', 'name with spaces', '-option-like', '']
    result = subprocess.run([str(self.wrapper), *args], env=self.env,
                            capture_output=True, text=True, timeout=10)
    self.assertEqual(result.returncode, 23, result.stderr)
    self.assertEqual(json.loads(result.stdout), {
      'args': ['put', *args], 'only_home': 'false', 'fallback': 'false',
    })

  def test_missing_gtrash_leaves_target_and_does_not_use_path_shadow(self):
    self.gtrash.unlink()
    target = self.home / 'keep.txt'
    target.write_text('keep')
    shadow = self.bin / 'gtrash'
    shadow.write_text('#!/bin/sh\nexit 0\n')
    shadow.chmod(0o755)
    self.env['PATH'] = str(self.bin) + ':/usr/bin:/bin'
    result = subprocess.run([str(self.wrapper), '-f', str(target)], env=self.env,
                            capture_output=True, text=True, timeout=10)
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual(target.read_text(), 'keep')

  def test_fish_and_child_shell_resolve_the_managed_rm(self):
    command = [shutil.which('fish'), '--no-config', '-c',
               'source "$argv[1]"; /bin/sh -c \'rm -f -- "argument with spaces"\'',
               str(ROOT / 'config/.config/fish/shell-init.fish')]
    result = subprocess.run(command, env=self.env, capture_output=True, text=True, timeout=10)
    self.assertEqual(result.returncode, 23, result.stderr)
    self.assertEqual(json.loads(result.stdout)['args'], ['put', '-f', '--', 'argument with spaces'])


if __name__ == '__main__':
  unittest.main()
