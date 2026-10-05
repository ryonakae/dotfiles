#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


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
  print("This entrypoint does not back up files, manage Hermes, or roll back automatically.")
  if input("Type 'switch' to confirm application: ").strip() != "switch":
    raise ValueError("switch cancelled; no activation performed")
  subprocess.run([target["hermesCheck"]], check=True)
  subprocess.run([
    "/usr/bin/sudo", str(Path(system) / "sw/bin/darwin-rebuild"),
    "switch", "--flake", f"{source}#{configuration}", "--no-update-lock-file",
  ], check=True)


def main():
  parser = argparse.ArgumentParser(description="Build, apply, or update the locked macOS configuration")
  parser.add_argument("action", choices=["build", "switch", "update"])
  parser.add_argument("target", nargs="?")
  parser.add_argument("--configuration", help="darwinConfigurations name (default: mac)")
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
  configuration = args.configuration if args.configuration is not None else "mac"
  if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", configuration):
    parser.error("configuration must be a Nix identifier (letters, digits, underscores or hyphens)")
  if args.action == "switch":
    if os.geteuid() == 0:
      parser.error("run switch as the target user, not with sudo; only darwin-rebuild is elevated")
    if os.environ.get("APP_SANDBOX_CONTAINER_ID") == "agent-safehouse":
      parser.error("switch must be run by a human outside Safehouse after migration approval")
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
