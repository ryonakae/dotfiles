import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
NIX = shutil.which('nix') or '/nix/var/nix/profiles/default/bin/nix'


@unittest.skipUnless(Path(NIX).is_file(), 'Nix is required for CLI integration tests')
class DotfilesCliTests(unittest.TestCase):
  def setUp(self):
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.root = Path(self.directory.name) / 'repo'
    self.root.mkdir()
    (self.root / 'scripts').mkdir()
    for name in ('dotfiles.sh', 'dotfiles.py'):
      source = ROOT / 'scripts' / name
      if source.exists():
        shutil.copy(source, self.root / 'scripts' / name)
    for name in ('host', 'public', 'replacement'):
      (self.root / name).mkdir()
      (self.root / name / 'value').write_text(name)
    (self.root / 'host' / 'host.json').write_text(json.dumps({
      'username': 'example', 'homeDirectory': '/Users/example',
    }))
    (self.root / 'flake.nix').write_text('''{
  inputs.host = { url = "path:./host"; flake = false; };
  inputs.public = { url = "path:./public"; flake = false; };
  outputs = { self, host, public }: {
    darwinConfigurations.mac.system = builtins.derivation {
      name = "dotfiles-cli-test";
      system = "aarch64-darwin";
      builder = "/bin/sh";
      args = [ "-c" ''
        /bin/mkdir -p "$out"
        printf '%s' '${(builtins.fromJSON (builtins.readFile "${host}/host.json")).username}' > "$out/username"
        printf '%s' '${self}' > "$out/source"
        printf '%s' '${host}' > "$out/host"
      '' ];
    };
  };
}
''')
    self.host = Path(self.directory.name) / 'local-host'
    self.host.mkdir()
    (self.host / 'host.json').write_text(json.dumps({
      'username': 'fixture-user', 'homeDirectory': '/Users/fixture-user',
    }))
    self.env = dict(os.environ, PATH=str(Path(NIX).parent) + ':' + os.environ['PATH'])
    self.command('git', 'init', '--quiet')
    self.command('git', 'add', '.')
    self.command(NIX, '--extra-experimental-features', 'nix-command flakes',
                 'flake', 'lock', str(self.root))
    self.command('git', 'add', 'flake.lock')

  def command(self, *args):
    return subprocess.run(args, cwd=self.root, env=self.env,
                          capture_output=True, text=True, check=True)

  def cli(self, *args):
    return subprocess.run(['/bin/bash', str(self.root / 'scripts/dotfiles.sh'),
                           *args], cwd=self.root, env=self.env,
                          capture_output=True, text=True)

  def test_build_uses_local_host_without_changing_lock_or_importing_untracked_files(self):
    lock = (self.root / 'flake.lock').read_bytes()
    (self.root / 'untracked-secret.txt').write_text('DUMMY_SECRET=not-a-real-secret\n')
    (self.host / 'untracked-secret.txt').write_text('DUMMY_SECRET=not-a-real-secret\n')
    result = self.cli('build', '--host', str(self.host))
    self.assertEqual(result.returncode, 0, result.stderr)
    output = Path(result.stdout.strip())
    self.assertEqual((output / 'username').read_text(), 'fixture-user')
    self.assertEqual((self.root / 'flake.lock').read_bytes(), lock)
    self.assertFalse((Path((output / 'source').read_text()) / 'untracked-secret.txt').exists())
    self.assertFalse((Path((output / 'host').read_text()) / 'untracked-secret.txt').exists())

  def test_changed_public_url_requires_explicit_update(self):
    lock = (self.root / 'flake.lock').read_bytes()
    flake = self.root / 'flake.nix'
    flake.write_text(flake.read_text().replace('path:./public', 'path:./replacement'))
    result = self.cli('build', '--host', str(self.host))
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('lock', result.stderr.lower())
    self.assertEqual((self.root / 'flake.lock').read_bytes(), lock)

  def test_missing_public_lock_entry_requires_explicit_update(self):
    lockfile = self.root / 'flake.lock'
    lock = json.loads(lockfile.read_text())
    del lock['nodes']['public']
    del lock['nodes']['root']['inputs']['public']
    lockfile.write_text(json.dumps(lock))
    before = lockfile.read_bytes()
    result = self.cli('build', '--host', str(self.host))
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('lock', result.stderr.lower())
    self.assertEqual(lockfile.read_bytes(), before)

  def test_explicit_update_repairs_changed_public_input_without_building(self):
    flake = self.root / 'flake.nix'
    flake.write_text(flake.read_text().replace('path:./public', 'path:./replacement'))
    result = self.cli('update', 'public')
    self.assertEqual(result.returncode, 0, result.stderr)
    lock = json.loads((self.root / 'flake.lock').read_text())
    self.assertEqual(lock['nodes']['public']['original']['path'], './replacement')
    self.assertNotIn('/nix/store/', result.stdout)


if __name__ == '__main__':
  unittest.main()
