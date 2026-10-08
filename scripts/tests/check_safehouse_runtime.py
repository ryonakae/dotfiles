"""Run outside Safehouse; all file operations use a disposable HOME."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / 'config/.config/agent-safehouse'


def main():
  if os.environ.get('APP_SANDBOX_CONTAINER_ID') == 'agent-safehouse':
    raise SystemExit('Run this check outside Safehouse; nested policies cannot validate new grants.')
  with tempfile.TemporaryDirectory(prefix='dotfiles-policy-') as temporary:
    home = Path(temporary).resolve()
    trash_roots = ['.local/share/Trash', 'custom data/Trash',
                   'volume/.Trash-' + str(os.getuid()), 'volume/.Trash/' + str(os.getuid())]
    ordinary = ['Downloads/normal.txt', '.env', '.aws/credentials', '.gnupg/private.txt',
                '.ssh/id_ed25519', '.ssh/config', '.ssh/known_hosts',
                'Library/Messages/chat.db', 'Library/Application Support/Google/Chrome/Cookies',
                'project/.secrets/token.txt', '.android/release.keystore',
                'vendor/fixture/.env', '.hermes/.env', '.config/fish/config.fish']
    payloads = [root + '/files/private.txt' for root in trash_roots] + ['.Trash/private.txt']
    metadata = [root + '/info/item.trashinfo' for root in trash_roots]
    for relative in ordinary + payloads + metadata + ['.hermes/Trash/files/exception.txt']:
      target = home / relative
      target.parent.mkdir(parents=True, exist_ok=True)
      target.write_text('dummy data')
    env = dict(os.environ, HOME=str(home), UNLISTED_RUNTIME_VALUE='inherited value with spaces')
    args = ['safehouse', '--workdir=' + str(home), '--add-dirs=' + str(home), '--env',
            '--allow-profile-writes', '--enable=wide-read,ssh,process-control',
            '--append-profile=' + str(RUNTIME / 'compatibility.sb'),
            '--append-profile=' + str(RUNTIME / 'local-overrides.sb'), '--', sys.executable, '-c']

    def check(label, code):
      result = subprocess.run(args + [code], env=env, capture_output=True, text=True, timeout=20)
      assert result.returncode == 0, f'{label}: exit={result.returncode}\n{result.stderr}'
      print('PASS', label, flush=True)

    check('environment and child process', '''
import os, socket, subprocess
assert os.environ['UNLISTED_RUNTIME_VALUE'] == 'inherited value with spaces'
a, b = socket.socketpair()
a.send(b'ok')
assert b.recv(2) == b'ok'
subprocess.run(['/usr/bin/true'], check=True)
''')
    for relative in ordinary + metadata + ['.hermes/Trash/files/exception.txt']:
      check('allow read/write ' + relative,
            f'from pathlib import Path; p=Path({str(home / relative)!r}); '
            'assert p.read_text() == "dummy data"; p.write_text("changed"); '
            'assert p.read_text() == "changed"')
    for relative in payloads:
      for operation in ['read_text()', 'write_text("changed")', 'unlink()']:
        check('deny payload ' + operation + ' ' + relative, f'''
from pathlib import Path
p = Path({str(home / relative)!r})
assert p.stat().st_size > 0
try:
  p.{operation}
except PermissionError:
  pass
else:
  raise AssertionError('payload operation was allowed')
''')
    for index, root in enumerate(trash_roots):
      source = home / f'Downloads/put-{index}'
      source.write_text('dummy Put data')
      destination = home / root / 'files/new.txt'
      check('allow Put ' + root, f'import os; os.rename({str(source)!r}, {str(destination)!r})')
      assert destination.read_text() == 'dummy Put data'
    target = home / 'Downloads/rm-target'
    target.write_text('keep')
    check('deny /bin/rm execution', f'''
import subprocess
try:
  subprocess.run(['/bin/rm', '-f', {str(target)!r}], check=True)
except PermissionError:
  pass
else:
  raise AssertionError('/bin/rm executed')
''')
    assert target.read_text() == 'keep'
    print('SAFEHOUSE_RUNTIME_PASS', flush=True)


if __name__ == '__main__':
  main()
