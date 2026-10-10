// 用便携 Python 逐个 import LOCKED_VERSIONS.txt 里列的每个顶层包，输出实际版本号，
// 用来做最终校验（不依赖本机系统 Python）。
const { execSync } = require('node:child_process');
const fs = require('node:fs');

const pyExe = 'program-design/third_party/portable-runtime/python/python.exe';
const lockTxt = fs.readFileSync('program-design/third_party/portable-runtime/wheels/LOCKED_VERSIONS.txt', 'utf8');
const pips = {};
lockTxt.split('\n').forEach(line => {
  const clean = line.split('#')[0].trim();
  const m = clean.match(/^([A-Za-z0-9_-]+)==(.+)$/);
  if (m) pips[m[1]] = m[2].replace(/\.post[0-9]*$/, '');
});
// name -> [import 名, 取版本的方式]
// 'metadata' 表示这个包没有运行时版本属性，用 importlib.metadata 查
const checks = [
  ['sympy','sympy','__version__'],
  ['pint','pint','__version__'],
  ['numpy','numpy','__version__'],
  ['scipy','scipy','__version__'],
  ['matplotlib','matplotlib','__version__'],
  ['plotly','plotly','__version__'],
  ['mpmath','mpmath','__version__'],
  ['flexparser','flexparser','__version__'],
  ['platformdirs','platformdirs','__version__'],
  ['typing-extensions','typing_extensions','metadata'],
  ['contourpy','contourpy','__version__'],
  ['cycler','cycler','__version__'],
  ['fonttools','fontTools','__version__'],
  ['kiwisolver','kiwisolver','__version__'],
  ['packaging','packaging','__version__'],
  ['pillow','PIL','__version__'],
  ['pyparsing','pyparsing','__version__'],
  ['python-dateutil','dateutil','__version__'],
  ['narwhals','narwhals','__version__'],
];
let allOk = true;
for (const [name, mod, verAttr] of checks) {
  const want = pips[name];
  let script;
  if (verAttr === 'metadata') {
    script = `import importlib.metadata as md; print(md.version('${name.replace(/[-]/g,'_')}'))`;
  } else {
    script = `import ${mod}; print(getattr(${mod},'${verAttr}','?'))`;
  }
  try {
    let out = execSync(`"${pyExe}" -c "${script}"`, { encoding: 'utf8' }).trim();
    out = out.replace(/\.post[0-9]*$/, ''); // 构建后缀不算版本失配
    const ok = out === want;
    if (!ok) allOk = false;
    console.log(`${ok?'✓':'✗'} ${name}==${want} (实际 ${out})`);
  } catch (e) {
    allOk = false;
    console.log(`✗ ${name}==${want}  import 失败: ${e.message.split('\n')[0]}`);
  }
}
console.log(allOk ? '\n全部匹配 ✓' : '\n有失配 ✗');
process.exit(allOk ? 0 : 1);
