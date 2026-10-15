const c = require('fs').readFileSync('sasando_live_enhanced_out/fig_sasando_live_enhanced.html', 'utf8');
const srcMatches = [...c.matchAll(/src=["']([^"']+)["']/g)];
console.log('src= attributes found:', srcMatches.length);
srcMatches.forEach(m => console.log('  src:', m[1]));
const linkHref = [...c.matchAll(/href=["']([^"']+)["']/g)];
console.log('href= attributes found:', linkHref.length);
linkHref.forEach(m => console.log('  href:', m[1]));
const injected = c.match(/<script>\s*\(function\(\)\{\s*var root = document\.getElementById\('live-root-fig_sasando_live_enhanced'[\s\S]*?<\/script>/);
console.log('injected live script found:', !!injected);
if (injected) {
  console.log('fetch( in injected block:', /fetch\(/.test(injected[0]));
  console.log('XMLHttpRequest in injected block:', /XMLHttpRequest/.test(injected[0]));
  console.log('eval( in injected block:', /[^a-zA-Z0-9_]eval\(/.test(injected[0]));
}
