#!/usr/bin/env python3
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
MISE = Path('/opt/homebrew/bin/mise')
LOGIN_SHELL = '/opt/homebrew/bin/fish'
# install.sh's wire_shell_path test: without a match, products creates or appends to config.fish.
FISH_PATH_LINE = r'(?m)^[ \t]*fish_add_path.*\.local/bin'
ORIGIN = 'https://github.com/ryonakae/hermes-agent.git'
BRANCH = 'ryonakae'


def managed_paths(target, hermes_home):
  directories = [hermes_home, hermes_home / 'tools', target.parent, target, target / '.git',
                 target / 'scripts', target / '.hermes', target / '.hermes/bin']
  files = [target / 'scripts/install.sh', target / '.hermes/bin/hermes',
           target / '.git/config', target / '.git/HEAD',
           target / '.hermes-bootstrap-complete', target / '.hermes-bootstrap-complete.tmp',
           target / '.install_method']
  for path in [*directories, *files]:
    for ancestor in (path, *path.parents):
      if ancestor.is_symlink():
        raise ValueError(f'symlink in managed path: {ancestor}')
    if os.path.lexists(path) and not (path.is_dir() if path in directories else path.is_file()):
      raise ValueError(f'unknown managed path type: {path}')
  if os.path.lexists(target / '.hermes-bootstrap-complete.tmp'):
    raise ValueError('unknown temporary completion marker; inspect before resuming')
  method = target / '.install_method'
  if method.exists() and method.read_text().strip() != 'git':
    raise ValueError('unknown .install_method; inspect before resuming')


def git(target, environment, *args):
  return subprocess.run(['git', '-C', str(target), *args], cwd=ROOT, env=environment,
                        check=True, text=True, capture_output=True).stdout.strip()


def checkout(target, environment):
  if not (target / '.git').is_dir():
    raise ValueError(f'unknown checkout: {target}')
  if Path(git(target, environment, 'rev-parse', '--show-toplevel')) != target:
    raise ValueError('Git worktree does not match the managed checkout')
  if git(target, environment, 'config', '--get-all', 'remote.origin.url') != ORIGIN:
    raise ValueError('checkout origin does not match the managed fork')
  if git(target, environment, 'symbolic-ref', '--short', 'HEAD') != BRANCH:
    raise ValueError('checkout branch does not match ryonakae')
  if git(target, environment, 'status', '--porcelain', '--untracked-files=all'):
    raise ValueError('dirty checkout; preserve and inspect local changes')
  return git(target, environment, 'rev-parse', 'HEAD')


def completed(target, head):
  marker = target / '.hermes-bootstrap-complete'
  try:
    record = json.loads(marker.read_text())
    if (type(record.get('schemaVersion')) is not int or record['schemaVersion'] != 1
        or record['pinnedCommit'] != head or record['pinnedBranch'] != BRANCH):
      raise ValueError('marker does not match checkout HEAD/branch/schema')
    datetime.strptime(record['completedAt'], '%Y-%m-%dT%H:%M:%S.%fZ')
  except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
    raise ValueError(f'incomplete checkout or unknown completion marker: {error}; inspect before resuming standard installer stages') from error
  executable = target / '.hermes/bin/hermes'
  if not executable.is_file() or not os.access(executable, os.X_OK):
    raise ValueError('incomplete checkout: .hermes/bin/hermes is not executable')


