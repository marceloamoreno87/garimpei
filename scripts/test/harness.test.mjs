import test from 'node:test';
import assert from 'node:assert/strict';
import { cpSync, existsSync, mkdtempSync, mkdirSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'garimpei-harness-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  cpSync(new URL('../', import.meta.url), join(root, 'scripts'), {
    recursive: true,
    filter: (source) => !source.endsWith('/test'),
  });
  const git = spawnSync('git', ['init', '--quiet', '--initial-branch=main', root]);
  assert.equal(git.status, 0);
  return root;
}

test('init without Python scaffold diagnoses the prerequisite without generating app state', (t) => {
  const root = fixture(t);
  const before = readdirSync(root).sort();
  const result = spawnSync('bash', ['scripts/init.sh'], { cwd: root, encoding: 'utf8' });
  assert.equal(result.status, 64, result.stdout + result.stderr);
  assert.match(result.stderr, /scaffold/i);
  assert.deepEqual(readdirSync(root).sort(), before);
});

test('resolver without Python scaffold does not announce an environment', (t) => {
  const root = fixture(t);
  const result = spawnSync('bash', ['scripts/resolve-env.sh'], {
    cwd: root, encoding: 'utf8',
  });
  assert.equal(result.status, 64, result.stderr);
  assert.match(result.stderr, /scaffold/i);
  assert.equal(result.stdout, '');
});

test('backend gates fail before scaffolding without invoking or downloading tools', (t) => {
  const root = fixture(t);
  const bin = join(root, 'bin');
  mkdirSync(bin);
  const marker = join(root, 'unexpected-tool-execution');
  writeFileSync(join(bin, 'npx'), '#!/bin/sh\ntouch "$HARNESS_TEST_MARKER"\nexit 99\n', { mode: 0o755 });
  const result = spawnSync(process.execPath, ['scripts/run-gates.mjs'], {
    cwd: root, encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, HARNESS_TEST_MARKER: marker },
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /scaffold|backend/i);
  assert.equal(existsSync(marker), false);
});

test('setup reuses the same marketplace without replacing its existing revision', (t) => {
  const root = fixture(t);
  const bin = join(root, 'bin');
  mkdirSync(bin);
  writeFileSync(join(bin, 'codex'), `#!/bin/sh
if [ "$1 $2 $3" = "plugin marketplace list" ]; then
  printf '%s\\n' '{"marketplaces":[{"name":"fullcycle-claude-marketplace","marketplaceSource":{"sourceType":"git","source":"https://github.com/devfullcycle/claude-mkt-place.git"}}]}'
elif [ "$1 $2" = "plugin add" ]; then
  printf '%s\\n' "$3"
elif [ "$1 $2" = "plugin list" ]; then
  printf '%s\\n' '{}'
else
  echo "Unexpected mutation: $*" >&2
  exit 57
fi
`, { mode: 0o755 });
  const result = spawnSync('bash', ['scripts/setup-codex.sh'], {
    cwd: root, encoding: 'utf8', env: { ...process.env, PATH: `${bin}:${process.env.PATH}` },
  });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.equal(result.stdout.split('\n').filter((line) => line.endsWith('@fullcycle-claude-marketplace')).length, 4);
});
