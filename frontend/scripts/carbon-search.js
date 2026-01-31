#!/usr/bin/env node

/**
 * Carbon Components Search Script
 * Quickly search for Carbon components and their usage
 * 
 * Usage:
 *   pnpm carbon:search <component>
 *   pnpm carbon:search button
 *   pnpm carbon:search "data table"
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CARBON_REF_DIR = path.join(__dirname, '../../docs/carbon-reference');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function searchInFile(filePath, searchTerm) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const results = [];
  const searchRegex = new RegExp(searchTerm, 'gi');

  lines.forEach((line, index) => {
    if (searchRegex.test(line)) {
      results.push({
        line: index + 1,
        content: line.trim(),
      });
    }
  });

  return results;
}

function formatResults(fileName, results, searchTerm) {
  if (results.length === 0) return '';

  const output = [`\n${colors.bright}${colors.blue}📄 ${fileName}${colors.reset}`];
  
  results.slice(0, 5).forEach(result => {
    let highlightedContent = result.content;
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    highlightedContent = highlightedContent.replace(regex, `${colors.bright}${colors.green}$1${colors.reset}`);
    
    output.push(
      `  ${colors.dim}Line ${result.line}:${colors.reset} ${highlightedContent}`
    );
  });

  if (results.length > 5) {
    output.push(`  ${colors.dim}... and ${results.length - 5} more matches${colors.reset}`);
  }

  return output.join('\n');
}

function searchComponents(searchTerm) {
  console.log(`${colors.bright}${colors.cyan}🔍 Searching for "${searchTerm}" in Carbon reference...${colors.reset}\n`);

  const files = [
    { name: 'COMPONENT_CATALOG.md', description: 'Component descriptions and use cases' },
    { name: 'COMPONENT_EXAMPLES.md', description: 'Copy-paste ready examples' },
    { name: 'USAGE_GUIDE.md', description: 'Best practices and patterns' },
    { name: 'CSS_UTILITIES.md', description: 'Design tokens and utilities' },
  ];

  let totalMatches = 0;
  const outputs = [];

  files.forEach(file => {
    const filePath = path.join(CARBON_REF_DIR, file.name);
    
    if (!fs.existsSync(filePath)) {
      console.log(`${colors.yellow}⚠ ${file.name} not found${colors.reset}`);
      return;
    }

    const results = searchInFile(filePath, searchTerm);
    totalMatches += results.length;

    if (results.length > 0) {
      const formatted = formatResults(file.name, results, searchTerm);
      if (formatted) outputs.push(formatted);
    }
  });

  if (outputs.length > 0) {
    outputs.forEach(output => console.log(output));
    console.log(`\n${colors.bright}${colors.green}✅ Found ${totalMatches} matches across ${outputs.length} files${colors.reset}`);
    
    // Provide helpful next steps
    console.log(`\n${colors.bright}💡 Next steps:${colors.reset}`);
    console.log(`  • Open the matching file: ${colors.cyan}code docs/carbon-reference/<filename>${colors.reset}`);
    console.log(`  • View examples: ${colors.cyan}code docs/carbon-reference/COMPONENT_EXAMPLES.md${colors.reset}`);
    console.log(`  • Check live docs: ${colors.cyan}open https://svelte.carbondesignsystem.com${colors.reset}`);
  } else {
    console.log(`${colors.red}❌ No matches found for "${searchTerm}"${colors.reset}`);
    console.log(`\n${colors.yellow}💡 Try searching for:${colors.reset}`);
    console.log('  • Component names: button, modal, datatable');
    console.log('  • UI patterns: form, navigation, layout');
    console.log('  • CSS tokens: spacing, color, typography');
  }
}

// Check for component examples directory
function listAvailableExamples() {
  const examplesDir = path.join(CARBON_REF_DIR, 'docs/src/pages/components');
  
  if (fs.existsSync(examplesDir)) {
    const files = fs.readdirSync(examplesDir)
      .filter(f => f.endsWith('.svx'))
      .map(f => f.replace('.svx', ''));
    
    console.log(`\n${colors.bright}${colors.cyan}📚 Available component examples:${colors.reset}`);
    
    const columns = 3;
    const columnWidth = 25;
    
    for (let i = 0; i < files.length; i += columns) {
      const row = files.slice(i, i + columns)
        .map(f => f.padEnd(columnWidth))
        .join('');
      console.log(`  ${colors.dim}${row}${colors.reset}`);
    }
  }
}

// Main execution
const searchTerm = process.argv.slice(2).join(' ');

if (!searchTerm) {
  console.log(`${colors.bright}${colors.cyan}Carbon Components Search Tool${colors.reset}`);
  console.log('\nUsage:');
  console.log(`  ${colors.green}pnpm carbon:search <search-term>${colors.reset}`);
  console.log('\nExamples:');
  console.log(`  ${colors.dim}pnpm carbon:search button${colors.reset}`);
  console.log(`  ${colors.dim}pnpm carbon:search "data table"${colors.reset}`);
  console.log(`  ${colors.dim}pnpm carbon:search modal${colors.reset}`);
  console.log(`  ${colors.dim}pnpm carbon:search spacing${colors.reset}`);
  
  listAvailableExamples();
} else {
  searchComponents(searchTerm);
}