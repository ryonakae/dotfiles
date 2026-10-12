#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import stat
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ETC = Path('/etc')


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
    return
  print("These files will stop being active shell configuration. Keep this terminal open.")
  print("If custom settings still need migration, cancel now. Backups will not be overwritten.")
  if input("Type 'backup' to preserve these shell files and continue: ").strip() != 'backup':
    raise ValueError('shell backup cancelled; no activation performed')
  subprocess.run([
    '/usr/bin/sudo', '/usr/bin/python3', '-c', SHELL_BACKUP_PROGRAM, json.dumps(files),
  ], check=True)


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


def switch_target(source, configuration):
  target = nix(
    "eval", f"{source}#darwinConfigurations.{configuration}.config", "--no-update-lock-file",
    "--apply", '''c: let h = c.home-manager.users.${c.system.primaryUser}; in {
      username = h.home.username;
      homeDirectory = h.home.homeDirectory;
      hermesCheck = toString h.xdg.configFile."hermes/check-stopped.sh".source;
    }''', "--json", json_output=True,
  )
  user = pwd.getpwuid(os.getuid())
  if target["username"] != user.pw_name or Path(target["homeDirectory"]).resolve() != Path(user.pw_dir).resolve():
    raise ValueError("switch must run as the configured user with their configured home directory")
  return target


def switch(system, source, configuration, target):
  profile = Path("/nix/var/nix/profiles/system")
  if os.path.lexists(profile):
    previous = profile.resolve(strict=True)
  else:
    previous = "none (first activation)"
  print(f"Source: {source}")
  print(f"Candidate system: {system}")
  print(f"Previous system profile: {previous}")
  print(f"Target user: {target['username']} ({target['homeDirectory']})")
  print("This applies system settings, Homebrew and Home Manager configuration.")
  print("Review the changes; stop apps or preserve files only where conflicts require it.")
  print("Native file checks run during activation. Failure may leave a new profile and partial changes.")
  print("Shell files may require a separately confirmed backup; no general backup, Hermes management, or automatic rollback is performed.")
  if input("Type 'switch' to confirm application: ").strip() != "switch":
    raise ValueError("switch cancelled; no activation performed")
  subprocess.run([target["hermesCheck"]], check=True)
  prepare_shell_files(system)
  subprocess.run([
    "/usr/bin/sudo", str(Path(system) / "sw/bin/darwin-rebuild"),
    "switch", "--flake", f"{source}#{configuration}", "--no-update-lock-file",
  ], check=True)


def main():
  parser = argparse.ArgumentParser(description="Build, apply, or update the locked macOS configuration")
  parser.add_argument("action", choices=["build", "switch", "update"])
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
  if args.target:
    parser.error(f"{args.action} does not accept an update target")
  configuration = args.configuration if args.configuration is not None else "default"
  if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", configuration):
    parser.error("configuration must be a Nix identifier (letters, digits, underscores or hyphens)")
  if args.action == "switch":
    if os.geteuid() == 0:
      parser.error("run switch as the target user, not with sudo; shell backup and darwin-rebuild are elevated when needed")
    if os.environ.get("APP_SANDBOX_CONTAINER_ID") == "agent-safehouse":
      parser.error("switch must be run by the user outside Safehouse after migration approval")
    if not sys.stdin.isatty():
      parser.error("switch requires an interactive terminal for confirmation")
  source = locked_source()
  target = switch_target(source, configuration) if args.action == "switch" else None
  nix("flake", "check", source, "--no-update-lock-file")
  result = nix("build", f"{source}#darwinConfigurations.{configuration}.system",
               "--no-update-lock-file", "--no-link", "--json", json_output=True)
  system = result[0]["outputs"]["out"]
  print(system)
  if args.action == "switch":
    switch(system, source, configuration, target)


if __name__ == "__main__":
  try:
    main()
  except (OSError, ValueError, KeyError, EOFError, subprocess.CalledProcessError) as error:
    print(f"dotfiles: {error}", file=sys.stderr)
    sys.exit(1)
