const fs = require('fs');
const path = require('path');

const distAssetsDir = path.join(__dirname, '..', 'frontend', 'dist', 'assets');
const files = fs.readdirSync(distAssetsDir).filter(f => f.endsWith('.js'));

let hasError = false;

for (const file of files) {
  const filePath = path.join(distAssetsDir, file);
  const content = fs.readFileSync(filePath, 'utf8');

  // Check for any hardcoded localhost or 127.0.0.1 URLs
  const urlMatches = content.match(/https?:\/\/[^\s"'`]*(localhost|127\.0\.0\.1)[^\s"'`]*/gi);
  if (urlMatches && urlMatches.length > 0) {
    console.error(`FAILED: Found hardcoded localhost URLs in ${file}:`, urlMatches);
    hasError = true;
  } else {
    console.log(`PASSED: Zero hardcoded localhost URLs found in ${file}`);
  }

  // Also check if onrender.com is present in the build
  if (content.includes('adaptiveclass-ai.onrender.com')) {
    console.log(`PASSED: Verified production Render backend URL is baked into ${file}`);
  }
}

if (hasError) {
  process.exit(1);
} else {
  console.log('SUCCESS: Production bundle verification passed cleanly.');
}
