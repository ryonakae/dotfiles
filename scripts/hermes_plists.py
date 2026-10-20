#!/usr/bin/python3
import argparse
import os
from pathlib import Path
import plistlib
import stat
import sys
import tempfile


SERVICES = ('gateway',)


def definitions(home):
  path = ':'.join([str(home / '.local/bin'), str(home / '.local/share/mise/shims'),
                   '/usr/bin', '/bin', '/usr/sbin', '/sbin', '/opt/homebrew/bin', '/usr/local/bin'])
  result = {}
  for name in SERVICES:
    environment = {'HOME': str(home), 'HERMES_HOME': str(home / '.hermes'), 'PATH': path}
    result[f'ai.hermes.{name}.plist'] = plistlib.dumps({
      'Label': f'ai.hermes.{name}',
      'ProgramArguments': [str(home / f'.config/agent-safehouse/safe-hermes-{name}.sh')],
      'WorkingDirectory': str(home / '.hermes'),
      'EnvironmentVariables': environment,
      'Disabled': True, 'RunAtLoad': True, 'KeepAlive': True,
      'StandardOutPath': str(home / f'.hermes/logs/{name}.log'),
      'StandardErrorPath': str(home / f'.hermes/logs/{name}.error.log'),
    })
  return result


def read_existing(path):
  try:
    info = path.lstat()
  except FileNotFoundError:
    return None
  if stat.S_ISLNK(info.st_mode):
    raise OSError(f'plist path is a symlink: {path}')
  if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
    raise OSError(f'plist is not a user-owned regular file: {path}')
  return path.read_bytes()


def check_directories(home):
  if not home.is_absolute() or not home.is_dir():
    raise OSError(f'HOME must be an existing absolute directory: {home}')
  for path in (home, home / 'Library', home / 'Library/LaunchAgents'):
    try:
      info = path.lstat()
    except FileNotFoundError:
      continue
    if stat.S_ISLNK(info.st_mode):
      raise OSError(f'plist parent path is a symlink: {path}')
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
      raise OSError(f'plist parent is not a user-owned directory: {path}')


def main():
  argparse.ArgumentParser(description='Place Hermes LaunchAgent definitions without loading services.').parse_args()
  home = Path(os.environ['HOME'])
  check_directories(home)
  destination = home / 'Library/LaunchAgents'
  generated = definitions(home)
  existing = {name: read_existing(destination / name) for name in generated}
  candidates = {name: contents for name, contents in generated.items() if existing[name] != contents}
  if not candidates:
    print('Hermes: plist definitions are unchanged.')
    return 0
  for name in candidates:
    action = 'Replace differing' if (destination / name).exists() else 'Create'
    print(f'{action} Hermes plist: {destination / name}')
  if input('Place these definitions without starting or stopping services? [y/N] ').strip().lower() != 'y':
    print('Hermes: plist placement cancelled.', file=sys.stderr)
    return 1
  check_directories(home)
  for name, contents in existing.items():
    if read_existing(destination / name) != contents:
      raise OSError(f'plist changed during confirmation: {destination / name}')
  destination.mkdir(parents=True, exist_ok=True)
  for name, contents in candidates.items():
    path = destination / name
    with tempfile.NamedTemporaryFile(dir=destination, prefix=f'.{name}.', delete=False) as stream:
      temporary = Path(stream.name)
      try:
        stream.write(contents)
        stream.flush()
        check_directories(home)
        if read_existing(path) != existing[name]:
          raise OSError(f'plist changed during confirmation: {path}')
        os.replace(temporary, path)
      finally:
        temporary.unlink(missing_ok=True)
    print(f'Placed Hermes plist: {path}')
  return 0


if __name__ == '__main__':
  try:
    sys.exit(main())
  except (EOFError, OSError, KeyError) as error:
    print(f'Hermes: {error}', file=sys.stderr)
    sys.exit(1)
