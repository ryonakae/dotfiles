import io
import os
import tarfile
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / 'scripts/bootstrap-nix.sh'


class BootstrapNixTests(unittest.TestCase):
  def setUp(self):
    self.directory = tempfile.TemporaryDirectory()
    self.addCleanup(self.directory.cleanup)
    self.home = Path(self.directory.name)
    self.bin = self.home / 'bin'
    self.bin.mkdir()
    self.marker = self.home / 'installer-arguments'
    self.archive = self.home / 'fixture.tar.xz'
    payload = b'#!/bin/sh\nprintf "%s\\n" "$@" > "$INSTALL_MARKER"\n'
    with tarfile.open(self.archive, 'w:xz') as archive:
      info = tarfile.TarInfo('fixture/install')
      info.size = len(payload)
      info.mode = 0o755
      archive.addfile(info, io.BytesIO(payload))
    self.env = dict(os.environ, HOME=str(self.home), APP_SANDBOX_CONTAINER_ID='',
                    PATH=str(self.bin) + ':/usr/bin:/bin',
                    INSTALL_MARKER=str(self.marker), ARCHIVE_FIXTURE=str(self.archive))
    self.program('uname', 'case "$1" in -s) echo Darwin;; -m) echo arm64;; esac\n')
    self.program('stat', 'exit 1\n')
    self.program('curl', 'while [ "$#" -gt 0 ]; do\n'
                 'if [ "$1" = --output ]; then cp "$ARCHIVE_FIXTURE" "$2"; exit; fi\n'
                 'shift\ndone\nexit 1\n')
    self.program('shasum', 'cat >/dev/null\nexit 0\n')

  def program(self, name, body):
    path = self.bin / name
    path.write_text('#!/bin/sh\n' + body)
    path.chmod(0o755)

  def run_bootstrap(self):
    return subprocess.run(['/bin/bash', str(BOOTSTRAP), '--install'], env=self.env,
                          capture_output=True, text=True)

  def test_runs_verified_installer_in_daemon_mode(self):
    result = self.run_bootstrap()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertTrue(self.marker.exists(), 'the installer was not started')
    self.assertEqual(self.marker.read_text(), '--daemon\n--no-channel-add\n')

  def test_rejects_non_apple_silicon_macos(self):
    for system, machine in [('Linux', 'aarch64'), ('Darwin', 'x86_64')]:
      with self.subTest(system=system, machine=machine):
        self.program('uname', f'case "$1" in -s) echo {system};; -m) echo {machine};; esac\n')
        result = self.run_bootstrap()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.marker.exists())

  def test_existing_nix_is_not_reinstalled(self):
    self.program('nix', 'exit 0\n')
    result = self.run_bootstrap()
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn('already', result.stdout)
    self.assertFalse(self.marker.exists())

  def test_existing_installation_paths_require_manual_inspection(self):
    self.program('stat', 'exit 0\n')
    result = self.run_bootstrap()
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('existing', result.stderr)
    self.assertFalse(self.marker.exists())

  def test_checksum_failure_does_not_run_installer(self):
    self.program('shasum', 'cat >/dev/null\nexit 1\n')
    result = self.run_bootstrap()
    self.assertNotEqual(result.returncode, 0)
    self.assertFalse(self.marker.exists())

  def test_download_failure_does_not_run_installer(self):
    self.program('curl', 'exit 22\n')
    result = self.run_bootstrap()
    self.assertEqual(result.returncode, 22)
    self.assertFalse(self.marker.exists())

  def test_requires_explicit_install_request(self):
    env = dict(os.environ, APP_SANDBOX_CONTAINER_ID='')
    result = subprocess.run(['/bin/bash', str(BOOTSTRAP)], env=env,
                            capture_output=True, text=True)
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('--install', result.stderr)

  def test_refuses_install_inside_safehouse(self):
    with tempfile.TemporaryDirectory() as directory:
      marker = Path(directory) / 'installed'
      bindir = Path(directory) / 'bin'
      bindir.mkdir()
      curl = bindir / 'curl'
      curl.write_text('#!/bin/sh\ntouch "$INSTALL_MARKER"\n')
      curl.chmod(0o755)
      env = dict(os.environ, APP_SANDBOX_CONTAINER_ID='agent-safehouse',
                 PATH=str(bindir) + ':/usr/bin:/bin', INSTALL_MARKER=str(marker))
      result = subprocess.run(['/bin/bash', str(BOOTSTRAP), '--install'],
                              env=env, capture_output=True, text=True)
      self.assertNotEqual(result.returncode, 0)
      self.assertIn('outside Safehouse', result.stderr)
      self.assertFalse(marker.exists())


if __name__ == '__main__':
  unittest.main()
