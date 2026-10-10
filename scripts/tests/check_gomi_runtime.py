"""Run explicitly outside Safehouse; gomi operations target disposable data only."""
import configparser
import fcntl
import os
from pathlib import Path
import pty
import re
import select
import shutil
import signal
import struct
import subprocess
import tempfile
import termios
import time
from urllib.parse import unquote
import uuid


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / 'config/.config/agent-safehouse'


def restore_in_tty(env, config, source):
  # 外部volumeの既存trashを復元一覧へ取り込まない。
  isolation = r'(version 1)(allow default)(deny file-read* file-write* (regex #".*/\.Trash(-[0-9]+)?(/.*)?$"))'
  pid, master = pty.fork()
  if pid == 0:
    os.execvpe('/usr/bin/sandbox-exec', ['sandbox-exec', '-p', isolation,
              'gomi', '--config', str(config), '--restore'], env)
  fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', 40, 140, 0, 0))
  deadline = time.monotonic() + 20
  output = ''
  requested = False
  confirmed = False
  reaped = False
  try:
    while time.monotonic() < deadline:
      if select.select([master], [], [], 0.1)[0]:
        try:
          data = os.read(master, 65536)
        except OSError:
          break
        if not data:
          break
        output += data.decode(errors='replace')
        plain = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', output)
        if not requested and source.name in plain:
          os.write(master, b'\r')
          output = ''
          requested = True
        elif requested and not confirmed and ('ok to restore?' in plain.lower()):
          os.write(master, b'y\r')
          confirmed = True
      if source.exists():
        os.write(master, b'q')
        _, status = os.waitpid(pid, 0)
        reaped = True
        assert os.waitstatus_to_exitcode(status) == 0, 'restore TUI failed'
        return
    raise AssertionError('restore TUI did not restore dummy target: ' + repr(output[-2500:]))
  finally:
    if not reaped:
      try:
        os.kill(pid, signal.SIGTERM)
      except ProcessLookupError:
        pass
      os.waitpid(pid, 0)
    os.close(master)


def main():
  if os.environ.get('APP_SANDBOX_CONTAINER_ID') == 'agent-safehouse':
    raise SystemExit('Run outside Safehouse; this check needs a fresh policy and restore TTY.')
  with tempfile.TemporaryDirectory(prefix='dotfiles-gomi-') as temporary:
    base = Path(temporary)
    home = base / 'home'
    config = home / '.config/gomi/config.yaml'
    config.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / 'config/.config/gomi/config.yaml', config)
    env = {'HOME': str(home), 'PATH': os.environ['PATH'],
           'XDG_DATA_HOME': str(home / '.local/share'), 'TMPDIR': str(base),
           'TERM': 'xterm-256color'}
    work = home / 'work'
    work.mkdir()
    source = work / ('restore-' + uuid.uuid4().hex[:12])
    source.mkdir()
    (source / 'space name').write_text('dummy space data')
    (source / '--prune=1d').write_text('dummy option data')
    target = work / 'target'
    target.write_text('symlink target remains')
    (source / 'link').symlink_to(target)
    sandbox = ['safehouse', '--workdir=' + str(work), '--add-dirs=' + str(home), '--env',
               '--enable=wide-read,process-control',
               '--append-profile=' + str(RUNTIME / 'compatibility.sb'),
               '--append-profile=' + str(RUNTIME / 'local-overrides.sb'), '--']
    moved = subprocess.run(sandbox + ['gomi', '--config', str(config), '--', str(source)], env=env,
                           capture_output=True, text=True, timeout=30)
    assert moved.returncode == 0, moved.stderr
    assert not source.exists(), 'source not moved'
    trash = home / '.local/share/Trash'
    info = configparser.ConfigParser(interpolation=None)
    info.read(trash / 'info' / (source.name + '.trashinfo'))
    assert unquote(info['Trash Info']['Path']) == str(source), 'metadata changed the absolute input path'
    assert (trash / 'files' / source.name / 'space name').read_text() == 'dummy space data'
    print('PASS real gomi Put under production policy + XDG metadata', flush=True)
    restore_in_tty(env, config, source)
    assert (source / 'space name').read_text() == 'dummy space data'
    assert (source / '--prune=1d').read_text() == 'dummy option data'
    assert (source / 'link').is_symlink() and (source / 'link').readlink() == target
    assert target.read_text() == 'symlink target remains'
    assert not (trash / 'info' / (source.name + '.trashinfo')).exists()
    print('PASS real restore TUI + original paths/content/symlink', flush=True)
    processes = []
    for i in range(4):
      folder = work / str(i)
      folder.mkdir()
      (folder / 'same').write_text('dummy ' + str(i))
      processes.append(subprocess.Popen(sandbox + ['gomi', '--config', str(config), '--', str(folder / 'same')],
                       env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
    for process in processes:
      _, stderr = process.communicate(timeout=30)
      assert process.returncode == 0, stderr
    saved = [path for path in (trash / 'files').iterdir() if path.name.startswith('same')]
    assert len(saved) == 4 and {p.read_text() for p in saved} == {'dummy ' + str(i) for i in range(4)}
    assert len(list((trash / 'info').glob('same*.trashinfo'))) == 4
    print('PASS concurrent real gomi calls preserve all data/metadata', flush=True)
    print('GOMI_RUNTIME_PASS', flush=True)


if __name__ == '__main__':
  main()
