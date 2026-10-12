#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
from contextlib import contextmanager


ROOT = Path(__file__).resolve().parents[1]
ETC = Path('/etc')
STORE = Path('/nix/store')
PROFILE = Path('/nix/var/nix/profiles/system')
CURRENT = Path('/run/current-system')
BREW = Path('/opt/homebrew/bin/brew')
SUDO_REFRESH_INTERVAL = 30
SUDO_REFRESH_TIMEOUT = 10


SHELL_BACKUP_PROGRAM = '''
import ctypes
import hashlib
import json
import os
import stat
import sys


def verify(path, expected):
  fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
  with os.fdopen(fd, 'rb') as file:
    info = os.fstat(file.fileno())
    if not stat.S_ISREG(info.st_mode):
      raise ValueError(f"Not a regular file: {path}")
    metadata = {key: getattr(info, key) for key in expected['metadata']}
    if metadata != expected['metadata'] or hashlib.sha256(file.read()).hexdigest() != expected['sha256']:
      raise ValueError(f"File changed after confirmation: {path}")


try:
  libc = ctypes.CDLL(None, use_errno=True)
  rename_exclusive = libc.renamex_np
  rename_exclusive.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
  rename_exclusive.restype = ctypes.c_int
  RENAME_EXCL = 0x00000004
  files = json.loads(sys.argv[1])
  for path, expected in files:
    verify(path, expected)
    if os.path.lexists(path + '.before-nix-darwin'):
      raise FileExistsError(f"Backup already exists: {path}.before-nix-darwin")
  for path, expected in files:
    backup = path + '.before-nix-darwin'
    verify(path, expected)
    # Rename preserves even a concurrently replaced source without clobbering a backup.
    if rename_exclusive(os.fsencode(path), os.fsencode(backup), RENAME_EXCL) != 0:
      error = ctypes.get_errno()
      raise OSError(error, os.strerror(error), backup)
    verify(backup, expected)
    print(f"Preserved {path} as {backup}", flush=True)
  for path, expected in files:
    if os.path.lexists(path):
      raise ValueError(f"Shell file reappeared during backup: {path}")
except (OSError, ValueError, AttributeError) as error:
  print(f"Shell backup stopped: {error}. Inspect both paths before retrying; no automatic restore was attempted.", file=sys.stderr)
  sys.exit(1)
'''


def prepare_shell_files(system):
  files = []
  for name in ('bashrc', 'zshrc'):
    if not (Path(system) / 'etc' / name).is_symlink():
      continue
    path = ETC / name
    try:
      info = path.lstat()
    except FileNotFoundError:
      continue
    if stat.S_ISLNK(info.st_mode):
      if os.readlink(path) == str(ETC / 'static' / name):
        continue
      raise ValueError(f"Unexpected shell link; inspect before switching: {path}")
    if not stat.S_ISREG(info.st_mode):
      raise ValueError(f"Not a regular shell file: {path}")
    backup = Path(str(path) + '.before-nix-darwin')
    if os.path.lexists(backup):
      raise ValueError(f"Backup already exists; inspect both paths: {path}, {backup}")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as file:
      info = os.fstat(file.fileno())
      if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"Not a regular shell file: {path}")
      content = file.read()
    expected = {
      'metadata': {key: getattr(info, key) for key in (
        'st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns')},
      'sha256': hashlib.sha256(content).hexdigest(),
    }
    files.append((str(path), expected))
    print(f"\nShell file: {path}\nPreserve as: {backup}\nContents (escaped):")
    for line in content.decode('utf-8', errors='backslashreplace').splitlines():
      print(repr(line))
  if not files:
    return []
  print("These files will stop being active shell configuration. Keep this terminal open.")
  print("If custom settings still need migration, cancel now. Backups will not be overwritten.")
  if input("Type 'backup' to preserve these shell files and continue: ").strip() != 'backup':
    raise ValueError('shell backup cancelled; no activation performed')
  return files


