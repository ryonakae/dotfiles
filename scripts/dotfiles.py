#!/usr/bin/env python3
import argparse
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


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


def host_snapshot(directory):
  values = json.loads((directory / "host.json").read_text())
  if not isinstance(values, dict) or set(values) != {"username", "homeDirectory"}:
    raise ValueError("host.json must contain only username and homeDirectory (no secrets)")
  if not isinstance(values["username"], str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", values["username"]):
    raise ValueError("host.json requires a non-empty macOS username")
  home = values["homeDirectory"]
  if not isinstance(home, str) or not home.startswith("/") or home == "/" or ".." in Path(home).parts:
    raise ValueError("host.json requires an absolute homeDirectory other than /")
  # Only the declared fields enter the store, never the local directory itself.
  with tempfile.TemporaryDirectory(prefix="dotfiles-host-") as temporary:
    (Path(temporary) / "host.json").write_text(json.dumps(values) + "\n")
    return nix("store", "add-path", "--name", "dotfiles-host", temporary)


def locked_source(directory):
  baseline = nix("flake", "metadata", f"git+{ROOT.as_uri()}",
                 "--no-update-lock-file", "--json", json_output=True)
  source = "path:" + baseline["path"]
  host = "path:" + host_snapshot(directory)
  overrides = ["--override-input", "host", host, "--no-write-lock-file"]
  resolved = nix("flake", "metadata", source, *overrides, "--json", json_output=True)
  before = copy.deepcopy(baseline["locks"])
  after = copy.deepcopy(resolved["locks"])
  host_node = before["nodes"][before["root"]]["inputs"]["host"]
  if not isinstance(host_node, str):
    raise ValueError("host must be a direct non-Flake input")
  for graph in (before, after):
    node = graph["nodes"].pop(host_node)
    if node.get("flake") is not False or node.get("inputs"):
      raise ValueError("host must be a non-Flake leaf")
  if before != after:
    raise ValueError("host override changed public dependencies; run an explicit update first")
  return source, overrides


def main():
  parser = argparse.ArgumentParser(description="Build the locked macOS configuration")
  parser.add_argument("action", choices=["build", "update"])
  parser.add_argument("target", nargs="?")
  parser.add_argument("--host", type=Path, default=Path.home() / ".config/dotfiles/host")
  args = parser.parse_args()
  if args.action == "update":
    target = args.target or "all"
    graph = json.loads((ROOT / "flake.lock").read_text())
    public = set(graph["nodes"][graph["root"]]["inputs"]) - {"host"}
    if target != "all" and target not in public:
      parser.error("unknown update target; available: all, " + ", ".join(sorted(public)))
    targets = [] if target == "all" else [target]
    print("Updating inputs: " + ", ".join(sorted(public) if target == "all" else targets), flush=True)
    nix("flake", "update", *targets, "--flake", str(ROOT))
    return
  if args.target:
    parser.error("build does not accept an update target")
  source, overrides = locked_source(args.host)
  nix("flake", "check", source, *overrides)
  result = nix("build", source + "#darwinConfigurations.mac.system",
               *overrides, "--no-link", "--json", json_output=True)
  print(result[0]["outputs"]["out"])


if __name__ == "__main__":
  try:
    main()
  except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
    print(f"dotfiles: {error}", file=sys.stderr)
    sys.exit(1)
