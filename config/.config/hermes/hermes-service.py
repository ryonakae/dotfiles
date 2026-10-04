#!/usr/bin/env python3
"""Hermes lifecycle under the Nix-only definition/management ownership protocol.

Direct launchctl operations, Hermes installers, concurrent activation/management,
and processes escaping the observed service tree are unsupported. Nix is the sole
plist writer; activation must reject loaded jobs before replacing definitions.
launchctl text checks are deliberately version-sensitive, not a stable API.
Unknown output or legacy definitions require manual investigation, never a
force-stop fallback. Process churn and transient state writes can require retry;
no state, config, credentials, full argv or environment is printed or repaired.
"""

import argparse
import ast
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import plistlib
import pwd
import re
import signal
import stat
import subprocess
import sys
import time

import psutil

DEFINITIONS = Path('@definitions@')
KINDS = ("gateway", "dashboard")
TIMEOUT = 120
MAX_BYTES = 1024 * 1024


class Refused(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Refused(message)


def command(*args, data=None):
    result = subprocess.run(args, input=data, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=10, check=False)
    require(result.returncode == 0 and not result.stderr,
            f"{Path(args[0]).name} {args[1]} failed; state is unknown")
    require(len(result.stdout) <= MAX_BYTES, "probe output exceeds supported size")
    return result.stdout


def launchctl(*args):
    return command("/bin/launchctl", *args).decode("utf-8")


def metadata(path):
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def directory(path, uid, optional=False):
    info = metadata(path)
    if info is None and optional:
        return False
    require(info is not None and stat.S_ISDIR(info.st_mode) and info.st_uid == uid,
            "relevant directory is missing, linked, or not user-owned")
    require(path.resolve() == path, "relevant directory resolves through a symlink")
    return True


def read_file(path, uid=None, optional=False):
    info = metadata(path)
    if info is None and optional:
        return None
    require(info is not None and stat.S_ISREG(info.st_mode),
            "relevant file is missing or not a regular file")
    require(uid is None or (info.st_uid == uid and not info.st_mode & 0o022),
            "relevant file has unsafe ownership or permissions")
    require(info.st_size <= MAX_BYTES, "relevant file exceeds supported size")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        current = os.fstat(stream.fileno())
        require((info.st_dev, info.st_ino) == (current.st_dev, current.st_ino),
                "relevant file changed while opening")
        data = stream.read(MAX_BYTES + 1)
        after = os.fstat(stream.fileno())
    require(len(data) <= MAX_BYTES and
            (current.st_size, current.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            "relevant file changed while reading")
    return data


def json_value(data):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, "duplicate key in runtime state")
            value[key] = item
        return value

    return json.loads(data.decode("utf-8-sig"), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(
                          Refused("non-finite runtime state")))


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


@dataclass(frozen=True)
class Process:
    pid: int
    created: float
    parent: int
    uids: tuple
    argv: tuple

    @property
    def identity(self):
        return self.pid, self.created


def inspect(pid, uid):
    process = psutil.Process(pid)
    uids = tuple(process.uids())
    ours = uid in uids
    # Other users cannot own our runtime, but their parent links can reveal an unsafe descendant.
    if not ours:
        return Process(pid, 0, process.ppid(), uids, ())
    created = process.create_time()
    require(positive(created), "process creation time is unavailable")
    argv = tuple(process.cmdline())
    require(not ours or argv or process.status() == psutil.STATUS_ZOMBIE,
            "current-user process command line is unavailable")
    result = Process(pid, created, process.ppid(), uids, argv)
    require(psutil.Process(pid).create_time() == created, "process identity changed during census")
    return result


def census(uid):
    # process_iter silently skips vanished processes; a failed census cannot prove absence.
    for attempt in range(3):
        try:
            pids = psutil.pids()
            processes = {pid: inspect(pid, uid) for pid in pids}
            require(set(psutil.pids()) == set(pids), "process census changed; retry operation")
            return processes
        except psutil.NoSuchProcess:
            if attempt == 2:
                raise Refused("process census did not stabilize") from None
    raise Refused("process census failed")


def python_entry(argv):
    if not argv:
        return None
    name = Path(argv[0]).name
    if name in ("hermes", "hermes-gateway", "desktop-gateway.py"):
        return list(argv[1:]) if name == "hermes" else ["gateway", "run"]
    if not re.fullmatch(r"python(?:\d+(?:\.\d+)*)?", name):
        return None
    for index, token in enumerate(argv[1:], 1):
        if token == "-m":
            if index + 1 < len(argv) and argv[index + 1] in ("hermes_cli", "hermes_cli.main"):
                return list(argv[index + 2:])
            if index + 1 < len(argv) and argv[index + 1] == "gateway.run":
                return ["gateway", "run"]
            return None
        if token == "-c":
            if index + 1 >= len(argv):
                return None
            tree = ast.parse(argv[index + 1])
            aliases = {name.asname or name.name for node in ast.walk(tree)
                       if isinstance(node, ast.ImportFrom) and node.module == "hermes_cli.main"
                       for name in node.names if name.name == "main"}
            calls_main = any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                             and node.func.id in aliases for node in ast.walk(tree))
            runs_module = any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                              and node.func.attr == "run_module" and node.args
                              and isinstance(node.args[0], ast.Constant)
                              and node.args[0].value == "hermes_cli.main"
                              for node in ast.walk(tree))
            return list(argv[index + 2:]) if calls_main or runs_module else None
        if not token.startswith("-"):
            if token.endswith("/hermes_cli/main.py") or Path(token).name == "hermes":
                return list(argv[index + 1:])
            if token.endswith("/gateway/run.py") or Path(token).name == "desktop-gateway.py":
                return ["gateway", "run"]
            return None
    return None


