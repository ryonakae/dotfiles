"""Run explicitly outside Safehouse; gomi operations target disposable data only."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / 'config/.config/agent-safehouse'


def main():
  if os.environ.get('APP_SANDBOX_CONTAINER_ID') == 'agent-safehouse':
    raise SystemExit('Run outside Safehouse; this check needs a fresh policy.')
  with tempfile.TemporaryDirectory(prefix='dotfiles-gomi-') as temporary:
    base = Path(temporary)
    home = base / 'home'
    config = home / '.config/gomi/config.yaml'
    config.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / 'config/.config/gomi/config.yaml', config)
    env = {'HOME': str(home), 'PATH': os.environ['PATH'],
           'XDG_DATA_HOME': str(home / '.local/share'), 'TMPDIR': str(base)}
    work = home / 'work'
    work.mkdir()
    source = work / 'dummy file'
    source.write_text('dummy data')
    sandbox = ['safehouse', '--workdir=' + str(work), '--add-dirs=' + str(home), '--env',
               '--enable=wide-read,process-control',
               '--append-profile=' + str(RUNTIME / 'compatibility.sb'),
               '--append-profile=' + str(RUNTIME / 'local-overrides.sb'), '--']
    moved = subprocess.run(sandbox + ['gomi', '--config', str(config), '--', str(source)],
                           env=env, capture_output=True, text=True, timeout=30)
    assert moved.returncode == 0, moved.stderr
    assert not source.exists(), 'source not moved'
    assert (home / '.local/share/Trash/files' / source.name).read_text() == 'dummy data'
    print('PASS real gomi Put under production policy', flush=True)
    print('GOMI_RUNTIME_PASS', flush=True)


if __name__ == '__main__':
  main()
