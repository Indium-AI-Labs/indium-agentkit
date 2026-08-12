#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const args = process.argv.slice(2);
const command = args[0] || 'install';
const targetDir = process.cwd();
const repoRoot = path.resolve(__dirname, '..');

if (command === 'help' || command === '--help' || command === '-h') {
  console.log(`\x1b[36mindium-agentkit CLI v1.0.0\x1b[0m`);
  console.log(`Portable AI coding-agent skills, subagents, and templates.\n`);
  console.log(`Usage:`);
  console.log(`  npx indium-agentkit add [name]    Install skills and agents into current project`);
  console.log(`  npx indium-agentkit install       Install all skills, agents, and Cursor rules`);
  console.log(`\nExamples:`);
  console.log(`  npx indium-agentkit add frontend-ship`);
  console.log(`  npx indium-agentkit add frontend-builder`);
  process.exit(0);
}

if (command === 'add' || command === 'install') {
  const targetItem = args[1] || 'all';
  console.log(`\x1b[36m[indium-agentkit]\x1b[0m Installing skills and agents (${targetItem}) into ${targetDir}...`);
  try {
    const installScript = path.join(repoRoot, 'scripts', 'install.sh');
    if (fs.existsSync(installScript)) {
      execSync(`bash "${installScript}" "${targetDir}"`, { stdio: 'inherit' });
      console.log(`\x1b[32m[indium-agentkit]\x1b[0m Successfully installed skills and agent definitions into ${targetDir}!`);
    } else {
      console.error(`\x1b[31m[error]\x1b[0m Installation script not found at ${installScript}`);
      process.exit(1);
    }
  } catch (err) {
    console.error(`\x1b[31m[error]\x1b[0m Failed to run installation:`, err.message);
    process.exit(1);
  }
} else {
  console.log(`\x1b[36mindium-agentkit CLI v1.0.0\x1b[0m`);
  console.log(`Usage: npx indium-agentkit add [name]`);
}
