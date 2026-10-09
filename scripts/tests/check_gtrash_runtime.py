"""Run outside Safehouse; real gtrash only touches a disposable HOME and trash."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / 'config/.config/agent-safehouse'


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--gtrash', default='/opt/homebrew/bin/gtrash')
  options = parser.parse_args()
  if os.environ.get('APP_SANDBOX_CONTAINER_ID') == 'agent-safehouse':
    raise SystemExit('Run outside Safehouse; nested policies cannot validate new grants.')
  gtrash = Path(options.gtrash).resolve(strict=True)
  with tempfile.TemporaryDirectory(prefix='dotfiles-gtrash-') as temporary:
    home = Path(temporary).resolve()
    work = home / 'work'
    work.mkdir()
    trash = home / '.local/share/Trash'
    trash.mkdir(parents=True)
    tmp = home / 'tmp'
    tmp.mkdir()
    bin_dir = home / '.local/bin'
    bin_dir.mkdir()
    wrapper = bin_dir / 'rm'
    wrapper.write_text((ROOT / 'config/.local/bin/rm').read_text().replace(
      '/opt/homebrew/bin/gtrash', str(gtrash)))
    wrapper.chmod(0o755)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('GTRASH_', 'TRASH_', 'XDG_'))}
    env.update(HOME=str(home), TMPDIR=str(tmp), XDG_DATA_HOME=str(home / '.local/share'),
               XDG_CONFIG_HOME=str(home / '.config'), GTRASH_HOME_TRASH_DIR=str(trash),
               GTRASH_ONLY_HOME_TRASH='false', GTRASH_HOME_TRASH_FALLBACK_COPY='false',
               PATH=str(bin_dir) + ':' + os.environ['PATH'])

    def run(command, *, sandbox=True, environment=None, profile=None):
      if sandbox:
        # Direct sandbox-exec reuses the policy without Safehouse's env setup.
        environment = dict(environment or env, APP_SANDBOX_CONTAINER_ID='agent-safehouse')
        command = ['/usr/bin/sandbox-exec', '-f', str(profile or policy), *command]
      return subprocess.run([str(x) for x in command], env=environment or env, cwd=work,
                            input='', capture_output=True, text=True, timeout=30)

    args = ['safehouse', '--workdir=' + str(work), '--add-dirs=' + str(home), '--env',
            '--allow-profile-writes', '--enable=wide-read,ssh,process-control',
            '--append-profile=' + str(RUNTIME / 'compatibility.sb'),
            '--append-profile=' + str(RUNTIME / 'local-overrides.sb')]
    generated = run([*args, '--stdout', '--', '/bin/sh'], sandbox=False)
    assert generated.returncode == 0, generated.stderr
    policy = home / 'policy.sb'
    policy.write_text(generated.stdout)
    version = run([gtrash, '--version'], sandbox=False)
    assert version.returncode == 0, version.stderr
    print(version.stdout.strip(), flush=True)

    def put(path):
      result = run([wrapper, '-rf', '--', path])
      assert result.returncode == 0, result.stderr
      assert not os.path.lexists(path), path
      return result

    def entries():
      result = {}
      for info in (trash / 'info').glob('*.trashinfo'):
        line = next(line[5:] for line in info.read_text().splitlines() if line.startswith('Path='))
        original = unquote(line)
        result[original] = trash / 'files' / info.name[:-10]
      return result

    def restore(paths):
      # Human-side restoration must not enumerate the host's other volume trash.
      result = run([gtrash, 'restore', '--force', *paths], sandbox=False,
                   environment=dict(env, GTRASH_ONLY_HOME_TRASH='true'))
      assert result.returncode == 0, result.stderr

    outside = work / 'outside-rm.txt'
    outside.write_text('disposable test data')
    result = run([wrapper, '--', outside], sandbox=False)
    assert result.returncode == 0 and not outside.exists(), result.stderr
    assert not entries(), 'outside rm must not use the trash'
    print('PASS outside Safehouse uses system rm', flush=True)

    for kind in ['file', 'directory', 'broken-link']:
      path = work / kind
      if kind == 'file':
        path.write_text('original')
      elif kind == 'directory':
        path.mkdir()
        (path / 'child').write_text('original')
      else:
        path.symlink_to('missing-target')
      put(path)
      stored = entries()[str(path)]
      assert os.path.lexists(stored)
      restore([path])
      if kind == 'broken-link':
        assert path.is_symlink() and os.readlink(path) == 'missing-target'
      else:
        assert (path / 'child' if kind == 'directory' else path).read_text() == 'original'
      print('PASS protected Put + human restore', kind, flush=True)

    paths = []
    for index in range(16):
      parent = work / str(index)
      parent.mkdir()
      path = parent / 'same-name'
      if index < 12:
        path.write_text(str(index))
      else:
        path.mkdir()
        (path / 'child').write_text(str(index))
      paths.append(path)
    with ThreadPoolExecutor(max_workers=16) as pool:
      list(pool.map(put, paths))
    saved = entries()
    assert len({saved[str(path)] for path in paths}) == 16
    restore(paths)
    for index, path in enumerate(paths):
      assert (path if index < 12 else path / 'child').read_text() == str(index)
    print('PASS 16-process same-name Put + human restore', flush=True)
    result = run([wrapper, '-rf', '--', *paths[:3]])
    assert result.returncode == 0, result.stderr
    restore(paths[:3])
    assert [path.read_text() for path in paths[:3]] == ['0', '1', '2']
    print('PASS single-command same-name Put', flush=True)

    protected = work / 'protected'
    protected.write_text('keep')
    put(protected)
    payload = entries()[str(protected)]
    for operation in ['read_text()', 'write_text("changed")', 'unlink()']:
      code = f'''from pathlib import Path
p = Path({str(payload)!r})
try:
  p.{operation}
except PermissionError:
  pass
else:
  raise AssertionError('payload operation was allowed')
'''
      result = run([sys.executable, '-c', code])
      assert result.returncode == 0, result.stderr
    assert payload.read_text() == 'keep'
    print('PASS sandbox cannot read/write/unlink payload', flush=True)

    denied = work / 'move-denied'
    denied.write_text('keep')
    failure_policy = home / 'failure.sb'
    failure_policy.write_text(policy.read_text() + '\n(deny file-write-unlink (literal '
                              + json.dumps(str(denied)) + '))\n')
    result = run([wrapper, '-f', denied], profile=failure_policy)
    assert result.returncode != 0 and denied.read_text() == 'keep', result.stderr
    print('PASS failed Put preserves source and returns failure', flush=True)
    result = run(['/bin/rm', '-f', denied])
    assert result.returncode != 0 and denied.read_text() == 'keep'
    print('PASS /bin/rm execution denied', flush=True)

    result = run([*args, '--', '/bin/sh', '-c',
                  'set -e; t=$(mktemp); printf temporary > "$t"; trap \'rm -f -- "$t"\' EXIT'],
                 sandbox=False)
    assert result.returncode == 0, result.stderr
    assert any(path.is_file() and not path.is_symlink() and path.read_text() == 'temporary'
               for path in entries().values())
    print('PASS Safehouse and EXIT trap cleanup through managed rm', flush=True)
    print('GTRASH_RUNTIME_PASS', flush=True)


if __name__ == '__main__':
  main()
