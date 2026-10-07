"""Run outside Safehouse; creates and removes only a new dummy Keychain item/job."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid


def main():
  if os.environ.get('APP_SANDBOX_CONTAINER_ID') == 'agent-safehouse':
    raise SystemExit('Run outside Safehouse to check the native Keychain and launchd.')
  dotenvx = '/opt/homebrew/bin/dotenvx'
  with tempfile.TemporaryDirectory(prefix='dotfiles-keychain-') as temporary:
    base = Path(temporary)
    env_file = base / '.env'
    env_file.write_text('AGENT_TEST_TOKEN=dotfiles-dummy-token\n')
    env_file.chmod(0o600)
    # macOS Keychainのlogin contextは実HOMEを必要とする。envファイルは一時領域に閉じる。
    env = {'HOME': os.environ['HOME'], 'PATH': '/usr/bin:/bin',
           'USER': os.environ.get('USER', ''), 'TMPDIR': os.environ.get('TMPDIR', '/tmp')}
    public_key = None
    job = None

    def run(args):
      result = subprocess.run(args, env=env, cwd=base, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=25)
      if result.returncode:
        print(re.sub(r'[0-9a-f]{20,}', '<hex-redacted>', result.stderr), flush=True)
        raise AssertionError(args[0] + ' failed: exit=' + str(result.returncode))
      return result

    try:
      run([dotenvx, 'encrypt', '--quiet', '--no-armor', '-f', str(env_file)])
      match = re.search(r'^DOTENV_PUBLIC_KEY=[\"\']?([0-9a-f]+)', env_file.read_text(), re.M)
      assert match, 'missing public key'
      public_key = match.group(1)
      assert not (base / '.env.keys').exists(), 'unexpected key file'
      code = 'import os; assert os.environ.get("AGENT_TEST_TOKEN") == "dotfiles-dummy-token"'
      injected = [dotenvx, 'run', '--quiet', '--strict', '--no-armor', '-f', str(env_file), '-fk', '/dev/null', '--']
      run(injected + [sys.executable, '-c', code])
      print('PASS native Keychain without key file', flush=True)
      result_file = base / 'result'
      job = 'dotfiles.keychain-check.' + uuid.uuid4().hex
      child_code = code + '; from pathlib import Path; Path(' + repr(str(result_file)) + ').write_text("passed")'
      run(['/bin/launchctl', 'submit', '-l', job, '-o', str(base / 'stdout'), '-e', str(base / 'stderr'), '--',
           '/usr/bin/env', 'HOME=' + env['HOME'], 'PATH=' + env['PATH'], *injected, sys.executable, '-c', child_code])
      deadline = time.monotonic() + 20
      while time.monotonic() < deadline and not result_file.exists():
        time.sleep(0.1)
      assert result_file.exists() and result_file.read_text() == 'passed', 'launchd decryption did not complete'
      print('PASS real launchd noninteractive decryption', flush=True)
      run(['/bin/launchctl', 'remove', job])
      job = None
      env_file.unlink()
      missing = subprocess.run(injected + [sys.executable, '-c', 'raise SystemExit(99)'],
                               env=env, cwd=base, capture_output=True, timeout=25)
      assert missing.returncode != 0 and missing.returncode != 99, 'missing env did not stop child'
      print('PASS missing environment prevents child startup', flush=True)
    finally:
      if job:
        subprocess.run(['/bin/launchctl', 'remove', job], capture_output=True, timeout=15)
      if public_key:
        result = subprocess.run(['/usr/bin/security', 'delete-generic-password', '-s', 'dotenvx', '-a', public_key],
                                capture_output=True, timeout=15)
        assert result.returncode == 0, 'dummy Keychain cleanup failed'
    print('DOTENVX_RUNTIME_PASS', flush=True)


if __name__ == '__main__':
  main()
