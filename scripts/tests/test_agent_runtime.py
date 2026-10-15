import json
import os
import plistlib
from pathlib import Path
import select
import shlex
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
    adapter_source = ROOT / 'config/.local/libexec/hermes-gui-launchctl/launchctl'
    if adapter_source.exists():
      adapter = self.home / '.local/libexec/hermes-gui-launchctl/launchctl'
      adapter.parent.mkdir(parents=True)
      adapter.write_text(adapter_source.read_text().replace(
        '/bin/launchctl', shlex.quote(str(self.bin / 'launchctl'))))
      adapter.chmod(0o755)
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
    self.env['APP_SANDBOX_CONTAINER_ID'] = 'agent-safehouse'
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
        enabled = set(features.removeprefix('--enable=').split(','))
        self.assertTrue({'keychain', 'process-control'} <= enabled)
        if name in ('gateway', 'dashboard'):
          self.assertTrue(enabled.isdisjoint({'clipboard', 'cleanshot', 'xcode'}))
        self.assertEqual([arg for arg in args if arg.startswith('--append-profile=')],
                         ['--append-profile=' + str(runtime / 'compatibility.sb'),
                          '--append-profile=' + str(runtime / 'local-overrides.sb')])

  def test_cli_wrappers_forward_only_user_arguments(self):
    self.install_runtime()
    self.program('safehouse', (self.bin / 'probe').read_text())
    fish_dir = self.fish_dir
    for name in ['claude', 'codex', 'gemini', 'hermes', 'pi', 'opencode']:
      for arguments in [[], ['--model', 'model with spaces', ''], ['prompt with spaces'],
                        ['--', 'prompt with spaces', '--'], ['--model', 'model', '--', 'prompt']]:
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
          expected = [executable, *arguments]
          if name == 'claude':
            insertion = 1 + arguments.index('--') if '--' in arguments else len(expected)
            expected[insertion:insertion] = ['--mcp-config', str(self.home / '.claude/mcp.json')]
          self.assertEqual(args[args.index('--') + 1:], expected)

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

  def gateway_status(self, service_output, *, disabled_output=None, print_code=0,
                     disabled_code=0, keep_alive=False, run_at_load=True, disabled=True,
                     terminal=False):
    plist = self.home / 'Library/LaunchAgents/ai.hermes.gateway.plist'
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_bytes(plistlib.dumps({
      'Label': 'ai.hermes.gateway', 'Disabled': disabled,
      'RunAtLoad': run_at_load, 'KeepAlive': keep_alive,
    }))
    if disabled_output is None:
      disabled_output = 'disabled services = {\n\t"ai.hermes.gateway" => false\n}'
    self.program('launchctl', '#!' + sys.executable + '\n'
      'import sys\n'
      'args = sys.argv[1:]\n'
      'if args[0] == "print":\n'
      f'  print({service_output!r})\n'
      f'  sys.exit({print_code})\n'
      'elif args[0] == "print-disabled":\n'
      f'  print({disabled_output!r})\n'
      f'  sys.exit({disabled_code})\n'
      'else: sys.exit(88)\n')
    command = [shutil.which('fish'), '--no-config', '-c',
               'source "$argv[1]/hermes-gateway.fish"; hermes-gateway status', str(self.fish_dir)]
    if not terminal:
      return subprocess.run(command, env=self.env, capture_output=True, text=True, timeout=15)
    master, slave = os.openpty()
    output = bytearray()
    try:
      result = subprocess.run(command, env=dict(self.env, TERM='xterm-256color'),
                              stdout=slave, stderr=slave, timeout=15)
      while select.select([master], [], [], 0)[0]:
        output.extend(os.read(master, 4096))
    finally:
      os.close(slave)
      os.close(master)
    return subprocess.CompletedProcess(command, result.returncode, output.decode(), '')

  def test_gateway_status_reports_running_process_and_configured_policy(self):
    result = self.gateway_status(
      'gui/501/ai.hermes.gateway = {\n\tstate = running\n\tpid = 10250\n'
      '\tprogram = /nix/store/example-safe-hermes-gateway.sh\n}')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn('Gateway: running (PID 10250)', result.stdout)
    self.assertIn('Program: /nix/store/example-safe-hermes-gateway.sh', result.stdout)
    self.assertIn('Start at login: enabled', result.stdout)
    self.assertIn('Restart on crash (plist): disabled', result.stdout)
    self.assertEqual(result.stderr, '')

  def test_gateway_status_colors_terminal_states_but_not_piped_output(self):
    for state, code, color in [('running', 0, '32'), ('not running', 1, '33')]:
      with self.subTest(state=state):
        output = (f'gui/501/ai.hermes.gateway = {{\n\tstate = {state}\n\tpid = 10250\n'
                  '\tprogram = /nix/store/example-safe-hermes-gateway.sh\n}')
        result = self.gateway_status(output, terminal=True)
        self.assertEqual(result.returncode, code, result.stdout)
        self.assertIn(f'\x1b[{color}m{state}', result.stdout)
        self.assertIn('Restart on crash (plist)', result.stdout)
        piped = self.gateway_status(output)
        self.assertEqual(piped.returncode, code)
        self.assertNotIn('\x1b[', piped.stdout + piped.stderr)
    for output, code in [('', 5), ('unexpected output', 0)]:
      result = self.gateway_status(output, print_code=code, terminal=True)
      self.assertNotEqual(result.returncode, 0)
      self.assertIn('\x1b[31mGateway:', result.stdout)

  def test_gateway_status_distinguishes_stopped_and_unavailable_services(self):
    stopped = self.gateway_status(
      'gui/501/ai.hermes.gateway = {\n\tstate = not running\n'
      '\tprogram = /nix/store/example-safe-hermes-gateway.sh\n}')
    self.assertEqual(stopped.returncode, 1, stopped.stderr)
    self.assertIn('Gateway: not running', stopped.stdout)
    self.assertNotIn('PID', stopped.stdout)
    for code in [113, 5]:
      with self.subTest(code=code):
        result = self.gateway_status('', print_code=code)
        self.assertEqual(result.returncode, code)
        self.assertIn('Gateway: unavailable', result.stderr)
        if code == 113:
          self.assertIn('not registered', result.stderr)
          self.assertNotIn('query failed', result.stderr)
        else:
          self.assertIn('query failed', result.stderr)
          self.assertNotIn('not registered', result.stderr)
        self.assertNotIn('Gateway: running', result.stdout)

  def test_gateway_status_rejects_unknown_or_incomplete_service_output(self):
    for output in [
      '', 'unexpected output',
      'gui/501/ai.hermes.gateway = {\n\tstate = running\n'
      '\tprogram = /nix/store/example-safe-hermes-gateway.sh\n}',
      'gui/501/ai.hermes.gateway = {\n\tstate = running\n\tpid = 0\n'
      '\tprogram = /nix/store/example-safe-hermes-gateway.sh\n}',
    ]:
      with self.subTest(output=output):
        result = self.gateway_status(output)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Gateway: unknown', result.stderr)

  def test_gateway_status_reads_policy_and_launchd_overrides(self):
    output = ('gui/501/ai.hermes.gateway = {\n\tstate = running\n\tpid = 10250\n'
              '\tprogram = /nix/store/example-safe-hermes-gateway.sh\n}')
    for override, default, expected in [
      ('enabled', True, 'enabled'), ('false', True, 'enabled'),
      ('disabled', False, 'disabled'), ('true', False, 'disabled'),
      (None, True, 'disabled'), (None, False, 'enabled'),
    ]:
      with self.subTest(override=override, default=default):
        overrides = '\tdisabled services = {\n'
        if override is not None:
          overrides += f'\t\t"ai.hermes.gateway" => {override}\n'
        overrides += '\t}'
        result = self.gateway_status(output, disabled_output=overrides,
                                     disabled=default, keep_alive=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f'Start at login: {expected}', result.stdout)
        self.assertIn('Restart on crash (plist): enabled', result.stdout)
    result = self.gateway_status(output, run_at_load=False)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn('Start at login: disabled', result.stdout)

  def test_gateway_status_fails_when_policy_cannot_be_read(self):
    output = ('gui/501/ai.hermes.gateway = {\n\tstate = running\n\tpid = 10250\n'
              '\tprogram = /nix/store/example-safe-hermes-gateway.sh\n}')
    for kwargs in [
      {'disabled_output': 'unexpected output'},
      {'disabled_output': 'disabled services = {\n\t"ai.hermes.gateway" => unknown\n}'},
      {'disabled_code': 5}, {'keep_alive': {'SuccessfulExit': False}},
    ]:
      with self.subTest(kwargs=kwargs):
        result = self.gateway_status(output, **kwargs)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Restart on crash (plist): disabled', result.stdout)

  def test_service_managers_use_stable_hermes_and_propagate_native_failure(self):
    hermes = self.home / '.local/libexec/hermes'
    hermes.parent.mkdir(parents=True, exist_ok=True)
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
      'gateway': {'stop': ['gateway', 'stop']},
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

  def service_action(self, service, action, **settings):
    domain = f'gui/{os.getuid()}'
    self.env.update(SERVICE=service, DOMAIN=domain, GUI_LOADED='1', NATIVE_EXIT='0',
                    QUERY_EXIT='0', DOMAIN_EXIT='0', BOOTOUT_EXIT='0', NATIVE_REMOVES='0',
                    BOOTSTRAP_FAILURES='0', BOOTSTRAP_EXIT='5')
    self.env.update({key: str(value) for key, value in settings.items()})
    log = Path(self.directory.name) / 'service-operations'
    log.write_text('')
    self.env['SERVICE_LOG'] = str(log)
    state = Path(self.directory.name) / 'gui-loaded'
    state.write_text(self.env['GUI_LOADED'])
    self.env['GUI_STATE'] = str(state)
    attempts = Path(self.directory.name) / 'bootstrap-attempts'
    attempts.write_text('0')
    self.env['BOOTSTRAP_ATTEMPTS'] = str(attempts)
    self.program('sleep', '#!/bin/sh\nexit 0\n')
    (self.home / '.hermes').mkdir(exist_ok=True)
    plist = self.home / f'Library/LaunchAgents/ai.hermes.{service}.plist'
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_text('Nix-owned definition')
    launchctl = self.program('launchctl', '#!' + sys.executable + '\n'
      'import json, os, pathlib, sys\n'
      'a = sys.argv[1:]; e = os.environ; d = e["DOMAIN"]; label = "ai.hermes." + e["SERVICE"]\n'
      'state = pathlib.Path(e["GUI_STATE"])\n'
      'with open(e["SERVICE_LOG"], "a") as f: f.write(json.dumps(a) + "\\n")\n'
      'if a == ["managername"]: print("Background")\n'
      'elif a == ["print", d]:\n'
      '  print(d + " = {\\n\\tservices = {\\n\\t}\\n}"); sys.exit(int(e["DOMAIN_EXIT"]))\n'
      'elif a == ["print", d + "/" + label]:\n'
      '  if int(e["QUERY_EXIT"]): sys.exit(int(e["QUERY_EXIT"]))\n'
      '  if state.read_text() == "0":\n'
      '    print("Could not find service", file=sys.stderr); sys.exit(113)\n'
      '  print(d + "/" + label + " = {\\n\\tstate = running\\n\\tpid = 123\\n\\tprogram = /nix/store/wrapper\\n}")\n'
      'elif a == ["print", d.replace("gui/", "user/") + "/" + label]: print("user job exists")\n'
      'elif a == ["bootout", d + "/" + label]:\n'
      '  if int(e["BOOTOUT_EXIT"]): sys.exit(int(e["BOOTOUT_EXIT"]))\n'
      '  state.write_text("0")\n'
      'elif a == ["bootstrap", d, os.environ["HOME"] + "/Library/LaunchAgents/" + label + ".plist"]:\n'
      '  attempts = pathlib.Path(e["BOOTSTRAP_ATTEMPTS"]); count = int(attempts.read_text()) + 1\n'
      '  attempts.write_text(str(count))\n'
      '  if count <= int(e["BOOTSTRAP_FAILURES"]): sys.exit(int(e["BOOTSTRAP_EXIT"]))\n'
      '  state.write_text("1")\n'
      'elif a in [["enable", d + "/" + label], ["disable", d + "/" + label]]: pass\n'
      'else: print("forbidden launchctl request: " + repr(a), file=sys.stderr); sys.exit(88)\n')
    hermes = self.home / '.local/libexec/hermes'
    hermes.parent.mkdir(parents=True, exist_ok=True)
    hermes.write_text('#!' + sys.executable + '\n'
      'import json, os, subprocess, sys\n'
      'e = os.environ\n'
      'with open(e["SERVICE_LOG"], "a") as f: f.write(json.dumps(["native", *sys.argv[1:]]) + "\\n")\n'
      'if int(e["NATIVE_EXIT"]): sys.exit(int(e["NATIVE_EXIT"]))\n'
      'if e["SERVICE"] == "gateway":\n'
      '  d = e["DOMAIN"]; label = "/ai.hermes.gateway"\n'
      '  if subprocess.run(["launchctl", "print", d + label], capture_output=True).returncode:\n'
      '    if subprocess.run(["launchctl", "print", d.replace("gui/", "user/") + label], capture_output=True).returncode == 0:\n'
      '      d = d.replace("gui/", "user/")\n'
      '    elif subprocess.check_output(["launchctl", "managername"], text=True).strip() != "Aqua": d = d.replace("gui/", "user/")\n'
      '  if e["NATIVE_REMOVES"] == "1": subprocess.run(["launchctl", "bootout", d + label], check=True)\n')
    hermes.chmod(0o755)
    command = [shutil.which('fish'), '--no-config', '-c',
               'set -p fish_function_path "$argv[1]"; '
               'source "$argv[1]/hermes-$argv[2].fish"; hermes-$argv[2] $argv[3]',
               str(self.fish_dir), service, action]
    result = subprocess.run(command, env=self.env, capture_output=True, text=True, timeout=15)
    operations = [json.loads(line) for line in log.read_text().splitlines()]
    self.assertEqual(plist.read_text(), 'Nix-owned definition')
    return result, operations

  def test_background_service_start_targets_gui_without_global_environment_mutation(self):
    for service in ['gateway', 'dashboard']:
      with self.subTest(service=service):
        result, operations = self.service_action(service, 'start')
        self.assertEqual(result.returncode, 0, result.stderr)
        domain = f'gui/{os.getuid()}'
        self.assertEqual(operations, [
          ['print', domain], ['enable', f'{domain}/ai.hermes.{service}'],
          ['bootstrap', domain, str(self.home / f'Library/LaunchAgents/ai.hermes.{service}.plist')],
        ])

  def test_restart_retries_transient_bootstrap_eio_without_repeating_shutdown(self):
    for service in ['gateway', 'dashboard']:
      with self.subTest(service=service):
        result, operations = self.service_action(service, 'restart', BOOTSTRAP_FAILURES=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sum(op[0] == 'bootstrap' for op in operations), 2)
        self.assertEqual(sum(op[0] == 'native' for op in operations), 1)
        self.assertEqual(sum(op[0] == 'bootout' for op in operations), 1)
        self.assertFalse(any('user/' in arg for op in operations for arg in op))

  def test_bootstrap_retry_is_bounded_and_only_for_eio_with_absent_service(self):
    cases = [
      ({'GUI_LOADED': 0, 'BOOTSTRAP_FAILURES': 99}, 5, 5),
      ({'GUI_LOADED': 0, 'BOOTSTRAP_FAILURES': 1, 'BOOTSTRAP_EXIT': 1}, 1, 1),
      ({'GUI_LOADED': 0, 'BOOTSTRAP_FAILURES': 1, 'QUERY_EXIT': 3}, 3, 1),
      ({'GUI_LOADED': 1, 'BOOTSTRAP_FAILURES': 1}, 5, 1),
    ]
    for service in ['gateway', 'dashboard']:
      for settings, code, attempts in cases:
        with self.subTest(service=service, settings=settings):
          result, operations = self.service_action(service, 'start', **settings)
          self.assertEqual(result.returncode, code, result.stderr)
          self.assertEqual(sum(op[0] == 'bootstrap' for op in operations), attempts)
          self.assertFalse(any(op[0] in ['native', 'bootout', 'disable'] for op in operations))

  def test_background_stop_gracefully_stops_native_and_unloads_only_gui_job(self):
    for service in ['gateway', 'dashboard']:
      for loaded, native_removes in [(1, 0), (1, 1), (0, 0), (0, 1)]:
        with self.subTest(service=service, loaded=loaded, native_removes=native_removes):
          result, operations = self.service_action(service, 'stop', GUI_LOADED=loaded,
                                                   NATIVE_REMOVES=native_removes)
          self.assertEqual(result.returncode, 0, result.stderr)
          domain = f'gui/{os.getuid()}'
          target = f'{domain}/ai.hermes.{service}'
          native = ['native', '--profile', 'default', service,
                    'stop' if service == 'gateway' else '--stop']
          self.assertIn(native, operations)
          self.assertEqual(operations[-1], ['disable', target])
          self.assertNotIn(['list'], operations)
          self.assertNotIn(['managername'], operations)
          self.assertFalse(any('user/' in arg for op in operations for arg in op))
          if loaded:
            self.assertIn(['bootout', target], operations)
          else:
            self.assertNotIn(['bootout', target], operations)

  def test_service_restart_does_not_start_after_failed_shutdown_or_query(self):
    for service in ['gateway', 'dashboard']:
      for settings in [dict(NATIVE_EXIT=23), dict(QUERY_EXIT=5), dict(QUERY_EXIT=3),
                       dict(QUERY_EXIT=125), dict(DOMAIN_EXIT=113), dict(BOOTOUT_EXIT=5)]:
        with self.subTest(service=service, settings=settings):
          result, operations = self.service_action(service, 'restart', **settings)
          self.assertNotEqual(result.returncode, 0)
          self.assertFalse(any(op[0] in ['bootstrap', 'enable', 'disable'] for op in operations))
          if 'QUERY_EXIT' in settings or 'DOMAIN_EXIT' in settings:
            self.assertFalse(any(op[0] == 'native' for op in operations))
          if 'NATIVE_EXIT' in settings:
            self.assertEqual(result.returncode, 23)

  def hermes_launcher(self, *, where_exit=0, where_output=None, executable=True):
    install = Path(self.directory.name) / 'mise Hermes install'
    (install / 'bin').mkdir(parents=True)
    hermes = install / 'bin/hermes'
    hermes.write_text('#!' + sys.executable + '\n'
      'import json, os, sys\n'
      'print(json.dumps({"args": sys.argv[1:], "cwd": os.getcwd(), '
      '"path": os.environ["PATH"], "unlisted": os.environ["UNLISTED_RUNTIME_VALUE"]}))\n'
      'sys.exit(23)\n')
    hermes.chmod(0o755 if executable else 0o644)
    mise = self.external_bin / 'mise'
    mise.write_text('#!' + sys.executable + '\n'
      'import json, os, sys\n'
      'with open(os.environ["MISE_LOG"], "w") as f:\n'
      '  json.dump({"args": sys.argv[1:], "cwd": os.getcwd()}, f)\n'
      f'print({str(install) if where_output is None else where_output!r})\n'
      f'sys.exit({where_exit})\n')
    mise.chmod(0o755)
    launcher = self.home / '.local/libexec/hermes'
    launcher.parent.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'config/.local/libexec/hermes'
    if source.exists():
      launcher.write_text(source.read_text().replace('/opt/homebrew/bin/mise', shlex.quote(str(mise))))
      launcher.chmod(0o755)
    self.env['MISE_LOG'] = str(Path(self.directory.name) / 'mise-query')
    return launcher

  def test_hermes_launcher_resolves_explicit_fork_without_changing_runtime_contract(self):
    launcher = self.hermes_launcher()
    adapter_dir = self.home / '.local/libexec/hermes-gui-launchctl'
    self.env['PATH'] = str(adapter_dir) + ':' + self.env['PATH']
    result = subprocess.run(['/bin/sh', str(launcher), '--profile', 'default', 'gateway', 'stop', ''],
                            env=self.env, cwd=self.project, capture_output=True, text=True, timeout=15)
    self.assertEqual(result.returncode, 23, result.stderr)
    self.assertEqual(json.loads(result.stdout), {
      'args': ['--profile', 'default', 'gateway', 'stop', ''],
      'cwd': str(self.project.resolve()), 'path': self.env['PATH'], 'unlisted': 'value with spaces',
    })
    self.assertEqual(json.loads(Path(self.env['MISE_LOG']).read_text()), {
      'args': ['where', 'pypi:git+https://github.com/ryonakae/hermes-agent.git@ryonakae'],
      'cwd': str(self.home.resolve()),
    })

  def test_hermes_launcher_stops_on_resolution_failure_or_missing_executable(self):
    for settings, expected in [({'where_exit': 31}, 31), ({'executable': False}, 126)]:
      with self.subTest(settings=settings):
        launcher = self.hermes_launcher(**settings)
        result = subprocess.run(['/bin/sh', str(launcher)], env=self.env, cwd=self.project,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, expected, result.stderr)
        self.assertEqual(result.stdout, '')
        shutil.rmtree(Path(self.directory.name) / 'mise Hermes install')

  def test_hermes_launcher_rejects_nonabsolute_resolution_instead_of_using_project_binary(self):
    malicious = self.project / 'relative/bin/hermes'
    malicious.parent.mkdir(parents=True)
    malicious.write_text('#!/bin/sh\nprintf wrong-hermes\n')
    malicious.chmod(0o755)
    launcher = self.hermes_launcher(where_output='relative')
    result = subprocess.run(['/bin/sh', str(launcher)], env=self.env, cwd=self.project,
                            capture_output=True, text=True, timeout=15)
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual(result.stdout, '')

  def test_service_update_only_prints_explicit_mise_update_guidance(self):
    log = Path(self.directory.name) / 'updates'
    self.env['UPDATE_LOG'] = str(log)
    for name in ['mise', 'hermes', 'launchctl']:
      self.program(name, '#!/bin/sh\nprintf forbidden >> "$UPDATE_LOG"\nexit 99\n')
    for service in ['gateway', 'dashboard']:
      with self.subTest(service=service):
        result = subprocess.run([shutil.which('fish'), '--no-config', '-c',
          'source "$argv[1]/hermes-$argv[2].fish"; hermes-$argv[2] update',
          str(self.fish_dir), service], env=self.env, cwd=self.project,
          capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Hermes is managed by mise', result.stderr)
        self.assertIn('install --force', result.stderr)
        self.assertIn('pypi:git+https://github.com/ryonakae/hermes-agent.git@ryonakae', result.stderr)
        self.assertFalse(log.exists())

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