class SudoRefresh:
  def __init__(self):
    self.stop = threading.Event()
    self.failure = None

  def check(self):
    if self.failure:
      raise ValueError(f'sudo cache refresh failed ({self.failure}); reauthentication required; no automatic retry')

  def refresh(self):
    while not self.stop.wait(SUDO_REFRESH_INTERVAL):
      process = None
      try:
        process = subprocess.Popen(['/usr/bin/sudo', '-n', '-v'])
        deadline = time.monotonic() + SUDO_REFRESH_TIMEOUT
        while True:
          if self.stop.is_set():
            return
          remaining = deadline - time.monotonic()
          if remaining <= 0:
            raise subprocess.TimeoutExpired(process.args, SUDO_REFRESH_TIMEOUT)
          try:
            code = process.wait(timeout=min(0.1, remaining))
            if code:
              raise subprocess.CalledProcessError(code, process.args)
            break
          except subprocess.TimeoutExpired:
            if time.monotonic() >= deadline:
              raise
      except (OSError, subprocess.SubprocessError) as error:
        self.failure = str(error)
        print(f'sudo cache refresh failed: {error}; waiting for any active operation before stopping.', file=sys.stderr)
        return
      finally:
        if process is not None:
          if process.poll() is None:
            process.terminate()
            try:
              process.wait(timeout=2)
            except subprocess.TimeoutExpired:
              process.kill()
              process.wait()
          else:
            process.wait()


@contextmanager
def sudo_authentication():
  subprocess.run(['/usr/bin/sudo', '-v'], check=True)
  refresh = SudoRefresh()
  thread = threading.Thread(target=refresh.refresh, name='dotfiles-sudo-refresh')
  handlers = {}

  def interrupted(signum, frame):
    raise SystemExit(128 + signum)

  try:
    for signum in (signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
      handlers[signum] = signal.signal(signum, interrupted)
    thread.start()
    yield refresh
  finally:
    handlers[signal.SIGINT] = signal.getsignal(signal.SIGINT)
    for signum in handlers:
      signal.signal(signum, signal.SIG_IGN)
    try:
      refresh.stop.set()
      if thread.ident is not None:
        thread.join()
    finally:
      for signum, handler in handlers.items():
        signal.signal(signum, handler)


def nix(*args, json_output=False):
  executable = shutil.which("nix") or "/nix/var/nix/profiles/default/bin/nix"

  result = subprocess.run(
    [executable, "--extra-experimental-features", "nix-command flakes", *args],
    cwd=ROOT, stdout=subprocess.PIPE, text=True,
  )
  if result.returncode:
    print(result.stdout, end="", file=sys.stderr)
    result.check_returncode()
  return json.loads(result.stdout) if json_output else result.stdout.strip()


def locked_source():
  metadata = nix("flake", "metadata", f"git+{ROOT.as_uri()}",
                 "--no-update-lock-file", "--json", json_output=True)
  return "path:" + metadata["path"]


def configured_target(source, configuration):
  target = nix(
    "eval", f"{source}#darwinConfigurations.{configuration}.config", "--no-update-lock-file",
    "--apply", '''c: let h = c.home-manager.users.${c.system.primaryUser}; in {
      username = h.home.username;
      homeDirectory = h.home.homeDirectory;
      hermesCheck = toString h.xdg.configFile."hermes/check-stopped.sh".source;
    }''', "--json", json_output=True,
  )
  validate_user(target)
  return target


def validate_user(target):
  user = pwd.getpwuid(os.getuid())
  home = Path(target['homeDirectory']).resolve()
  if (target['username'] != user.pw_name or home != Path(user.pw_dir).resolve()
      or not os.environ.get('HOME') or home != Path(os.environ['HOME']).resolve()):
    raise ValueError('run as the configured user with their configured user home and HOME')


def artifact(path):
  system = Path(path).resolve(strict=True)
  if system.parent != STORE or not system.is_dir():
    raise ValueError('specify an existing system directly inside the Nix store')
  if (system / 'systemConfig').read_text().strip() != str(system):
    raise ValueError('invalid systemConfig self-reference')
  metadata = system / 'etc/dotfiles/build.json'
  if not metadata.is_file():
    raise ValueError('artifact has no dotfiles metadata; run build to create a new artifact')
  target = json.loads(metadata.read_text())
  if not isinstance(target, dict):
    raise ValueError('invalid artifact metadata: expected an object')
  for key in ('configuration', 'source', 'username', 'homeDirectory', 'hermesCheck', 'mise'):
    if not isinstance(target.get(key), str) or not target[key]:
      raise ValueError(f'invalid artifact metadata: {key}')
  if not Path(target['homeDirectory']).is_absolute():
    raise ValueError('invalid artifact home directory')
  if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]*', target['configuration']):
    raise ValueError('invalid artifact configuration')
  source = Path(target['source'])
  if not source.is_absolute() or source.parent != STORE or not source.is_dir():
    raise ValueError('invalid artifact source snapshot')
  for path in (system / 'activate', system / 'sw/bin/nix-env', system / 'sw/bin/darwin-rebuild',
               Path(target['hermesCheck']), Path(target['mise'])):
    if not path.is_absolute() or not path.resolve().is_relative_to(STORE) or not path.is_file() or not os.access(path, os.X_OK):
      raise ValueError(f'missing or non-executable artifact file: {path}')
  validate_user(target)
  return system, target


