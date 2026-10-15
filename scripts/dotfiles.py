#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import pwd
import signal
import subprocess
import sys
import threading
import time
from contextlib import contextmanager


ROOT = Path(__file__).resolve().parents[1]
TARGET_USER = 'ryo.nakae'
TARGET_HOME = Path('/Users/ryo.nakae')
BREW = Path('/opt/homebrew/bin/brew')
MISE = Path('/opt/homebrew/bin/mise')
SUDO_REFRESH_INTERVAL = 30
SUDO_REFRESH_TIMEOUT = 10


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


def interactive_user(parser):
  if os.geteuid() == 0:
    parser.error('run setup as the target user, not with sudo')
  if os.environ.get('APP_SANDBOX_CONTAINER_ID') == 'agent-safehouse':
    parser.error('setup must be run by the user outside Safehouse after migration approval')
  if not sys.stdin.isatty():
    parser.error('setup requires an interactive terminal for confirmation')


def user_home():
  user = pwd.getpwuid(os.getuid())
  home = Path(user.pw_dir).resolve()
  if (user.pw_name != TARGET_USER or home != TARGET_HOME.resolve()
      or not os.environ.get('HOME') or home != Path(os.environ['HOME']).resolve()):
    raise ValueError('run as the configured user with their configured user home and HOME')
  return user, home


def executable(path):
  return path.is_file() and os.access(path, os.X_OK)


def check_homebrew():
  prefix = BREW.parents[1]
  for path in (prefix / '.managed_by_nix_darwin', prefix / 'Library/.homebrew-is-managed-by-nix'):
    if os.path.lexists(path):
      raise ValueError('Nix-managed Homebrew detected; use the separately approved one-time migration, not setup')
  for path in (BREW, prefix / 'Library/Homebrew'):
    if path.resolve().is_relative_to(Path('/nix/store')):
      raise ValueError('Nix-managed Homebrew detected; use the separately approved one-time migration, not setup')
  if not executable(BREW) and (os.path.lexists(BREW) or (prefix.exists() and any(prefix.iterdir()))):
    raise ValueError(f'unknown existing Homebrew prefix or executable: {prefix}; inspect before installing')


def confirm(word, purpose):
  if input(f"Type '{word}' to {purpose}: ").strip() != word:
    raise ValueError(f'{purpose} cancelled')


