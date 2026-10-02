"""Run explicitly outside Safehouse; all file operations use a disposable HOME."""
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
    home = Path(temporary)
    trash_roots = ['.local/share/Trash', 'custom data/Trash',
                   'volume/.Trash-' + str(os.getuid()), 'volume/.Trash/' + str(os.getuid())]
    files = [*[(root + '/files/private.txt') for root in trash_roots],
             *[(root + '/info/item.trashinfo') for root in trash_roots],
      'Downloads/normal.txt', '.env', '.aws/credentials', '.gnupg/private.txt',
      '.ssh/id_ed25519', '.ssh/config', '.ssh/known_hosts', '.ssh/agent/socket-fixture',
      '.config/fish/config.fish', 'Library/Messages/chat.db',
      'Library/Application Support/Google/Chrome/Cookies',
      '.config/agent-browser/profile/normal.txt', '.hermes/.env',
      'vendor/fixture/.env',
      '.config/agent-safehouse/run-with-agent-env.sh',
      'dotfiles/config/.config/fish/config.fish',
      'dotfiles/config/.local/bin/rm',
    ]
    for relative in files:
      target = home / relative
      target.parent.mkdir(parents=True, exist_ok=True)
      target.write_text('dummy data')
    (home / 'secret-alias').symlink_to(home / '.env')
    env = dict(os.environ, HOME=str(home), UNLISTED_RUNTIME_VALUE='inherited value with spaces')
    args = ['safehouse', '--workdir=' + str(home), '--add-dirs=' + str(home), '--env',
            '--enable=wide-read,ssh,process-control,launch-services',
            '--append-profile=' + str(RUNTIME / 'compatibility.sb'),
            '--append-profile=' + str(RUNTIME / 'local-overrides.sb'), '--', sys.executable, '-c']

    def check(label, code, expected=0):
      result = subprocess.run(args + [code], env=env, capture_output=True, text=True, timeout=20)
      if (result.returncode == 0) != (expected == 0):
        print('FAIL', label, 'exit=' + str(result.returncode), flush=True)
        print(result.stderr, flush=True)
        raise AssertionError(label)
      print('PASS', label, flush=True)

    check('compile + environment', 'import os; assert os.environ["UNLISTED_RUNTIME_VALUE"] == "inherited value with spaces"')
    for relative in ['.env', '.aws/credentials', '.gnupg/private.txt', '.ssh/id_ed25519',
                     '.config/fish/config.fish', 'Library/Messages/chat.db',
                     'Library/Application Support/Google/Chrome/Cookies', 'secret-alias',
                     'dotfiles/config/.config/fish/config.fish',
                     *[root + '/files/private.txt' for root in trash_roots]]:
      check('deny read ' + relative, f'from pathlib import Path; Path({str(home / relative)!r}).read_text()', 1)
    for relative in ['.env', '.aws/credentials', '.gnupg/private.txt', '.ssh/id_ed25519',
                     '.config/fish/config.fish', '.config/agent-safehouse/run-with-agent-env.sh',
                     'dotfiles/config/.local/bin/rm',
                     *[root + '/files/private.txt' for root in trash_roots]]:
      check('deny write ' + relative, f'from pathlib import Path; Path({str(home / relative)!r}).write_text("changed")', 1)
    for relative in ['.config', '.aws', 'Library', 'Library/Application Support/Google',
                     'dotfiles', 'dotfiles/config/.config/fish',
                     '.local/share', *trash_roots,
                     'volume/.Trash']:
      check('deny rename ' + relative, f'import os; os.rename({str(home / relative)!r}, {str(home / (relative + "-moved"))!r})', 1)
    for relative in ['Downloads/normal.txt', '.ssh/config', '.ssh/known_hosts',
                     '.ssh/agent/socket-fixture', '.config/agent-browser/profile/normal.txt',
                     '.hermes/.env', 'vendor/fixture/.env',
                     *[root + '/info/item.trashinfo' for root in trash_roots]]:
      check('allow read ' + relative, f'from pathlib import Path; assert Path({str(home / relative)!r}).read_text() == "dummy data"')
    for relative in ['Downloads/normal.txt', '.ssh/known_hosts', '.hermes/.env', 'vendor/fixture/.env']:
      check('allow write ' + relative, f'from pathlib import Path; Path({str(home / relative)!r}).write_text("changed")')
    for root in trash_roots:
      put_source = home / 'Downloads/put-source'
      put_source.write_text('dummy Put data')
      check('trash Put without reading payload ' + root,
            f'import os; os.rename({str(put_source)!r}, {str(home / root / "files/new.txt")!r})')
    check('IPC + child process', 'import socket, subprocess; a,b=socket.socketpair(); a.send(b"ok"); assert b.recv(2)==b"ok"; subprocess.run(["/usr/bin/true"],check=True)')
    print('SAFEHOUSE_RUNTIME_PASS', flush=True)


if __name__ == '__main__':
  main()
