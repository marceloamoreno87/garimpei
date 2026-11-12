#!/usr/bin/env node
import { existsSync, readdirSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const backend = resolve(process.argv.find(x => x.startsWith('--cwd='))?.slice(6) || join(root, 'apps/backend'));
const groups = [
 ['Tipos', [['mypy','--strict','src','tests','scripts/quality','manage.py']]],
 ['Lint', [['ruff','check','src','tests','scripts','manage.py'],['ruff','format','--check','src','tests','scripts','manage.py'],['djlint','src/garimpei/infra/http/templates','--lint','--profile=django']]],
 ['Limites', [['lint-imports','--config','.importlinter']]],
 ['Arquitetura', [['python','scripts/quality/check_architecture.py']]],
 ['Ciclos', [['python','scripts/quality/check_cycles.py']]],
 ['Não utilizados', [['vulture','src','scripts/quality','quality/vulture_whitelist.py','--min-confidence','60'],['deptry','.']]],
];
function required(path) {
 if (!existsSync(join(backend,path))) { console.error(`[gates] Backend/prerequisite absent: ${path}`); process.exit(64); }
}
for (const path of ['pyproject.toml','uv.lock','.python-version','.importlinter','src/garimpei/main.py','tests','scripts/quality/check_architecture.py','scripts/quality/check_cycles.py','quality/entrypoints.json','quality/vulture_whitelist.py']) required(path);
for (const tool of ['python','mypy','ruff','djlint','lint-imports','vulture','deptry']) required(`.venv/bin/${tool}`);
const scope = readdirSync(join(backend,'src/garimpei'),{recursive:true}).filter(x=>x.endsWith('.py'));
if (!scope.length) { console.error('[gates] Empty Python scope'); process.exit(64); }
for (const [name,commands] of groups) {
 console.log(`[gates] ${name}: ${scope.length} Python source files`);
 for (const command of commands) {
  const args=['run','--frozen','--no-sync',...command];console.log(`[gates] uv ${args.join(' ')}`);
  const result=spawnSync('uv',args,{cwd:backend,stdio:'inherit',env:{...process.env,DJANGO_SETTINGS_MODULE:'garimpei.config.test_settings'}});
  if(result.error){console.error(`[gates] ${name}: tool unavailable`);process.exit(64);}
  if(result.status!==0){console.error(`[gates] ${name}: FAILED`);process.exit(result.status||1);}
 }
 console.log(`[gates] ${name}: PASS`);
}
console.log('[gates] Six Python groups approved');