def setup(configurations):
  declarations = [ROOT / 'mise.toml']
  declarations += [ROOT / f'mise.{name}.toml' for name in configurations]
  brewfiles = [ROOT / 'brew' / f'Brewfile.{name}' for name in configurations]
  protected = [*declarations, *brewfiles, ROOT / 'scripts/macos-settings.sh']
  if 'default' in configurations:
    protected += [ROOT / 'config/.config/mise/config.base.toml', ROOT / 'scripts/hermes_plists.py',
                  ROOT / 'mise.hermes.toml', ROOT / 'scripts/hermes-install.py']
  snapshot = {}
  environment = {key: value for key, value in os.environ.items()
                 if not key.startswith('MISE_') or key == 'MISE_DATA_DIR'}
  environment.update(
    MISE_ENV=','.join(configurations),
    MISE_CEILING_PATHS=str(ROOT.parent),
    MISE_GLOBAL_CONFIG_FILE=str(ROOT / 'mise.toml'),
    MISE_SYSTEM_CONFIG_FILE=str(ROOT / 'mise.toml'),
  )
  mise = [str(MISE), '-C', str(ROOT), '-E', ','.join(configurations)]
  completed = []
  stage = 'preflight'

  def check_declarations():
    user_home()
    check_homebrew()
    for path, expected in snapshot.items():
      if path.read_bytes() != expected:
        raise ValueError(f'declaration changed after confirmation: {path}; stop and review')

  def run(label, command, *, cwd=ROOT, refresh=None, env=None, **kwargs):
    nonlocal stage
    stage = label
    check_declarations()
    if refresh:
      refresh.check()
    result = subprocess.run(command, cwd=cwd, env=environment if env is None else env, check=True, **kwargs)
    completed.append(label)
    if refresh:
      refresh.check()
    check_declarations()
    return result

  try:
    user, home = user_home()
    check_homebrew()
    snapshot = {path: path.read_bytes() for path in protected}
    environment.update(HOME=str(home), USER=user.pw_name, LOGNAME=user.pw_name,
                       PATH=f'{BREW.parent}:{BREW.parents[1] / "sbin"}:' + environment.get('PATH', '/usr/bin:/bin'))
    subprocess.run(['/usr/bin/xcode-select', '-p'], check=True, stdout=subprocess.PIPE, text=True)
    print(f'Checkout: {ROOT}\nTarget user: {user.pw_name} ({home})')
    print('Configurations (in order): ' + ', '.join(configurations))
    print('Setup installs/updates selected Brewfiles, obtains repositories, places links and applies selected macOS settings.')
    print('No cleanup, service restart, shell change, automatic retry or rollback is performed.')
    confirm('setup', 'approve this complete setup scope')
    check_declarations()
    if not executable(BREW):
      stage = 'Homebrew initial install'
      installer_url = 'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh'
      print(f'Homebrew is missing. Official installer: {installer_url}\nPrefix: {BREW.parents[1]}')
      confirm('install', 'install Homebrew with the official installer')
      installer = run('Homebrew installer download', ['/usr/bin/curl', '-fsSL', installer_url], stdout=subprocess.PIPE, text=True)
      with sudo_authentication() as refresh:
        run('Homebrew initial install', ['/bin/bash', '-c', installer.stdout], refresh=refresh)
      refresh.check()
      check_homebrew()
      if not executable(BREW):
        raise ValueError(f'Homebrew installer did not provide {BREW}')
    stage = 'Homebrew setup authentication'
    with sudo_authentication() as refresh:
      missing = [name for name in ('mise', 'uv') if not executable(BREW.parent / name)]
      if missing:
        run('setup foundation', [str(BREW), 'install', *missing], refresh=refresh)
      for name, brewfile in zip(configurations, brewfiles):
        run(f'brew bundle {name}', [str(BREW), 'bundle', '--file=' + str(brewfile)], refresh=refresh)
    refresh.check()
    for path in (BREW, MISE, BREW.parent / 'uv'):
      if not executable(path):
        raise ValueError(f'required setup tool missing after Homebrew: {path}')
    stage = 'mise trust'
    for path in declarations:
      print(f'Trust only this declaration: {path}\n{snapshot[path].decode("utf-8")}')
    confirm('trust', 'trust only these declarations')
    for path in declarations:
      run(f'mise trust {path.name}', [*mise, 'trust', str(path)])
    run('mise repos update', [*mise, 'bootstrap', 'repos', 'update', '--yes'])
    run('mise dry-run', [*mise, 'dot', 'apply', '--dry-run'], timeout=60)
    print('Inspect destinations and unknown files/links before approving. Dry-run success does not guarantee apply success.')
    stage = 'mise apply'
    confirm('apply', 'apply the displayed placement plan')
    run('mise apply', [*mise, 'dot', 'apply', '--yes'])
    if 'default' in configurations:
      stage = 'link verification'
      for destination, source in (('.config/fish/config.fish', '.config/fish/config.fish'),
                                  ('.config/mise/config.toml', '.config/mise/config.base.toml')):
        link = home / destination
        source_file = ROOT / 'config' / source
        if (not link.is_symlink() or not source_file.is_file()
            or Path(os.path.abspath(link.parent / link.readlink())) != source_file):
          raise ValueError(f'configuration link does not point to live checkout: {link}')
      completed.append('link verification')
      home_env = dict(environment, MISE_ENV='', MISE_CEILING_PATHS=str(home),
                      MISE_GLOBAL_CONFIG_FILE=str(ROOT / 'config/.config/mise/config.base.toml'))
      home_mise = [str(MISE), '-C', str(home)]
      run('mise runtimes', [*home_mise, 'install', 'node', 'python', 'ruby', 'bun', 'aqua:aws/aws-cli'], cwd=home, env=home_env)
      hermes_declaration = ROOT / 'mise.hermes.toml'
      hermes_mise = [str(MISE), '-C', str(ROOT), '-E', 'hermes']
      hermes_env = dict(environment, MISE_ENV='hermes')
      stage = 'Hermes declaration trust'
      print(f'Trust only this declaration: {hermes_declaration}\n{snapshot[hermes_declaration].decode("utf-8")}')
      confirm('trust', 'trust the Hermes lifecycle declaration')
      run('Hermes declaration trust', [*hermes_mise, 'trust', str(hermes_declaration)], env=hermes_env)
      run('Hermes initial install task', [*hermes_mise, 'run', 'hermes:install'], env=hermes_env)
      run('Hermes plist placement', ['/usr/bin/python3', str(ROOT / 'scripts/hermes_plists.py')])
    stage = 'macOS settings'
    with sudo_authentication() as refresh:
      run('mise macOS defaults', [*mise, 'bootstrap', 'macos', 'defaults', 'apply', '--yes'], refresh=refresh)
      for name in configurations:
        run(f'macOS supplement {name}', ['/bin/bash', str(ROOT / 'scripts/macos-settings.sh'), name], refresh=refresh)
    refresh.check()
    print('Setup complete: ' + ', '.join(completed))
    print('No services were restarted. Apply updated Hermes definitions explicitly with hermes-gateway / hermes-dashboard when needed.')
  except BaseException:
    print(f"Setup stopped at {stage}. Completed: {', '.join(completed) or 'none'}", file=sys.stderr)
    print('Setup is non-atomic. Inspect partial changes; no automatic retry or rollback was attempted.', file=sys.stderr)
    print('Do not repeat the whole setup automatically: resume the failed stage with standard brew bundle / mise trust / repos update / dot apply / install / macOS commands after review.', file=sys.stderr)
    raise


def main():
  parser = argparse.ArgumentParser(description='Set up explicitly selected macOS configurations')
  parser.add_argument('action', choices=['setup'])
  parser.add_argument('configurations', nargs='+', choices=['default', 'private', 'work'])
  args = parser.parse_args()
  if len(set(args.configurations)) != len(args.configurations):
    parser.error('duplicate configurations are not allowed')
  interactive_user(parser)
  setup(args.configurations)


if __name__ == '__main__':
  try:
    main()
  except (OSError, ValueError, KeyError, EOFError, subprocess.SubprocessError) as error:
    print(f'dotfiles: {error}', file=sys.stderr)
    sys.exit(1)
