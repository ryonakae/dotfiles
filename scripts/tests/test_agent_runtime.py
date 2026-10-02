import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / 'config/.config/agent-safehouse'


class AgentRuntimeTests(unittest.TestCase):
  def setUp(self):
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.home = Path(self.directory.name) / 'home with spaces'
    self.bin = self.home / '.local/bin'
    self.bin.mkdir(parents=True)
    self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin) + ':' + os.environ['PATH'],
                    UNLISTED_RUNTIME_VALUE='value with spaces')
    self.program('rm', '#!/bin/sh\nexit 0\n')
    self.program('dotenvx', '#!' + sys.executable + '\n'
      'import os, sys\n'
      'args = sys.argv[1:]\n'
      'assert args[:4] == ["run", "--quiet", "--strict", "--no-armor"]\n'
      'assert args[4:9] == ["-f", os.environ["HOME"] + "/.config/.env", "-fk", "/dev/null", "--"]\n'
      'os.environ["AGENT_TEST_TOKEN"] = "dummy-token"\n'
      'os.execvp(args[9], args[9:])\n')
    self.program('probe', '#!' + sys.executable + '\n'
      'import json, os, sys\n'
      'print(json.dumps({"args": sys.argv[1:], "token": os.environ["AGENT_TEST_TOKEN"], '
      '"unlisted": os.environ["UNLISTED_RUNTIME_VALUE"], "first_path": os.environ["PATH"].split(":")[0]}))\n'
      'sys.exit(23)\n')

  def program(self, name, content):
    path = self.bin / name
    path.write_text(content)
    path.chmod(0o755)
    return path

  def run_helper(self, *args):
    return subprocess.run(['/bin/sh', str(RUNTIME / 'run-with-agent-env.sh'), *args],
                          env=self.env, capture_output=True, text=True, timeout=15)

  def install_runtime(self):
    runtime = self.home / '.config/agent-safehouse'
    runtime.mkdir(parents=True)
    shutil.copy2(RUNTIME / 'run-with-agent-env.sh', runtime)
    for name in ['compatibility.sb', 'local-overrides.sb']:
      (runtime / name).touch()
    return runtime

  def test_all_wrappers_inject_before_sandbox_and_preserve_service_arguments(self):
    runtime = self.install_runtime()
    self.program('safehouse', (self.bin / 'probe').read_text())
    self.program('mise', '#!/bin/sh\nwhile [ "$1" != -- ]; do shift; done\nshift\n'
                 'PATH="/mise-shims:$PATH"; export PATH\nexec "$@"\n')
    fish_dir = ROOT / 'config/.config/fish/functions'
    fish = [shutil.which('fish'), '--no-config', '-c']
    wrappers = {
      'safe': (fish + ['source "$argv[1]/__safehouse_args.fish"; '
                      'source "$argv[1]/safe.fish"; safe probe "argument with spaces"', str(fish_dir)],
               ['probe', 'argument with spaces']),
      'hermes': (fish + ['source "$argv[1]/__safehouse_args.fish"; '
                        'source "$argv[1]/hermes.fish"; hermes computer-use doctor', str(fish_dir)],
                 ['hermes', 'computer-use', 'doctor']),
      'gateway': (['/bin/bash', str(RUNTIME / 'safe-hermes-gateway.sh')],
                  [str(self.home / '.hermes/hermes-agent/venv/bin/hermes'), '--profile', 'default', 'gateway', 'run']),
      'dashboard': (['/bin/bash', str(RUNTIME / 'safe-hermes-dashboard.sh')],
                    [str(self.home / '.hermes/hermes-agent/venv/bin/hermes'), 'dashboard', '--host',
                     '127.0.0.1', '--port', '3210', '--no-open', '--insecure']),
    }
    self.env.update(HERMES_DASHBOARD_HOST='127.0.0.1', HERMES_DASHBOARD_PORT='3210')
    for name, (command, tail) in wrappers.items():
      with self.subTest(wrapper=name):
        result = subprocess.run(command, env=self.env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 23, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['token'], 'dummy-token')
        self.assertEqual(payload['unlisted'], 'value with spaces')
        self.assertEqual(payload['first_path'], str(self.bin))
        args = payload['args']
        self.assertIn('--env', args)
        self.assertIn('--add-dirs=' + str(self.home), args)
        self.assertEqual(args[-len(tail):], tail)
        self.assertEqual([arg for arg in args if arg.startswith('--append-profile=')],
                         ['--append-profile=' + str(runtime / 'compatibility.sb'),
                          '--append-profile=' + str(runtime / 'local-overrides.sb')])

  def test_missing_protection_profile_prevents_sandbox_start(self):
    runtime = self.install_runtime()
    (runtime / 'local-overrides.sb').unlink()
    self.program('safehouse', '#!/bin/sh\necho unsafe-start\n')
    fish_dir = ROOT / 'config/.config/fish/functions'
    command = [shutil.which('fish'), '--no-config', '-c',
               'source "$argv[1]/__safehouse_args.fish"; '
               'source "$argv[1]/safe.fish"; safe probe', str(fish_dir)]
    result = subprocess.run(command, env=self.env, capture_output=True, text=True, timeout=15)
    self.assertEqual(result.returncode, 1, result.stderr)
    self.assertEqual(result.stdout, '')
    self.assertIn('required Safehouse profile', result.stderr)

  def test_decryption_failure_does_not_start_command(self):
    self.program('dotenvx', '#!/bin/sh\nprintf "decryption failed\\n" >&2\nexit 42\n')
    result = self.run_helper('probe')
    self.assertEqual(result.returncode, 42)
    self.assertEqual(result.stdout, '')
    self.assertEqual(result.stderr, 'decryption failed\n')

  def test_missing_rm_wrapper_does_not_start_command(self):
    (self.bin / 'rm').unlink()
    result = self.run_helper('probe')
    self.assertEqual(result.returncode, 127)
    self.assertEqual(result.stdout, '')
    self.assertIn('rm wrapper', result.stderr)

  def test_injects_environment_without_changing_arguments_or_exit_code(self):
    result = self.run_helper('probe', 'argument with spaces', '--flag', '')
    self.assertEqual(result.returncode, 23, result.stderr)
    self.assertEqual(json.loads(result.stdout), {
      'args': ['argument with spaces', '--flag', ''], 'token': 'dummy-token',
      'unlisted': 'value with spaces', 'first_path': str(self.bin),
    })
    self.assertEqual(result.stderr, '')


if __name__ == '__main__':
  unittest.main()
