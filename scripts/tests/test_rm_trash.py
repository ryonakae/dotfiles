import configparser
import json
import os
import pty
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / 'config/.local/bin/rm'


class RmTrashTests(unittest.TestCase):
  def setUp(self):
    self.temp = tempfile.TemporaryDirectory()
    self.addCleanup(self.temp.cleanup)
    self.base = Path(self.temp.name)
    self.home = self.base / 'home'
    self.home.mkdir()
    self.work = self.base / 'work'
    self.work.mkdir()
    self.bin = self.base / 'bin'
    self.bin.mkdir()
    self.config = self.home / '.config/gomi/config.yaml'
    self.config.parent.mkdir(parents=True)
    self.config.write_text('core:\n  trash:\n    strategy: xdg\n')
    self.log = self.base / 'calls.jsonl'
    self.gomi = self.bin / 'gomi'
    self.gomi.write_text(
      '#!' + sys.executable + '\n'
      'import json, os, signal, sys, time\n'
      'if os.getenv("FAKE_IGNORE_SIGNALS"):\n'
      '  for sig in [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]:\n'
      '    signal.signal(sig, signal.SIG_IGN)\n'
      'from pathlib import Path\n'
      'args = sys.argv[1:]\n'
      'with open(os.environ["CALL_LOG"], "a") as log:\n'
      '  log.write(json.dumps({"args": args, "data": os.getenv("XDG_DATA_HOME"), '
      '"config": os.getenv("XDG_CONFIG_HOME"), "pid": os.getpid(), '
      '"parent": os.getppid()}) + "\\n")\n'
      'source = Path(args[args.index("--") + 1])\n'
      'if os.getenv("FAKE_FAIL") == source.name or '
      'Path(args[1]).read_text() == "invalid config":\n'
      '  print("storage/config failure", file=sys.stderr)\n'
      '  sys.exit(23)\n'
      'trash = Path(os.environ["FAKE_TRASH"])\n'
      'trash.mkdir(exist_ok=True)\n'
      'if os.getenv("FAKE_BLOCK") == source.name:\n'
      '  while not Path(os.environ["RELEASE"]).exists(): time.sleep(0.01)\n'
      'destination = trash / source.name\n'
      'counter = 1\n'
      'while destination.exists():\n'
      '  destination = trash / (source.name + "_" + str(counter))\n'
      '  counter += 1\n'
      'source.rename(destination)\n'
    )
    self.gomi.chmod(0o755)
    self.env = dict(os.environ, HOME=str(self.home),
                    PATH=str(self.bin) + ':' + os.environ['PATH'],
                    CALL_LOG=str(self.log), FAKE_TRASH=str(self.base / 'saved'),
                    XDG_DATA_HOME=str(self.home / 'custom data'),
                    XDG_CONFIG_HOME=str(self.home / 'custom config'))

  def run_rm(self, *args, **kwargs):
    return subprocess.run([str(WRAPPER), *map(str, args)], cwd=self.work,
                          env=self.env, capture_output=True, text=True,
                          timeout=15, **kwargs)

  def calls(self):
    if not self.log.exists():
      return []
    return [json.loads(line) for line in self.log.read_text().splitlines()]

  def start_rm(self, *args, cwd=None):
    process = subprocess.Popen([str(WRAPPER), *map(str, args)], cwd=cwd or self.work,
                               env=self.env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    self.addCleanup(self.finish_process, process)
    return process

  def finish_process(self, process):
    if 'RELEASE' in self.env:
      Path(self.env['RELEASE']).touch()
    if process.poll() is None:
      process.terminate()
    process.communicate(timeout=10)

  def wait_for_calls(self, count):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
      calls = self.calls()
      if len(calls) >= count:
        return calls
      time.sleep(0.01)
    self.fail(f'expected {count} calls, got {self.calls()}')

  def test_processes_and_each_operand_share_one_serial_queue(self):
    other = self.base / 'other'
    other.mkdir()
    (self.work / 'same').write_text('first')
    (self.work / 'next').write_text('next')
    (other / 'same').write_text('second')
    self.env['FAKE_BLOCK'] = 'same'
    release = self.base / 'release'
    self.env['RELEASE'] = str(release)
    self.addCleanup(release.touch)
    first = self.start_rm('same', 'next')
    self.wait_for_calls(1)
    second = self.start_rm('same', cwd=other)
    time.sleep(0.4)
    self.assertEqual(len(self.calls()), 1)
    self.assertIsNone(second.poll())
    release.touch()
    for process in [first, second]:
      _, stderr = process.communicate(timeout=10)
      self.assertEqual(process.returncode, 0, stderr)
    self.assertEqual(len(self.calls()), 3)
    self.assertEqual((self.base / 'saved/same').read_text(), 'first')
    self.assertEqual((self.base / 'saved/same_1').read_text(), 'second')
    self.assertEqual((self.base / 'saved/next').read_text(), 'next')

  def prepare_blocked_move(self):
    (self.work / 'blocked').write_text('first')
    (self.work / 'next').write_text('must stay')
    (self.work / 'second').write_text('second')
    self.env['FAKE_BLOCK'] = 'blocked'
    self.env['FAKE_IGNORE_SIGNALS'] = '1'
    release = self.base / 'release'
    self.env['RELEASE'] = str(release)
    first = self.start_rm('blocked', 'next')
    call = self.wait_for_calls(1)[0]
    return first, call, release

  def assert_cancel_waits_for_child(self, signum):
    first, call, release = self.prepare_blocked_move()
    os.kill(call['parent'], signum)
    second = self.start_rm('second')
    time.sleep(0.4)
    self.assertIsNone(first.poll(), 'wrapper must reap its still-live child')
    self.assertEqual(len(self.calls()), 1)
    release.touch()
    _, stderr = first.communicate(timeout=10)
    self.assertEqual(first.returncode, 128 + signum, stderr)
    self.assertEqual(second.communicate(timeout=10)[1], '')
    self.assertEqual(second.returncode, 0)
    self.assertEqual((self.work / 'next').read_text(), 'must stay')

  def test_sigterm_waits_for_child_and_cancels_next_operand(self):
    self.assert_cancel_waits_for_child(signal.SIGTERM)

  def test_sigint_waits_for_child_and_cancels_next_operand(self):
    self.assert_cancel_waits_for_child(signal.SIGINT)

  def test_sighup_waits_for_child_and_cancels_next_operand(self):
    self.assert_cancel_waits_for_child(signal.SIGHUP)

  def test_sigkill_keeps_child_lock_until_child_finishes(self):
    first, call, release = self.prepare_blocked_move()
    os.kill(call['parent'], signal.SIGKILL)
    second = self.start_rm('second')
    time.sleep(0.4)
    self.assertEqual(len(self.calls()), 1)
    self.assertIsNone(second.poll())
    release.touch()
    first.communicate(timeout=10)
    self.assertNotEqual(first.returncode, 0)
    _, stderr = second.communicate(timeout=10)
    self.assertEqual(second.returncode, 0, stderr)
    self.assertEqual((self.work / 'next').read_text(), 'must stay')
    self.assertEqual((self.base / 'saved/blocked').read_text(), 'first')

  def test_cancelling_lock_waiter_does_not_move_its_target(self):
    first, _, release = self.prepare_blocked_move()
    waiter = self.start_rm('second')
    time.sleep(0.4)
    waiter.terminate()
    waiter.communicate(timeout=10)
    self.assertNotEqual(waiter.returncode, 0)
    self.assertEqual(len(self.calls()), 1)
    release.touch()
    first.communicate(timeout=10)
    self.assertEqual(first.returncode, 0)
    self.assertEqual((self.work / 'second').read_text(), 'second')

  def test_trash_roots_contents_and_ancestors_cannot_be_moved(self):
    default_trash = self.home / '.local/share/Trash'
    custom_trash = Path(self.env['XDG_DATA_HOME']) / 'Trash'
    for trash in [default_trash, custom_trash]:
      (trash / 'files').mkdir(parents=True)
      (trash / 'files/payload').write_text('saved')
    alias = self.base / 'alias'
    alias.symlink_to(custom_trash.parent, target_is_directory=True)
    for target in [default_trash, default_trash.parent, default_trash.parent.parent,
                   self.home, custom_trash, custom_trash.parent,
                   custom_trash / 'files/payload', alias / 'Trash', alias / 'Trash/files']:
      with self.subTest(target=target):
        result = self.run_rm('-rf', target)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('protected trash/lock path', result.stderr)
        self.assertEqual(self.calls(), [])
    self.assertEqual((custom_trash / 'files/payload').read_text(), 'saved')
    result = self.run_rm('missing')
    self.assertNotEqual(result.returncode, 0)
    lock = self.home / '.local/share/.rm-gomi.lock'
    self.assertNotEqual(self.run_rm('-f', lock).returncode, 0)
    link = self.work / 'trash-link'
    link.symlink_to(custom_trash, target_is_directory=True)
    result = self.run_rm('trash-link')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertTrue(custom_trash.is_dir())
    external = self.work / ('volume/.Trash-' + str(os.getuid()))
    external.mkdir(parents=True)
    result = self.run_rm('-r', external.parent)
    self.assertNotEqual(result.returncode, 0)
    self.assertTrue(external.exists())

  @unittest.skipUnless(shutil.which('fish'), 'fish is not installed')
  def test_noninteractive_fish_and_its_child_shells_use_same_wrapper(self):
    local_bin = self.home / '.local/bin'
    local_bin.mkdir(parents=True)
    (local_bin / 'rm').symlink_to(WRAPPER)
    for name in ['fish file', 'sh file', 'bash file']:
      (self.work / name).write_text(name)
    fish_dir = ROOT / 'config/.config/fish'
    result = subprocess.run(
      [shutil.which('fish'), '--no-config', '-c',
       'source "$argv[1]/conf.d/gomi.fish"; '
       'source "$argv[1]/functions/rm.fish"; '
       'command -s rm; rm -- "fish file"; or exit; '
       '/bin/sh -c \'command -v rm; rm -- "sh file"\'; or exit; '
       '/bin/bash --noprofile --norc -c \'command -v rm; rm -- "bash file"\'',
       str(fish_dir)], cwd=self.work, env=self.env, text=True,
      capture_output=True, timeout=15)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual(result.stdout.splitlines(), [str(local_bin / 'rm')] * 3)
    self.assertEqual(len(self.calls()), 3)
    for name in ['fish file', 'sh file', 'bash file']:
      self.assertEqual((self.base / 'saved' / name).read_text(), name)

  @unittest.skipUnless(shutil.which('gomi'), 'gomi is not installed')
  def test_real_gomi_xdg_metadata_and_storage_failure(self):
    installed = shutil.which('gomi')
    self.gomi.unlink()
    self.gomi.symlink_to(installed)
    shutil.copyfile(ROOT / 'config/.config/gomi/config.yaml', self.config)
    self.env['TMPDIR'] = str(self.base)
    directory = self.work / 'directory'
    directory.mkdir()
    (directory / 'nested').write_text('nested')
    target = self.work / 'target'
    target.write_text('target stays')
    (self.work / 'link').symlink_to(target)
    for name in ['space name', '--prune=1d']:
      (self.work / name).write_text(name)
    result = self.run_rm('-r', '--', 'space name', '--prune=1d', 'directory', 'link')
    self.assertEqual(result.returncode, 0, result.stderr)
    trash = Path(self.env['XDG_DATA_HOME']) / 'Trash'
    for name in ['space name', '--prune=1d', 'directory', 'link']:
      info = configparser.ConfigParser(interpolation=None)
      info.read(trash / 'info' / (name + '.trashinfo'))
      self.assertEqual(unquote(info['Trash Info']['Path']), str(self.work.resolve() / name))
      self.assertFalse((self.work / name).is_symlink())
      self.assertFalse((self.work / name).exists())
    self.assertEqual((trash / 'files/space name').read_text(), 'space name')
    self.assertEqual((trash / 'files/directory/nested').read_text(), 'nested')
    self.assertTrue((trash / 'files/link').is_symlink())
    self.assertEqual(target.read_text(), 'target stays')
    self.assertFalse((self.home / '.local/share/Trash').exists())
    broken = self.work / 'broken'
    broken.symlink_to(self.work / 'missing-target')
    result = self.run_rm('-f', 'broken')
    self.assertNotEqual(result.returncode, 0)
    self.assertTrue(broken.is_symlink())
    self.assertFalse((trash / 'files/broken').is_symlink())
    unusable = self.home / 'not a directory'
    unusable.write_text('blocked storage')
    self.env['XDG_DATA_HOME'] = str(unusable)
    result = self.run_rm('-f', 'target')
    self.assertNotEqual(result.returncode, 0)
    self.assertEqual(target.read_text(), 'target stays')
    self.config.write_text('core: [')
    result = self.run_rm('target')
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('config', result.stderr)
    self.assertEqual(target.read_text(), 'target stays')

  def test_interactive_requires_terminal_and_confirms_whole_target(self):
    target = self.work / 'payload'
    target.write_text('keep me')
    for args in [['-i', 'payload'], ['-fi', 'payload']]:
      result = self.run_rm(*args, input='y\n')
      self.assertNotEqual(result.returncode, 0)
      self.assertIn('terminal', result.stderr)
      self.assertTrue(target.exists())
      self.assertEqual(self.calls(), [])
    for answer, moved in [('n\n', False), ('y\n', True)]:
      master, slave = pty.openpty()
      try:
        os.write(master, answer.encode())
        result = self.run_rm('-i', 'payload', stdin=slave)
      finally:
        os.close(master)
        os.close(slave)
      self.assertEqual(result.returncode, 0, result.stderr)
      self.assertIn('entire target', result.stderr)
      self.assertIn('trash', result.stderr)
      self.assertEqual(not target.exists(), moved)
    target.write_text('force wins')
    self.assertEqual(self.run_rm('-if', 'payload').returncode, 0)
    directory = self.work / 'directory'
    directory.mkdir()
    (directory / 'nested').write_text('whole directory')
    master, slave = pty.openpty()
    try:
      os.write(master, b'y\n')
      result = self.run_rm('-ri', 'directory', stdin=slave)
    finally:
      os.close(master)
      os.close(slave)
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual((self.base / 'saved/directory/nested').read_text(), 'whole directory')

  def test_dependency_config_and_storage_failures_never_fallback(self):
    target = self.work / 'payload'
    target.write_text('keep me')
    self.env['FAKE_FAIL'] = 'payload'
    result = self.run_rm('-f', 'payload')
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('payload', result.stderr)
    self.assertIn('exit 23', result.stderr)
    self.assertEqual(target.read_text(), 'keep me')
    del self.env['FAKE_FAIL']
    self.config.write_text('invalid config')
    self.assertNotEqual(self.run_rm('payload').returncode, 0)
    self.assertTrue(target.exists())
    self.config.unlink()
    before = len(self.calls())
    result = self.run_rm('payload')
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('managed config', result.stderr)
    self.assertEqual(len(self.calls()), before)
    self.assertFalse(self.config.exists())
    self.config.write_text('core: {}')
    self.gomi.unlink()
    self.env['PATH'] = str(self.bin)
    (self.bin / 'uv').symlink_to(shutil.which('uv'))
    for args in [['payload'], ['-f', 'payload']]:
      result = self.run_rm(*args)
      self.assertNotEqual(result.returncode, 0)
      self.assertIn('gomi', result.stderr)
      self.assertTrue(target.exists())
    (self.bin / 'uv').unlink()
    result = self.run_rm('payload')
    self.assertNotEqual(result.returncode, 0)
    self.assertTrue(target.exists())

  def test_partial_failure_is_reported_and_other_operands_are_saved(self):
    for name in ['first', 'failed', 'last']:
      (self.work / name).write_text(name)
    self.env['FAKE_FAIL'] = 'failed'
    result = self.run_rm('first', 'failed', 'last')
    self.assertNotEqual(result.returncode, 0)
    self.assertIn('failed', result.stderr)
    self.assertEqual((self.work / 'failed').read_text(), 'failed')
    for name in ['first', 'last']:
      self.assertEqual((self.base / 'saved' / name).read_text(), name)

  def test_force_missing_files_directories_and_symlinks(self):
    for args, success in [([], False), (['-f'], True), (['missing'], False),
                          (['-f', 'missing'], True)]:
      with self.subTest(args=args):
        result = self.run_rm(*args)
        self.assertEqual(result.returncode == 0, success, result.stderr)
        self.assertEqual(self.calls(), [])
    directory = self.work / 'directory'
    directory.mkdir()
    (directory / 'payload').write_text('keep me')
    for args in [['directory'], ['-f', 'directory'], ['-d', 'directory']]:
      with self.subTest(args=args):
        self.assertNotEqual(self.run_rm(*args).returncode, 0)
        self.assertTrue((directory / 'payload').exists())
        self.assertEqual(self.calls(), [])
    result = self.run_rm('-R', 'directory')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertEqual((self.base / 'saved/directory/payload').read_text(), 'keep me')
    empty = self.work / 'empty'
    empty.mkdir()
    self.assertEqual(self.run_rm('-d', 'empty').returncode, 0)
    target = self.work / 'target'
    target.write_text('target stays')
    for name, destination in [('link', target), ('broken', self.work / 'absent'),
                              ('dirlink', self.base / 'saved/directory')]:
      with self.subTest(name=name):
        (self.work / name).symlink_to(destination)
        result = self.run_rm(name)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.base / 'saved' / name).is_symlink())
    self.assertEqual(target.read_text(), 'target stays')

  def test_rm_options_are_parsed_before_any_operand_is_moved(self):
    for args in [['first', '--prune=1d'], ['first', '--config', 'evil'],
                 ['-b', 'first'], ['-rfZ', 'first'], ['--restore', 'first'],
                 ['--unknown', 'first'], ['-I', 'first']]:
      with self.subTest(args=args):
        (self.work / 'first').write_text('keep me')
        result = self.run_rm(*args)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('unsupported option', result.stderr)
        self.assertTrue((self.work / 'first').exists())
        self.assertEqual(self.calls(), [])
    (self.work / 'first').write_text('keep me')
    result = self.run_rm('-rfRv', 'first')
    self.assertEqual(result.returncode, 0, result.stderr)
    self.assertIn('moved to trash', result.stdout)
    self.assertEqual(self.calls()[-1]['args'],
                     ['--config', str(self.config), '--', 'first'])

  def test_literal_names_and_explicit_managed_config_in_isolated_project(self):
    (self.work / 'pyproject.toml').write_text('[project]\nname="invalid"\n')
    for name in ['space name', '--prune=1d', '$HOME']:
      with self.subTest(name=name):
        (self.work / name).write_text('keep me')
        result = self.run_rm('--', name)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual((self.base / 'saved' / name).read_text(), 'keep me')
        call = self.calls()[-1]
        self.assertEqual(call['args'], ['--config', str(self.config), '--', name])
        self.assertEqual(call['data'], self.env['XDG_DATA_HOME'])
        self.assertEqual(call['config'], self.env['XDG_CONFIG_HOME'])
    self.assertFalse((self.work / '.venv').exists())
    self.assertFalse((self.work / 'uv.lock').exists())


if __name__ == '__main__':
  unittest.main()