def profile_state(path):
  return str(path.resolve()) if os.path.lexists(path) else 'none (first activation)'


def switch(system, target):
  print(f"Source: {target['source']}")
  print(f"Configuration: {target['configuration']}")
  print(f"Candidate system: {system}")
  print(f"Previous system profile: {profile_state(PROFILE)}")
  print(f"Target user: {target['username']} ({target['homeDirectory']})")
  print("This applies system settings, Homebrew and Home Manager configuration.")
  print("Review the changes; stop apps or preserve files only where conflicts require it.")
  print("Native file checks run during activation. Failure may leave a new profile and partial changes.")
  print("Shell files may require a separately confirmed backup; no general backup, Hermes management, or automatic rollback is performed.")
  if input("Type 'switch' to confirm application: ").strip() != "switch":
    raise ValueError("switch cancelled; no activation performed")
  subprocess.run([target["hermesCheck"]], check=True)
  files = prepare_shell_files(system)
  completed = []
  try:
    with sudo_authentication() as refresh:
      refresh.check()
      if files:
        subprocess.run([
          '/usr/bin/sudo', '/usr/bin/python3', '-c', SHELL_BACKUP_PROGRAM, json.dumps(files),
        ], check=True)
        completed.append('shell preservation')
      refresh.check()
      subprocess.run([
        '/usr/bin/sudo', str(system / 'sw/bin/nix-env'), '-p', str(PROFILE), '--set', str(system),
      ], check=True)
      completed.append('profile registration')
      refresh.check()
      subprocess.run([
        '/usr/bin/sudo', str(system / 'sw/bin/darwin-rebuild'), 'activate',
      ], check=True)
      completed.append('activation')
      refresh.check()
      if PROFILE.resolve() != system or CURRENT.resolve() != system:
        raise ValueError('applied profile/current-system does not match candidate')
    refresh.check()
  except BaseException:
    print(f"Completed: {', '.join(completed) or 'none'}", file=sys.stderr)
    print(f'System profile: {profile_state(PROFILE)}; current-system: {profile_state(CURRENT)}', file=sys.stderr)
    print('Application is non-atomic; inspect partial changes before retrying. No rollback attempted.', file=sys.stderr)
    raise


def build(source, configuration):
  nix('flake', 'check', source, '--no-update-lock-file')
  result = nix('build', f'{source}#darwinConfigurations.{configuration}.system',
               '--no-update-lock-file', '--no-link', '--json', json_output=True)
  return result[0]['outputs']['out']


