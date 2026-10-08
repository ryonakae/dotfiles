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
    self.external_bin = Path(self.directory.name) / 'brew bin'
    self.external_bin.mkdir()
    self.runtime = self.home / '.config/agent-safehouse'
    self.runtime.mkdir(parents=True)
    self.fish_dir = Path(self.directory.name) / 'fish-functions'
    self.fish_dir.mkdir()
    for source in RUNTIME.glob('*.sh'):
      self.copy_wrapper(source, self.runtime / source.name)
    for source in (ROOT / 'config/.config/fish/functions').glob('*.fish'):
      self.copy_wrapper(source, self.fish_dir / source.name)
    self.env = dict(os.environ, HOME=str(self.home), PATH=str(self.bin) + ':' + str(self.external_bin) + ':' + os.environ['PATH'],
                    UNLISTED_RUNTIME_VALUE='value with spaces')
    self.env.pop('MISE_DATA_DIR', None)
    self.env.pop('PI_TELEMETRY', None)
    self.project = Path(self.directory.name) / 'another project'
    self.project.mkdir()
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
      '"unlisted": os.environ["UNLISTED_RUNTIME_VALUE"], "first_path": os.environ["PATH"].split(":")[0], '
      '"telemetry": os.environ.get("PI_TELEMETRY")}))\n'
      'sys.exit(23)\n')

  def program(self, name, content):
    path = (self.external_bin if name in ['dotenvx', 'safehouse'] else self.bin) / name
    path.write_text(content)
    path.chmod(0o755)
    return path

  def copy_wrapper(self, source, destination):
    # Redirect only external command boundaries, never the real Homebrew files.
    text = source.read_text()
    for name in ['dotenvx', 'safehouse']:
      text = text.replace('/opt/homebrew/bin/' + name, str(self.external_bin / name))
    destination.write_text(text)
    destination.chmod(source.stat().st_mode)

  def run_helper(self, *args):
    return subprocess.run(['/bin/sh', str(self.runtime / 'run-with-agent-env.sh'), *args],
                          env=self.env, cwd=self.project,
                          capture_output=True, text=True, timeout=15)

  def install_runtime(self):
    for name in ['compatibility.sb', 'local-overrides.sb']:
      (self.runtime / name).touch()
    return self.runtime

  def test_environment_injection_uses_trusted_dotenvx_not_path_shadow(self):
    shadow = Path(self.directory.name) / 'shadow'
    shadow.mkdir()
    (shadow / 'dotenvx').write_text('#!/bin/sh\nexit 99\n')
    (shadow / 'dotenvx').chmod(0o755)
    self.env['PATH'] = str(shadow) + ':/usr/bin:/bin'
    result = self.run_helper(str(self.bin / 'probe'))
    self.assertEqual(result.returncode, 23, result.stderr)
    self.assertEqual(json.loads(result.stdout)['token'], 'dummy-token')

  def test_noninteractive_children_use_mise_shims_and_preserve_project_cwd(self):
    probe = self.program('runtime-probe', '#!' + sys.executable + '\n'
      'import json, os, subprocess\n'
      'print(json.dumps({"path": os.environ["PATH"].split(":"), "cwd": os.getcwd(), '
      '"node": subprocess.check_output(["node"], text=True).strip()}))\n')
    inherited_path = '/usr/bin:/bin:' + str(self.external_bin)
    self.env['PATH'] = inherited_path
    for data_dir in [self.home / '.local/share/mise', Path(self.directory.name) / 'custom mise data']:
      with self.subTest(data_dir=data_dir):
        shims = data_dir / 'shims'
        shims.mkdir(parents=True)
        node = shims / 'node'
        node.write_text('#!' + sys.executable + '\nimport os\nprint(os.getcwd())\n')
        node.chmod(0o755)
        if data_dir != self.home / '.local/share/mise':
          self.env['MISE_DATA_DIR'] = str(data_dir)
        result = self.run_helper(str(probe))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['path'][:2], [str(self.bin), str(shims)])
        self.assertEqual(payload['path'][2:5], inherited_path.split(':'))
        self.assertIn('/opt/homebrew/bin', payload['path'])
        self.assertEqual(payload['cwd'], str(self.project.resolve()))
        self.assertEqual(payload['node'], str(self.project.resolve()))

  def test_noninteractive_runtime_resolves_rm_to_trash_wrapper(self):
    gtrash = self.program('gtrash', (self.bin / 'probe').read_text())
    wrapper = self.bin / 'rm'
    wrapper.write_text((ROOT / 'config/.local/bin/rm').read_text().replace(
      '/opt/homebrew/bin/gtrash', str(gtrash)))
    wrapper.chmod(0o755)
    self.env['PATH'] = '/usr/bin:/bin'
    result = self.run_helper('/bin/sh', '-c', 'rm -rf -- "argument with spaces"')
    self.assertEqual(result.returncode, 23, result.stderr)
    self.assertEqual(json.loads(result.stdout)['args'], ['put', '-rf', '--', 'argument with spaces'])

  def test_all_wrappers_inject_before_sandbox_and_preserve_service_arguments(self):
    runtime = self.install_runtime()
    self.program('safehouse', (self.bin / 'probe').read_text())
    shadow = self.bin / 'safehouse'
    shadow.write_text('#!/bin/sh\nexit 99\n')
    shadow.chmod(0o755)
    hermes = str(self.home / '.local/libexec/hermes')
    fish_dir = self.fish_dir
    fish = [shutil.which('fish'), '--no-config', '-c']
    wrappers = {
      'safe': (fish + ['source "$argv[1]/__safehouse_args.fish"; '
                      'source "$argv[1]/safe.fish"; safe probe "argument with spaces"', str(fish_dir)],
               ['probe', 'argument with spaces']),
      'agy': (fish + ['source "$argv[1]/__safehouse_args.fish"; '
                     'source "$argv[1]/safe.fish"; '
                     'source "$argv[1]/agy.fish"; agy --model "model with spaces" ""', str(fish_dir)],
              ['agy', '--dangerously-skip-permissions', '--model', 'model with spaces', '']),
      'hermes': (fish + ['source "$argv[1]/__safehouse_args.fish"; '
                        'source "$argv[1]/hermes.fish"; hermes computer-use doctor', str(fish_dir)],
                 [hermes, 'computer-use', 'doctor']),
      'gateway': (['/bin/bash', str(runtime / 'safe-hermes-gateway.sh')],
                  [hermes, '--profile', 'default', 'gateway', 'run']),
      'dashboard': (['/bin/bash', str(runtime / 'safe-hermes-dashboard.sh')],
                    [hermes, '--profile', 'default', 'dashboard', '--host',
                     '127.0.0.1', '--port', '3210', '--no-open']),
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
        self.assertIn('--allow-profile-writes', args)
        self.assertIn('--add-dirs=' + str(self.home), args)
        self.assertEqual(args[-len(tail):], tail)
        features = next(arg for arg in args if arg.startswith('--enable='))
        self.assertEqual(features, {
          'gateway': '--enable=macos-gui,ssh,agent-browser,docker,all-agents,wide-read,keychain,process-control',
          'dashboard': '--enable=ssh,docker,all-agents,wide-read,keychain,process-control',
        }.get(name, '--enable=macos-gui,ssh,cleanshot,agent-browser,docker,clipboard,all-agents,wide-read,keychain,xcode,process-control'))
        self.assertEqual([arg for arg in args if arg.startswith('--append-profile=')],
                         ['--append-profile=' + str(runtime / 'compatibility.sb'),
                          '--append-profile=' + str(runtime / 'local-overrides.sb')])

  def test_cli_wrappers_forward_only_user_arguments(self):
    self.install_runtime()
    self.program('safehouse', (self.bin / 'probe').read_text())
    fish_dir = self.fish_dir
    for name in ['claude', 'codex', 'gemini', 'hermes', 'pi', 'opencode']:
      for arguments in [[], ['--model', 'model with spaces', '']]:
        with self.subTest(wrapper=name, arguments=arguments):
          command = [shutil.which('fish'), '--no-config', '-c',
                     'source "$argv[1]/__safehouse_args.fish"; '
                     'source "$argv[1]/safe.fish"; '
                     'source "$argv[1]/$argv[2].fish"; $argv[2] $argv[3..-1]',
                     str(fish_dir), name, *arguments]
          result = subprocess.run(command, env=self.env, capture_output=True,
                                  text=True, timeout=15)
          self.assertEqual(result.returncode, 23, result.stderr)
          args = json.loads(result.stdout)['args']
          executable = str(self.home / '.local/libexec/hermes') if name == 'hermes' else name
          self.assertEqual(args[args.index('--') + 1:], [executable, *arguments])

  def test_pi_disables_telemetry_at_sandbox_boundary(self):
    self.install_runtime()
    self.program('safehouse', (self.bin / 'probe').read_text())
    self.env['PI_TELEMETRY'] = '1'
    command = [shutil.which('fish'), '--no-config', '-c',
               'source "$argv[1]/__safehouse_args.fish"; '
               'source "$argv[1]/safe.fish"; '
               'source "$argv[1]/pi.fish"; pi', str(self.fish_dir)]
    result = subprocess.run(command, env=self.env, capture_output=True, text=True, timeout=15)
    self.assertEqual(result.returncode, 23, result.stderr)
    self.assertEqual(json.loads(result.stdout)['telemetry'], '0')

  def test_service_managers_use_stable_hermes_and_propagate_native_failure(self):
    hermes = self.home / '.local/libexec/hermes'
    hermes.parent.mkdir(parents=True)
    hermes.write_text('#!' + sys.executable + '\n'
      'import json, os, sys\n'
      'print(json.dumps({"args": sys.argv[1:], "home": os.environ["HERMES_HOME"]}))\n'
      'sys.exit(23)\n')
    hermes.chmod(0o755)
    self.program('hermes', '#!/bin/sh\nexit 99\n')
    self.program('launchctl', '#!' + sys.executable + '\n'
      'import sys\n'
      'if sys.argv[1:] == ["managername"]: print("Aqua")\n'
      'elif sys.argv[1] == "print": pass\n'
      'else: sys.exit(88)\n')
    for service, native_arguments in {
      'gateway': {'status': ['gateway', 'status'], 'stop': ['gateway', 'stop']},
      'dashboard': {'status': ['dashboard', '--status'], 'stop': ['dashboard', '--stop']},
    }.items():
      for action, arguments in native_arguments.items():
        with self.subTest(service=service, action=action):
          command = [shutil.which('fish'), '--no-config', '-c',
                     'source "$argv[1]/hermes-$argv[2].fish"; hermes-$argv[2] $argv[3]',
                     str(self.fish_dir), service, action]
          result = subprocess.run(command, env=self.env, capture_output=True,
                                  text=True, timeout=15)
          self.assertEqual(result.returncode, 23, result.stderr)
          payload = json.loads(next(line[line.index('{'):] for line in result.stdout.splitlines() if '{' in line))
          self.assertEqual(payload, {'args': ['--profile', 'default', *arguments],
                                    'home': str(self.home / '.hermes')})

  def test_missing_protection_profile_prevents_sandbox_start(self):
    runtime = self.install_runtime()
    (runtime / 'local-overrides.sb').unlink()
    self.program('safehouse', '#!/bin/sh\necho unsafe-start\n')
    fish_dir = self.fish_dir
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

  def test_injects_environment_without_changing_arguments_or_exit_code(self):
    result = self.run_helper('probe', 'argument with spaces', '--flag', '')
    self.assertEqual(result.returncode, 23, result.stderr)
    self.assertEqual(json.loads(result.stdout), {
      'args': ['argument with spaces', '--flag', ''], 'token': 'dummy-token',
      'unlisted': 'value with spaces', 'first_path': str(self.bin), 'telemetry': None,
    })
    self.assertEqual(result.stderr, '')


if __name__ == '__main__':
  unittest.main()
