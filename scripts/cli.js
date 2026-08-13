#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const args = process.argv.slice(2);
const command = args[0] || 'install';
const targetDir = process.cwd();
const repoRoot = path.resolve(__dirname, '..');

function parseTargetIde(args, projectPath) {
  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--target=')) {
      return args[i].split('=')[1].toLowerCase();
    }
    if ((args[i] === '-t' || args[i] === '--target') && args[i + 1]) {
      return args[i + 1].toLowerCase();
    }
  }

  // Auto-detection logic if no explicit target flag is passed
  const detected = [];
  if (fs.existsSync(path.join(projectPath, '.antigravity'))) detected.push('antigravity');
  if (fs.existsSync(path.join(projectPath, '.gemini'))) detected.push('gemini');
  if (fs.existsSync(path.join(projectPath, '.cursor'))) detected.push('cursor');
  if (fs.existsSync(path.join(projectPath, '.opencode'))) detected.push('opencode');
  if (fs.existsSync(path.join(projectPath, '.claude'))) detected.push('claude');
  if (fs.existsSync(path.join(projectPath, '.codex'))) detected.push('codex');

  if (detected.length === 1) {
    return detected[0];
  }
  return 'all';
}

if (command === 'help' || command === '--help' || command === '-h') {
  console.log(`\x1b[36mindium-ai-agentkit CLI v1.0.0\x1b[0m`);
  console.log(`Portable AI coding-agent skills, subagents, and templates.\n`);
  console.log(`Usage:`);
  console.log(`  npx indium-ai-agentkit add [name] [--target=<ide>]`);
  console.log(`  npx indium-ai-agentkit install [--target=<ide>]\n`);
  console.log(`Supported Target IDEs:`);
  console.log(`  --target=antigravity   Install for Antigravity IDE (.antigravity/skills)`);
  console.log(`  --target=gemini        Install for Gemini CLI (.gemini/skills)`);
  console.log(`  --target=cursor        Install Cursor Rules (.cursor/rules)`);
  console.log(`  --target=opencode      Install for OpenCode (.opencode/skills)`);
  console.log(`  --target=claude        Install for Claude Code (.claude/skills)`);
  console.log(`  --target=codex         Install for Codex (.codex/skills)`);
  console.log(`  --target=all           Install for all supported IDEs (default)\n`);
  console.log(`Examples:`);
  console.log(`  npx indium-ai-agentkit add frontend-ship --target=antigravity`);
  console.log(`  npx indium-ai-agentkit add frontend-ship --target=opencode`);
  process.exit(0);
}

if (command === 'add' || command === 'install') {
  const targetItem = args[1] && !args[1].startsWith('-') ? args[1] : 'all';
  const targetIde = parseTargetIde(args, targetDir);

  console.log(`\x1b[36m[indium-ai-agentkit]\x1b[0m Installing skills (${targetItem}) for target: \x1b[33m${targetIde}\x1b[0m...`);
  try {
    const installScript = path.join(repoRoot, 'scripts', 'install.sh');
    if (fs.existsSync(installScript)) {
      execSync(`bash "${installScript}" "${targetDir}" "${targetIde}"`, { stdio: 'inherit' });
      console.log(`\x1b[32m[indium-ai-agentkit]\x1b[0m Successfully installed skills (${targetItem}) for \x1b[33m${targetIde}\x1b[0m into ${targetDir}!`);
    } else {
      console.error(`\x1b[31m[error]\x1b[0m Installation script not found at ${installScript}`);
      process.exit(1);
    }
  } catch (err) {
    console.error(`\x1b[31m[error]\x1b[0m Failed to run installation:`, err.message);
    process.exit(1);
  }
} else {
  console.log(`\x1b[36mindium-ai-agentkit CLI v1.0.0\x1b[0m`);
  console.log(`Usage: npx indium-ai-agentkit add [name] [--target=<ide>]`);
}
