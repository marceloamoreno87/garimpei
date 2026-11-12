#!/usr/bin/env node
import assert from 'node:assert/strict';
import { existsSync, lstatSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const read = (path) => readFileSync(resolve(root, path), 'utf8');
const requiredSkills = [
  'prd-writer', 'spec-writer', 'clean-arch', 'implement-feature', 'evaluator',
  'fix-runner', 'implement-and-evaluate', 'implement-and-evaluate-tmux',
  'frontend-ui-design', 'playwright-cli', 'adrs-management', 'diagrams-generator',
  'project-analizer', 'development-guidelines',
];

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return lstatSync(path).isSymbolicLink() ? [] : walk(path);
    return [path];
  });
}

function checkSkills() {
  for (const name of requiredSkills) {
    const path = `.agents/skills/${name}/SKILL.md`;
    const text = read(path);
    const frontmatter = text.match(/^---\n([\s\S]*?)\n---\n/);
    assert.ok(frontmatter, `Frontmatter ausente: ${path}`);
    assert.match(frontmatter[1], new RegExp(`^name: ${name}$`, 'm'), `Nome inválido: ${path}`);
    assert.match(frontmatter[1], /^description: .+/m, `Descrição ausente: ${path}`);
    for (const match of text.matchAll(/\[[^\]]*\]\(([^)]+)\)/g)) {
      const target = match[1].split('#')[0];
      if (!target || /^(https?:|mailto:)/.test(target)) continue;
      assert.ok(existsSync(resolve(root, dirname(path), target)), `Link quebrado em ${path}: ${target}`);
    }
  }
  console.log(`[harness] ${requiredSkills.length} skills e referências de entrada válidas.`);
}

function checkScripts() {
  const files = [
    ...walk(join(root, 'scripts')),
    ...walk(join(root, '.agents/skills/clean-arch/scripts')),
    ...walk(join(root, '.agents/skills/implement-and-evaluate-tmux/scripts')),
  ].filter((path) => /\.(sh|mjs)$/.test(path));
  for (const path of files) {
    const command = path.endsWith('.sh') ? 'bash' : process.execPath;
    const flag = path.endsWith('.sh') ? '-n' : '--check';
    const result = spawnSync(command, [flag, path], { encoding: 'utf8' });
    assert.equal(result.status, 0, `${path}: ${result.stderr || result.error || 'erro de sintaxe'}`);
  }
  console.log(`[harness] Sintaxe de ${files.length} scripts validada.`);
}

function checkProgress() {
  const progress = JSON.parse(read('docs/prd_progress.json'));
  assert.equal(progress.schema_version, 1);
  assert.equal(progress.prd_path, 'docs/PRD.md');
  assert.ok(Number.isFinite(Date.parse(progress.generated_at)), 'generated_at inválido');
  assert.ok(progress.features && !Array.isArray(progress.features));
  const features = Object.entries(progress.features);
  if (features.length) assert.ok(existsSync(join(root, progress.prd_path)), 'Features exigem PRD');
  const states = new Set(['pending', 'implementing', 'implemented', 'done', 'fail', 'pr-blocked', 'removed']);
  for (const [id, feature] of features) {
    assert.match(id, /^F\d{2,}$/);
    assert.ok(states.has(feature.status), `Status inválido: ${id}`);
    assert.ok(Number.isInteger(feature.cycles) && feature.cycles >= 0, `Ciclos inválidos: ${id}`);
    assert.ok(Array.isArray(feature.dependencies), `Dependências inválidas: ${id}`);
    for (const dep of feature.dependencies) assert.ok(dep !== id && dep in progress.features, `Dependência inválida: ${id} -> ${dep}`);
  }
  console.log(`[harness] Progresso válido: ${features.length} features.`);
}


try {
  for (const path of ['AGENTS.md', 'README.md', 'docs/harness.md', 'plugins.md', '.codex/config.toml', '.playwright/cli.config.json']) {
    assert.ok(existsSync(join(root, path)), `Arquivo obrigatório ausente: ${path}`);
  }
  assert.equal(JSON.parse(read('.playwright/cli.config.json')).browser.browserName, 'chromium');
  checkSkills();
  checkScripts();
  checkProgress();
  console.log('[harness] Estrutura validada. Gates da aplicação dependem do scaffold.');
} catch (error) {
  console.error(`[harness] FALHA: ${error.message}`);
  process.exitCode = 1;
}