def runtime(process):
    entry = python_entry(process.argv)
    if entry is None:
        return None
    filtered = []
    profiles = []
    index = 0
    while index < len(entry):
        token = entry[index]
        if token in ("--profile", "-p"):
            require(index + 1 < len(entry), "malformed Hermes profile argument")
            profiles.append(entry[index + 1])
            index += 2
            continue
        if token.startswith(("--profile=", "-p=")):
            profiles.append(token.split("=", 1)[1])
        else:
            filtered.append(token)
        index += 1
    if filtered[:2] == ["gateway", "run"]:
        kind = "gateway"
    elif filtered[:1] == ["dashboard"] and not any(
            flag in filtered for flag in ("--stop", "--status")):
        kind = "dashboard"
    else:
        kind = "other"
    return kind, profiles


def hermes_hint(process):
    return any(Path(token).name in ("hermes", "hermes-gateway", "desktop-gateway.py")
               or token.endswith(("/gateway/run.py", "/hermes_cli/main.py"))
               or "hermes_cli.main" in token or token in ("hermes_cli", "gateway.run")
               or re.search(r"safe-hermes-(?:gateway|dashboard)\.sh$", token)
               for token in process.argv)


def inventory(text, header=True):
    lines = text.splitlines()
    if header:
        require(lines and lines.pop(0).split() == ["PID", "Status", "Label"],
                "unsupported launchctl list header")
    jobs = {}
    for line in lines:
        parts = line.split()
        require(len(parts) == 3 and re.fullmatch(r"(?:-|[1-9]\d*)" if header else r"(?:-|\d+)", parts[0])
                and re.fullmatch(r"[-+]?\d+" if header else r"(?:-|[-+]?\d+)", parts[1])
                and parts[2] not in jobs, "malformed launchd job inventory")
        jobs[parts[2]] = None if parts[0] in ("-", "0") else int(parts[0])
    return jobs