def setup(source, configuration):
  completed = []
  try:
    configured_target(source, configuration)
    system_path = build(source, configuration)
    completed.append('build')
    system, target = artifact(system_path)
    if target['source'] != source.removeprefix('path:') or target['configuration'] != configuration:
      raise ValueError('built artifact metadata does not match selected source/configuration')
    declaration = ROOT / 'mise.toml'
    expected = (Path(target['source']) / 'mise.toml').read_bytes()

    def check_declaration():
      if declaration.read_bytes() != expected:
        raise ValueError('checkout mise.toml changed since the build snapshot; stop and review before rebuilding')

    check_declaration()
    switch(system, target)
    completed.append('switch')
    mise = target['mise']
    for executable in (BREW, Path(mise)):
      if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ValueError(f'required tool missing after activation: {executable}')
    check_declaration()
    print(f'Configuration placement source (live Git checkout): {ROOT / "config"}')
    print('Nix uses the immutable artifact; configuration bodies remain live checkout files, not store copies.')
    print(f'Trust only this declaration: {declaration}\n{expected.decode("utf-8")}')
    if input("Type 'trust' to trust this file only: ").strip() != 'trust':
      raise ValueError('mise trust cancelled')
    check_declaration()
    subprocess.run([mise, '-C', str(ROOT), 'trust', str(declaration)], cwd=ROOT, check=True)
    completed.append('mise trust')
    check_declaration()
    subprocess.run([mise, '-C', str(ROOT), 'dot', 'apply', '--dry-run'], cwd=ROOT, timeout=60, check=True)
    completed.append('mise dry-run')
    print('Inspect destinations and unknown files/links before approving. Dry-run success does not guarantee apply success.')
    if input("Type 'apply' to apply the displayed placement plan: ").strip() != 'apply':
      raise ValueError('mise apply cancelled')
    check_declaration()
    subprocess.run([mise, '-C', str(ROOT), 'dot', 'apply'], cwd=ROOT, check=True)
    completed.append('mise apply')
    home = Path(target['homeDirectory'])
    for destination, source_file in (('.config/fish/config.fish', '.config/fish/config.fish'),
                                     ('.config/mise/config.toml', '.config/mise/config.base.toml')):
      link = home / destination
      source_file = ROOT / 'config' / source_file
      if (not link.is_symlink() or not source_file.is_file()
          or Path(os.path.abspath(link.parent / link.readlink())) != source_file):
        raise ValueError(f'configuration link does not point to live checkout: {link}')
    completed.append('link verification')
    print('Setup complete: ' + ', '.join(completed))
  except BaseException:
    print(f"Setup stopped. Completed: {', '.join(completed) or 'none'}", file=sys.stderr)
    if 'switch' in completed:
      print(f'Nix application succeeded; do not automatically switch again. Resume with standard mise trust / dot apply --dry-run / dot apply using {target["mise"]} -C {ROOT} after reviewing the failed stage.', file=sys.stderr)
    raise


def interactive_user(parser, action):
  if os.geteuid() == 0:
    parser.error(f'run {action} as the target user, not with sudo')
  if os.environ.get('APP_SANDBOX_CONTAINER_ID') == 'agent-safehouse':
    parser.error(f'{action} must be run by the user outside Safehouse after migration approval')
  if not sys.stdin.isatty():
    parser.error(f'{action} requires an interactive terminal for confirmation')


def main():
  parser = argparse.ArgumentParser(description="Build, apply, or update the locked macOS configuration")
  parser.add_argument("action", choices=["build", "switch", "setup", "update"])
  parser.add_argument("target", nargs="?")
  parser.add_argument("--configuration", help="darwinConfigurations name (default: default)")
  args = parser.parse_args()
  if args.action == "update":
    if args.configuration is not None:
      parser.error("update does not accept --configuration")
    target = args.target or "all"
    graph = json.loads((ROOT / "flake.lock").read_text())
    public = set(graph["nodes"][graph["root"]]["inputs"])
    if target != "all" and target not in public:
      parser.error("unknown update target; available: all, " + ", ".join(sorted(public)))
    targets = [] if target == "all" else [target]
    print("Updating inputs: " + ", ".join(sorted(public) if target == "all" else targets), flush=True)
    nix("flake", "update", *targets, "--flake", str(ROOT))
    return
  if args.action == 'switch':
    if args.configuration is not None or not args.target:
      parser.error('switch requires SYSTEM_PATH and does not accept --configuration; run build [--configuration NAME] first')
    interactive_user(parser, 'switch')
    system, target = artifact(args.target)
    switch(system, target)
    return
  if args.target:
    parser.error(f"{args.action} does not accept a target")
  configuration = args.configuration if args.configuration is not None else "default"
  if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", configuration):
    parser.error("configuration must be a Nix identifier (letters, digits, underscores or hyphens)")
  if args.action == 'setup':
    interactive_user(parser, 'setup')
    setup(locked_source(), configuration)
  else:
    print(build(locked_source(), configuration))


if __name__ == "__main__":
  try:
    main()
  except (OSError, ValueError, KeyError, EOFError, subprocess.SubprocessError) as error:
    print(f"dotfiles: {error}", file=sys.stderr)
    sys.exit(1)
