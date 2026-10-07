import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class HermesTmpdirTests(unittest.TestCase):
  def test_tmpdir_at_safehouse_boundary(self):
    user_tmp = subprocess.check_output(
      ['/usr/bin/getconf', 'DARWIN_USER_TEMP_DIR'], text=True
    ).strip()
    with tempfile.TemporaryDirectory() as directory:
      base = Path(directory)
      bin_dir = base / 'bin'
      bin_dir.mkdir()
      custom = base / 'custom temp'
      custom.mkdir()
      readonly = base / 'readonly'
      readonly.mkdir(mode=0o500)
      not_directory = base / 'file'
      not_directory.touch()
      safehouse = bin_dir / 'safehouse'
      safehouse.write_text(
        '#!' + sys.executable + '\n'
        'import json, os, sys, tempfile\n'
        'value = os.environ.get("TMPDIR")\n'
        'print(json.dumps({"tmpdir": value, "args": sys.argv[1:]}))\n'
        'if value:\n'
        '  with tempfile.TemporaryFile(dir=value): pass\n'
        'sys.exit(23)\n'
      )
      safehouse.chmod(0o755)
      runtime = base / '.config/agent-safehouse'
      runtime.mkdir(parents=True)
      def copy_wrapper(source, destination):
        # Keep native sandbox startup outside the fixture's subprocess boundary.
        text = source.read_text()
        for name in ['dotenvx', 'safehouse']:
          text = text.replace('/opt/homebrew/bin/' + name, str(bin_dir / name))
        destination.write_text(text)
        destination.chmod(source.stat().st_mode)

      for name in ['run-with-agent-env.sh', 'safe-hermes-gateway.sh', 'safe-hermes-dashboard.sh']:
        copy_wrapper(ROOT / 'config/.config/agent-safehouse' / name, runtime / name)
      for name in ['compatibility.sb', 'local-overrides.sb']:
        (runtime / name).touch()
      dotenvx = bin_dir / 'dotenvx'
      dotenvx.write_text('#!/bin/sh\nwhile [ "$1" != -- ]; do shift; done\nshift\nexec "$@"\n')
      dotenvx.chmod(0o755)
      fish_dir = base / 'fish-functions'
      fish_dir.mkdir()
      for name in ['__safehouse_args.fish', 'hermes.fish']:
        copy_wrapper(ROOT / 'config/.config/fish/functions' / name, fish_dir / name)
      commands = {
        'cli': [shutil.which('fish'), '--no-config', '-c',
                'source "$argv[1]/__safehouse_args.fish"; '
                'source "$argv[1]/hermes.fish"; hermes computer-use doctor',
                str(fish_dir)],
        'gateway': ['/bin/bash', str(runtime / 'safe-hermes-gateway.sh')],
        'dashboard': ['/bin/bash', str(runtime / 'safe-hermes-dashboard.sh')],
      }
      cases = {
        'unset': (None, user_tmp),
        'empty': ('', user_tmp),
        'missing': (str(base / 'missing'), user_tmp),
        'readonly': (str(readonly), user_tmp),
        'file': (str(not_directory), user_tmp),
        'custom': (str(custom), str(custom)),
        'user': (user_tmp, user_tmp),
      }
      try:
        for wrapper, command in commands.items():
          for case, (value, expected) in cases.items():
            with self.subTest(wrapper=wrapper, case=case):
              env = dict(os.environ, PATH=str(bin_dir) + ':' + os.environ['PATH'], HOME=str(base),
                         HERMES_DASHBOARD_HOST='127.0.0.1', HERMES_DASHBOARD_PORT='3210')
              env.pop('TMPDIR', None)
              if value is not None:
                env['TMPDIR'] = value
              result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=15)
              payload = json.loads(result.stdout)
              self.assertEqual(payload['tmpdir'], expected)
              self.assertEqual(result.returncode, 23, result.stderr)
              self.assertEqual(result.stderr, '')
              if wrapper == 'cli':
                self.assertEqual(payload['args'][-3:], [str(base / '.local/libexec/hermes'), 'computer-use', 'doctor'])
              elif wrapper == 'gateway':
                self.assertEqual(payload['args'][-4:], ['--profile', 'default', 'gateway', 'run'])
              else:
                self.assertEqual(payload['args'][-5:], ['--host', '127.0.0.1', '--port', '3210', '--no-open'])
      finally:
        readonly.chmod(0o700)


if __name__ == '__main__':
  unittest.main()
