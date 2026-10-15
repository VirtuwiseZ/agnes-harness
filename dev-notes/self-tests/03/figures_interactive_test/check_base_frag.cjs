const c = require('fs').readFileSync('sasando_live_out/fig_sasando_live.html', 'utf8');
const linkHref = [...c.matchAll(/href=["']([^"']+)["']/g)];
console.log('BASE (pre-change) demo href= count:', linkHref.length);
linkHref.slice(0, 6).forEach(m => console.log('  href:', m[1]));
