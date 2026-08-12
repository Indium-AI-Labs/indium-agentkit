#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const args = process.argv.slice(2);
const command = args[0] || 'install';
const targetDir = process.cwd();
const repoRoot = path.resolve(__dirname, '..');

if (command === 'add' || command === 'install') {
  const skillName = args[1] || 'all';
  console.log(`\x1b[36m[indium-agentkit]\x1b[0m Installing skills (${skillName}) into ${targetDir}...`);
  try {
    const installScript = path.join(repoRoot, 'scripts', 'install.sh');
    if (fs.existsSync(installScript)) {
      execSync(`bash "${installScript}" "${targetDir}"`, { stdio: 'inherit' });
      console.log(`\x1b[32m[indium-agentkit]\x1b[0m Successfully installed skills into ${targetDir}!`);
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
  console.log(`Usage: npx indium-agentkit add [skill-name]`);
}