class Controller:
    def __init__(self):
        self.uid = os.getuid()
        require(sys.platform == "darwin" and self.uid != 0 and os.geteuid() == self.uid,
                "requires an unprivileged macOS GUI session")
        self.home = Path(pwd.getpwuid(self.uid).pw_dir)
        require(os.environ.get("HOME") == str(self.home), "HOME does not match account home")
        directory(self.home, self.uid)
        self.hermes = self.home / ".hermes"
        self.domain = f"gui/{self.uid}"
        self.expected = {}
        self.raw = {}
        require(str(DEFINITIONS).startswith("/nix/store/"), "Nix definitions were not substituted")
        for kind in KINDS:
            label = f"ai.hermes.{kind}"
            data = read_file(DEFINITIONS / f"{label}.plist")
            definition = plistlib.loads(data)
            allowed = {"Label", "ProgramArguments", "WorkingDirectory", "EnvironmentVariables",
                       "Disabled", "RunAtLoad", "KeepAlive", "StandardOutPath", "StandardErrorPath"}
            require(isinstance(definition, dict) and set(definition) == allowed,
                    "unsupported generated definition")
            args = definition["ProgramArguments"]
            require(definition["Label"] == label and isinstance(args, list) and len(args) == 1
                    and isinstance(args[0], str) and args[0].startswith("/nix/store/")
                    and args[0].endswith(f"safe-hermes-{kind}.sh")
                    and definition["KeepAlive"] is False and definition["Disabled"] is True
                    and definition["RunAtLoad"] is True,
                    "generated definition violates the manual lifecycle contract")
            env = definition["EnvironmentVariables"]
            require(definition["WorkingDirectory"] == str(self.hermes)
                    and isinstance(env, dict) and set(env) == {"HOME", "HERMES_HOME", "PATH"}
                    and env["HOME"] == str(self.home) and env["HERMES_HOME"] == str(self.hermes)
                    and isinstance(env["PATH"], str) and bool(env["PATH"]),
                    "generated definition has unsupported environment or working directory")
            require(definition["StandardOutPath"] == str(self.hermes / "logs" / f"{kind}.log")
                    and definition["StandardErrorPath"] == str(self.hermes / "logs" / f"{kind}.error.log"),
                    "generated log paths are unsupported")
            self.expected[kind], self.raw[kind] = definition, data

    def jobs(self):
        require(launchctl("manageruid").strip() == str(self.uid)
                and launchctl("managername").strip() == "Aqua",
                "caller bootstrap is not the expected user's GUI domain")
        jobs = inventory(launchctl("list"))
        # User and GUI domains have separate jobs even though endpoints are shared.
        text = launchctl("print", f"user/{self.uid}")
        require(text.splitlines()[0] == f"user/{self.uid} = {{",
                "unsupported launchctl user-domain identity")
        blocks = re.findall(r"^\tservices = \{\n(.*?)^\t\}", text, re.M | re.S)
        require(len(blocks) == 1, "unsupported launchctl user-domain inventory")
        user_jobs = inventory(blocks[0], header=False)
        require(not any(label.startswith("ai.hermes.") for label in user_jobs),
                "user-domain Hermes jobs are unsupported; refusing continuation")
        require(not any(label.startswith("ai.hermes.") and label not in
                        {f"ai.hermes.{kind}" for kind in KINDS} for label in jobs),
                "named-profile or unknown Hermes launchd jobs are unsupported")
        return {kind: jobs.get(f"ai.hermes.{kind}") for kind in KINDS
                if f"ai.hermes.{kind}" in jobs}

    def live_definition(self, kind):
        path = self.home / "Library" / "LaunchAgents" / f"ai.hermes.{kind}.plist"
        directory(path.parent.parent, self.uid)
        directory(path.parent, self.uid)
        require(read_file(path, self.uid) == self.raw[kind],
                "live plist is not the current Nix definition; legacy job refused")

    def loaded_definition(self, kind, pid):
        self.live_definition(kind)
        text = launchctl("list", f"ai.hermes.{kind}").encode("utf-8")
        # Legacy list's property-list dump is not XML. plutil rejects unsupported objects.
        data = command("/usr/bin/plutil", "-convert", "xml1", "-o", "-", "-", data=text)
        loaded = plistlib.loads(data)
        allowed = {"Label", "LimitLoadToSessionType", "OnDemand", "LastExitStatus", "PID",
                   "TimeOut", "Program", "ProgramArguments", "StandardOutPath", "StandardErrorPath"}
        require(isinstance(loaded, dict) and set(loaded) <= allowed,
                "unsupported loaded launchd configuration")
        require(loaded.get("Label") == f"ai.hermes.{kind}"
                and loaded.get("LimitLoadToSessionType") == "Aqua"
                and loaded.get("OnDemand") in (True, "true", "1")
                and loaded.get("ProgramArguments") == self.expected[kind]["ProgramArguments"]
                and loaded.get("Program", self.expected[kind]["ProgramArguments"][0])
                == self.expected[kind]["ProgramArguments"][0],
                "loaded job is not a known on-demand Nix service")
        loaded_pid = loaded.get("PID")
        require((pid is None and loaded_pid in (None, 0, "0")) or
                (pid is not None and str(loaded_pid) == str(pid)),
                "loaded job PID changed during probe")
        for key in ("StandardOutPath", "StandardErrorPath"):
            require(loaded.get(key) == self.expected[kind][key], "loaded log path differs from definition")
        # Success confirms the label belongs to the explicitly addressed GUI domain.
        launchctl("print", f"{self.domain}/ai.hermes.{kind}")

    def state(self, processes):
        live = set()
        if not directory(self.hermes, self.uid, optional=True):
            return live
        homes = [self.hermes]
        profiles = self.hermes / "profiles"
        if directory(profiles, self.uid, optional=True):
            for path in sorted(profiles.iterdir()):
                require(re.fullmatch(r"[A-Za-z0-9_-]+", path.name), "unsupported profile path")
                directory(path, self.uid)
                homes.append(path)
        active = read_file(self.hermes / "active_profile", self.uid, optional=True)
        if active is not None:
            name = active.decode("utf-8").strip()
            require(name == "default" or (re.fullmatch(r"[A-Za-z0-9_-]+", name)
                    and profiles / name in homes), "invalid active profile state")
        for home in homes:
            for filename in ("gateway.pid", "gateway.lock", "gateway_state.json", "dashboard.pid", "serve.pid"):
                data = read_file(home / filename, self.uid, optional=True)
                if data is not None:
                    record = json_value(data)
                    if type(record) is int and filename.endswith((".pid", ".lock")):
                        record = {"pid": record}
                    identity = self.record(record, processes)
                    if identity is not None:
                        live.add(identity)
        ledger = read_file(self.hermes / "spawn-ledger.json", self.uid, optional=True)
        if ledger is not None:
            records = json_value(ledger)
            require(isinstance(records, list), "invalid spawn ledger")
            for record in records:
                require(isinstance(record, dict) and isinstance(record.get("purpose"), str)
                        and bool(record["purpose"]) and isinstance(record.get("install"), str)
                        and isinstance(record.get("argv"), str) and positive(record.get("registered_at"))
                        and "create_time" in record, "invalid spawn ledger entry")
                identity = self.record(record, processes, ledger=True)
                if identity is not None:
                    live.add(identity)
        return live

    def record(self, record, processes, ledger=False):
        require(isinstance(record, dict) and type(record.get("pid")) is int
                and record["pid"] > 1, "invalid runtime PID state")
        if not ledger:
            require("kind" not in record or record["kind"] in
                    ("hermes-gateway", "hermes-dashboard", "hermes-serve"), "invalid runtime kind")
            require("argv" not in record or (isinstance(record["argv"], list)
                    and all(isinstance(arg, str) for arg in record["argv"])), "invalid runtime argv state")
        require("hermes_home" not in record or (isinstance(record["hermes_home"], str)
                and ((ledger and record["hermes_home"] == "")
                     or Path(record["hermes_home"]).is_absolute())), "invalid runtime home state")
        created = record.get("create_time" if ledger else "start_time")
        require(created is None or positive(created), "invalid recorded process creation time")
        process = processes.get(record["pid"])
        if process is None:
            return
        # gateway.status uses centiseconds on macOS; spawn-ledger uses psutil epoch seconds.
        live_created = process.created if ledger else round(process.created * 100)
        if created is not None and abs(live_created - created) > 0.001:
            return
        require(self.uid in process.uids and (ledger or hermes_hint(process)),
                "runtime state refers to an unverified live process")
        # Legacy bare PIDs are discovery only; signalling authority comes from the live service tree.
        require(not ledger or created is not None, "live ledger entry has no creation time")
        return process.identity

    def check_plist_paths(self):
        library = self.home / "Library"
        agents = library / "LaunchAgents"
        if not directory(library, self.uid, optional=True) or not directory(agents, self.uid, optional=True):
            return
        for kind in KINDS:
            data = read_file(agents / f"ai.hermes.{kind}.plist", self.uid, optional=True)
            if data is not None:
                value = plistlib.loads(data)
                require(isinstance(value, dict) and value.get("Label") == f"ai.hermes.{kind}"
                        and isinstance(value.get("ProgramArguments"), list)
                        and bool(value["ProgramArguments"])
                        and all(isinstance(arg, str) for arg in value["ProgramArguments"]),
                        "invalid existing Hermes plist")

    def snapshot(self, retained=None):
        self.check_plist_paths()
        jobs = self.jobs()
        for kind, pid in jobs.items():
            self.loaded_definition(kind, pid)
        processes = census(self.uid)
        recorded = self.state(processes)
        require(self.jobs() == jobs, "launchd inventory changed during census")
        trees = {}
        for kind, pid in jobs.items():
            tree = set()
            if pid is not None:
                root = processes.get(pid)
                require(root is not None and root.uids == (self.uid,) * 3 and root.parent == 1,
                        "loaded service PID ownership or launchd ancestry is unverified")
                tree.add(pid)
                for _ in range(len(processes)):
                    children = {p.pid for p in processes.values() if p.parent in tree}
                    if children <= tree:
                        break
                    tree |= children
                require(all(processes[p].uids == (self.uid,) * 3 for p in tree),
                        "service descendant ownership is unverified")
                require(all(processes[p].created >= processes[processes[p].parent].created
                            for p in tree if p != pid), "service ancestry creation times disagree")
            # Captured descendants retain their ownership proof when a draining parent exits.
            for saved_pid, created in (retained or {}).get(kind, set()):
                saved = processes.get(saved_pid)
                if saved is not None:
                    require(saved.created == created, "captured PID was reused during drain")
                    tree.add(saved_pid)
            for _ in range(len(processes)):
                children = {p.pid for p in processes.values() if p.parent in tree}
                if children <= tree:
                    break
                tree |= children
            require(all(processes[p].uids == (self.uid,) * 3 for p in tree),
                    "captured descendant ownership changed")
            require(all(processes[p].created >= processes[processes[p].parent].created
                        for p in tree if processes[p].parent in tree),
                    "captured descendant ancestry changed")
            trees[kind] = tree
        runtimes = {kind: [] for kind in KINDS}
        for process in processes.values():
            if self.uid not in process.uids or (not hermes_hint(process) and process.identity not in recorded):
                continue
            owners = [kind for kind, tree in trees.items() if process.pid in tree]
            require(len(owners) == 1, "orphan, manual, or unowned Hermes runtime detected")
            kind = owners[0]
            identity = runtime(process)
            if identity is not None:
                require(identity == (kind, ["default"]),
                        "unrelated Hermes runtime or unsupported launch argv detected")
                require(process.argv[0].startswith("/nix/store/"), "runtime interpreter is not Nix-owned")
                runtimes[kind].append(process)
        require(all(len(items) <= 1 for items in runtimes.values()), "replacement or duplicate runtime detected")
        return jobs, processes, trees, runtimes

    def preflight(self):
        for _ in range(2):
            jobs, _, _, _ = self.snapshot()
            require(not jobs, "Hermes labels are still loaded; activation refused")
        print("Hermes preflight: unloaded; no current-user Hermes runtime found")

    def start(self, kind):
        jobs, _, _, _ = self.snapshot()
        require(kind not in jobs, "service is already loaded; use status or restart")
        self.live_definition(kind)
        directory(self.hermes, self.uid)
        logs = self.hermes / "logs"
        if not directory(logs, self.uid, optional=True):
            logs.mkdir(mode=0o700)
            directory(logs, self.uid)
        for key in ("StandardOutPath", "StandardErrorPath"):
            info = metadata(Path(self.expected[kind][key]))
            require(info is None or (stat.S_ISREG(info.st_mode) and info.st_uid == self.uid
                    and not info.st_mode & 0o022), "log destination has unsafe ownership or type")
        require(self.jobs() == jobs, "launchd inventory changed before start")
        launchctl("enable", f"{self.domain}/ai.hermes.{kind}")
        launchctl("bootstrap", self.domain,
                  str(self.home / "Library" / "LaunchAgents" / f"ai.hermes.{kind}.plist"))
        print(f"Hermes {kind}: bootstrapped (application readiness is not verified)")

    def stop(self, kind):
        jobs, processes, trees, runtimes = self.snapshot()
        target = f"{self.domain}/ai.hermes.{kind}"
        if kind not in jobs:
            launchctl("disable", target)
            print(f"Hermes {kind}: unloaded and disabled")
            return
        root_pid = jobs[kind]
        require(os.getpid() not in trees[kind], "cannot stop a service from inside its own process tree")
        tracked = {processes[pid].identity for pid in trees[kind]}
        original_runtimes = {p.identity for items in runtimes.values() for p in items}
        original_roots = {name: processes[pid].identity if pid is not None else None
                          for name, pid in jobs.items()}
        if root_pid is not None:
            require(len(runtimes[kind]) == 1, "loaded tree has no verified runtime; refusing bootout")
            expected = runtimes[kind][0]
            # Recheck the whole tree, loaded identity, uid and creation time immediately before SIGTERM.
            now_jobs, now_processes, now_trees, now_runtimes = self.snapshot()
            require(now_jobs == jobs and now_runtimes == runtimes
                    and all(now_processes.get(pid) == processes[pid] for pid in trees[kind])
                    and all(now_processes[pid].identity == original_roots[name]
                            for name, pid in now_jobs.items() if pid is not None)
                    and now_trees[kind] == trees[kind], "service tree changed before SIGTERM")
            fresh = inspect(expected.pid, self.uid)
            require(fresh == expected and runtime(fresh) == (kind, ["default"]),
                    "runtime identity changed before SIGTERM")
            process = psutil.Process(expected.pid)
            require(process.create_time() == expected.created, "runtime PID was reused")
            process.send_signal(signal.SIGTERM)
        deadline = time.monotonic() + TIMEOUT
        while True:
            current_jobs, current, current_trees, current_runtimes = self.snapshot({kind: tracked})
            require(set(current_jobs) == set(jobs), "service load/unload occurred during drain")
            for name, pid in current_jobs.items():
                identity = current[pid].identity if pid is not None else None
                require(identity == original_roots[name] or (name == kind and identity is None),
                        "service restarted during drain; refusing unload")
            require({p.identity for items in current_runtimes.values() for p in items}
                    <= original_runtimes, "replacement Hermes runtime appeared during drain")
            for pid, created in tracked:
                require(pid not in current or current[pid].created == created,
                        "tracked PID was reused during drain; refusing unload")
            tracked |= {current[pid].identity for pid in current_trees[kind]}
            if not any(pid in current for pid, _ in tracked) and current_jobs[kind] is None:
                break
            require(time.monotonic() < deadline, "drain timed out; no unload, restart or forced termination")
            time.sleep(0.5)
        self.loaded_definition(kind, None)
        require(self.jobs() == current_jobs, "launchd inventory changed before unload")
        launchctl("bootout", target)
        final_jobs, _, _, _ = self.snapshot()
        require(kind not in final_jobs, "service remains loaded after bootout; refusing continuation")
        launchctl("disable", target)
        print(f"Hermes {kind}: drained, unloaded and disabled")

    def status(self, kind):
        jobs, _, _, runtimes = self.snapshot()
        if kind not in jobs:
            print(f"Hermes {kind}: unloaded; no unowned Hermes runtime found")
        elif jobs[kind] is None:
            print(f"Hermes {kind}: loaded, idle; known Nix definition")
        else:
            print(f"Hermes {kind}: loaded PID {jobs[kind]}; verified runtimes: {len(runtimes[kind])}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preflight", "start", "stop", "restart", "status"))
    parser.add_argument("kind", choices=KINDS, nargs="?")
    args = parser.parse_args()
    if (args.action == "preflight") != (args.kind is None):
        parser.error("preflight takes no service; other actions require gateway or dashboard")
    try:
        controller = Controller()
        if args.action == "preflight":
            controller.preflight()
        elif args.action == "restart":
            controller.stop(args.kind)
            controller.start(args.kind)
        else:
            getattr(controller, args.action)(args.kind)
    except Refused as error:
        print(f"hermes-service: refused: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError, SyntaxError, KeyError, TypeError, IndexError,
            psutil.Error, subprocess.SubprocessError, plistlib.InvalidFileException):
        # Exception details can contain argv or private runtime data.
        print("hermes-service: probe or operation failed; state is unknown; no fallback", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
