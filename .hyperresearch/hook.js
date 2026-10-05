#!/usr/bin/env node
/**
 * hyperresearch PreToolUse hook — reminds agent to check research base first.
 * Installed by: hyperresearch install
 */
const fs = require('fs');
const path = require('path');

const HPR = 'C:\\Users\\flash\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\hyperresearch.exe';

// Check if a .hyperresearch directory exists (vault is initialized)
function findVault() {
    let dir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    while (true) {
        if (fs.existsSync(path.join(dir, '.hyperresearch'))) return dir;
        const parent = path.dirname(dir);
        if (parent === dir) return null;
        dir = parent;
    }
}

const vault = findVault();
if (vault) {
    const msg = [
        'HYPERRESEARCH: A research knowledge base exists in this project.',
        '',
        'BEFORE searching the web, check existing research:',
        '  ' + HPR + ' search "<your query>" -j',
        '',
        'DO NOT use WebFetch for source pages. Use hyperresearch fetch instead:',
        '  ' + HPR + ' fetch "<url>" --tag <topic> -j',
        'It runs a real headless browser, saves full content + screenshot, and indexes for future sessions.',
        '',
        'After fetching, READ the content and FOLLOW LINKS to primary sources. Keep fetching until you have the real sources, not just summaries.',
        '',
        'For multiple URLs, use subagents to fetch in parallel.',
    ].join('\n');
    // stderr reaches the model only on exit 2. On exit 0 it goes to the debug
    // log, so the reminder has to leave as hookSpecificOutput JSON on stdout.
    process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
            hookEventName: 'PreToolUse',
            additionalContext: msg
        }
    }) + '\n');
}
