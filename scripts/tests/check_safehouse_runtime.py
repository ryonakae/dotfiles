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
      'project/.secrets/.gitkeep', 'project/.secrets/token.txt', 'project/.secrets/.env',
      '.android/release.keystore', 'project/custom.keystore',
      '.config/agent-safehouse/run-with-agent-env.sh',
      'dotfiles/config/.config/fish/config.fish',
      'dotfiles/config/.local/bin/rm',
    ]
    for relative in files:
      target = home / relative
      target.parent.mkdir(parents=True, exist_ok=True)
      target.write_text('dummy data')
    (home / 'secret-alias').symlink_to(home / '.env')
    alias_directory = home / 'alias-project/.secrets'
    alias_directory.mkdir(parents=True)
    (alias_directory / '.gitkeep').symlink_to(home / '.env')
    project = home / 'project'
    (project / '.gitignore').write_text('.secrets/*\n!.secrets/.gitkeep\n')
    checkout = home / 'checkout'
    checkout.mkdir()
    env = dict(os.environ, HOME=str(home), UNLISTED_RUNTIME_VALUE='inherited value with spaces')
    args = ['safehouse', '--workdir=' + str(home), '--add-dirs=' + str(home), '--env',
            '--allow-profile-writes', '--enable=wide-read,ssh,process-control,launch-services',
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
    debug_key = home / '.android/debug.keystore'
    check('create/read/write Android debug keystore',
          f'from pathlib import Path; p=Path({str(debug_key)!r}); '
          'p.write_text("dummy debug key"); assert p.read_text() == "dummy debug key"')
    for relative in ['.android/release.keystore', 'project/custom.keystore']:
      check('deny keystore read ' + relative, f'from pathlib import Path; Path({str(home / relative)!r}).read_text()', 1)
      check('deny keystore write ' + relative, f'from pathlib import Path; Path({str(home / relative)!r}).write_text("changed")', 1)
    debug_key.unlink()
    debug_key.symlink_to(home / '.env')
    check('deny debug keystore alias read', f'from pathlib import Path; Path({str(debug_key)!r}).read_text()', 1)
    check('deny debug keystore alias write', f'from pathlib import Path; Path({str(debug_key)!r}).write_text("changed")', 1)
    check('Git placeholder metadata and directory listing',
          f'from pathlib import Path; p=Path({str(project / ".secrets")!r}); '
          'assert p.stat(); assert sorted(x.name for x in p.iterdir()) == [".env", ".gitkeep", "token.txt"]; '
          'assert (p / "token.txt").stat().st_size > 0; assert (p / ".gitkeep").read_text() == "dummy data"')
    check('Git status/add/diff and checkout with .secrets placeholder', f'''
import subprocess
from pathlib import Path
p = Path({str(project)!r})
for arguments in [
  ['init', '--quiet', '--initial-branch=main'],
  ['status', '--porcelain'],
  ['add', '--', '.gitignore', '.secrets/.gitkeep'],
  ['diff', '--cached', '--stat'],
  ['checkout-index', '--all', '--prefix={str(checkout)}/'],
]:
  result = subprocess.run(['git', '-C', str(p), *arguments], capture_output=True, text=True)
  assert result.returncode == 0, result.stderr
  assert not result.stderr, result.stderr
assert Path({str(checkout / '.secrets/.gitkeep')!r}).read_text() == 'dummy data'
placeholder = p / '.secrets/.gitkeep'
placeholder.write_text('updated placeholder')
placeholder.unlink()
''')
    for relative in ['project/.secrets/token.txt', 'project/.secrets/.env', 'alias-project/.secrets/.gitkeep']:
      check('deny secret content ' + relative, f'from pathlib import Path; Path({str(home / relative)!r}).read_text()', 1)
      check('deny secret mutation ' + relative, f'from pathlib import Path; Path({str(home / relative)!r}).write_text("changed")', 1)
    check('deny secret deletion', f'from pathlib import Path; Path({str(project / ".secrets/token.txt")!r}).unlink()', 1)
    for relative in ['.env', '.aws/credentials', '.gnupg/private.txt', '.ssh/id_ed25519',
                     '.config/fish/config.fish', 'Library/Messages/chat.db',
                     'Library/Application Support/Google/Chrome/Cookies', 'secret-alias',
                     'dotfiles/config/.config/fish/config.fish',
                     *[root + '/files/private.txt' for root in trash_roots]]:
      check('deny read ' + relative, f'from pathlib import Path; Path({str(home / relative)!r}).read_text()', 1)
    for relative in ['.env', '.aws/credentials', '.gnupg/private.txt', '.ssh/id_ed25519',
                     '.config/fish/config.fish',
                     *[root + '/files/private.txt' for root in trash_roots]]:
      check('deny write ' + relative, f'from pathlib import Path; Path({str(home / relative)!r}).write_text("changed")', 1)
    for relative in ['Downloads/normal.txt', '.ssh/config', '.ssh/known_hosts',
                     '.ssh/agent/socket-fixture', '.config/agent-browser/profile/normal.txt',
                     '.hermes/.env', 'vendor/fixture/.env',
                     *[root + '/info/item.trashinfo' for root in trash_roots]]:
      check('allow read ' + relative, f'from pathlib import Path; assert Path({str(home / relative)!r}).read_text() == "dummy data"')
    for relative in ['Downloads/normal.txt', '.ssh/known_hosts', '.hermes/.env', 'vendor/fixture/.env',
                     '.config/agent-safehouse/run-with-agent-env.sh', 'dotfiles/config/.local/bin/rm']:
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