def main():
  parser = argparse.ArgumentParser(description='Install or explicitly update the managed Hermes checkout')
  parser.add_argument('operation', choices=('install', 'update'))
  parser.add_argument('--yes', action='store_true', help='skip confirmations already approved by setup')
  args = parser.parse_args()
  stage = 'preflight'
  try:
    if os.geteuid() == 0 or os.getuid() == 0:
      raise ValueError('run as the target user, not root or sudo')
    if os.environ.get('APP_SANDBOX_CONTAINER_ID') == 'agent-safehouse':
      raise ValueError('run outside Safehouse in a normal terminal')
    home = Path(os.environ.get('HOME', ''))
    if not home.is_absolute() or home != Path(pwd.getpwuid(os.getuid()).pw_dir):
      raise ValueError('HOME must match the current user')
    hermes_home = home / '.hermes'
    target = home / 'Dev/private/hermes-agent'
    if any(os.environ.get(key) for key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE')):
      raise ValueError('unset Git directory/worktree/index overrides before operating on Hermes')
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith('MISE_') or key == 'MISE_DATA_DIR'}
    environment.update(
      MISE_ENV='hermes',
      MISE_CEILING_PATHS=str(ROOT.parent),
      MISE_GLOBAL_CONFIG_FILE=str(ROOT / 'mise.toml'),
      MISE_SYSTEM_CONFIG_FILE=str(ROOT / 'mise.toml'),
    )
    managed_paths(target, hermes_home)
    exists = os.path.lexists(target)
    if exists:
      completed(target, checkout(target, environment))
      if args.operation == 'install':
        print('Hermes is already complete; no checkout or dependency changes.')
        return
    elif args.operation == 'update':
      raise ValueError('Hermes is absent; use the hermes:install task first')
    fish_config = home / '.config/fish/config.fish'
    try:
      fish_ready = re.search(FISH_PATH_LINE, fish_config.read_text()) is not None
    except OSError:
      fish_ready = False
    if not fish_ready:
      raise ValueError(f'{fish_config} has no fish_add_path line for ~/.local/bin; apply the default configuration first')
    if not sys.stdin.isatty():
      raise ValueError('an interactive terminal is required for confirmation')
    print(f'Hermes {args.operation}: {target}; origin {ORIGIN}; branch {BRANCH}')
    print('Uses standard installer stages; may add managed uv, Python/Node runtimes and dependencies under ~/.hermes.')
    print('The products stage also builds the launcher and ~/.local/bin/hermes*, syncs bundled skills and profiles, and migrates ~/.hermes/config.yaml.')
    print('No services are stopped or started; stop any active Hermes services explicitly before updating.')
    if not args.yes and input(f"Type '{args.operation}' to continue: ").strip() != args.operation:
      raise ValueError('cancelled')
    managed_paths(target, hermes_home)
    if exists:
      completed(target, checkout(target, environment))
      (target / '.hermes-bootstrap-complete').unlink()
    elif os.path.lexists(target):
      raise ValueError('checkout appeared during confirmation; inspect before continuing')
    stage = 'repos update' if exists else 'repos apply'
    repos = ['update', str(target)] if exists else ['apply']
    subprocess.run([str(MISE), '-C', str(ROOT), '-E', 'hermes',
                    'bootstrap', 'repos', *repos, '--yes'],
                   cwd=ROOT, env=environment, check=True)
    managed_paths(target, hermes_home)
    head = checkout(target, environment)
    print(f'Using Hermes revision {head}')
    stages = ('python-deps', 'products', 'complete') if exists else ('venv', 'python-deps', 'products', 'complete')
    if not args.yes and input(f"Type '{args.operation}' to run {', '.join(stages)} at revision {head}: ").strip() != args.operation:
      raise ValueError('installer stages cancelled; checkout is incomplete, inspect before resuming')
    managed_paths(target, hermes_home)
    if checkout(target, environment) != head:
      raise ValueError('checkout HEAD changed during revision confirmation')
    for stage in stages:
      command = ['/bin/bash', str(target / 'scripts/install.sh'), '--stage', stage,
                 '--dir', str(target), '--branch', BRANCH, '--hermes-home', str(hermes_home)]
      managed_paths(target, hermes_home)
      # products appends a PATH line to the rc file of $SHELL; during setup that is still the shell
      # from before chsh, while fish already carries the line.
      stage_environment = dict(environment, SHELL=LOGIN_SHELL) if stage == 'products' else environment
      if stage == 'complete':
        if checkout(target, environment) != head:
          raise ValueError('checkout HEAD changed during dependency synchronization')
      print(f'Hermes installer stage: {stage}', flush=True)
      subprocess.run(command, cwd=target, env=stage_environment, check=True)
    managed_paths(target, hermes_home)
    completed(target, checkout(target, environment))
    print('Hermes installation complete. Additional optional features are not verified.')
  except (ValueError, OSError, subprocess.SubprocessError, EOFError, KeyboardInterrupt) as error:
    print(f'Hermes stopped at {stage}: {error}; no automatic retry or rollback.', file=sys.stderr)
    if stage == 'complete' and os.path.lexists(target / '.hermes-bootstrap-complete'):
      try:
        marker = target / '.hermes-bootstrap-complete'
        if any(path.is_symlink() for path in (marker, *marker.parents)):
          raise ValueError('symlink completion marker')
        completed(target, head)
        marker.unlink()
      except (ValueError, OSError) as marker_error:
        print(f'Completion marker not removed; inspect unknown state: {marker_error}', file=sys.stderr)
    if stage in ('venv', 'python-deps', 'products', 'complete'):
      print(f'Inspect this stage and any partial changes before manually resuming with the standard installer: {shlex.join(command)}', file=sys.stderr)
      print('Run later stages only after this stage succeeds; run complete last.', file=sys.stderr)
    raise SystemExit(130 if isinstance(error, KeyboardInterrupt) else 1)


if __name__ == '__main__':
  main()
