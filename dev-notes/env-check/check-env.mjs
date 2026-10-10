#!/usr/bin/env node
// AGH 宿主 + 本项目 hooks 的环境检查脚本
// 用法：从仓库根目录运行
//   node dev-notes/env-check/check-env.mjs
// 作用：一次性检查"跑 AGH 宿主 + 跑本项目 Python hooks"两条链路各自需要的
// 运行时是否装好、版本是否满足本项目实际验证过的版本（不是最低版本号，
// 是 dev-notes/self-tests/ 实际跑通过的那份版本清单，见
// dev-notes/self-tests/00-meta/self-test-index.md §3 固定事实块）。
// 本脚本自身是 Node 脚本（不是 .py），跟开发者原文"不能是.py"这条约束一致：
// 检查"Python 装没装"这件事本身不需要 Python 参与，靠 Node 的 child_process
// 去探测就行，不产生"检查工具本身依赖被检查对象"的循环依赖。
'use strict';
import { execSync } from 'node:child_process';

// ---- 探测工具（失败不抛异常，返回 null 表示"没装"）----
function probe(cmd, args = []) {
  try {
    const out = execSync(`${cmd} ${args.join(' ')}`, {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
      // Windows 下不 shell out（避免 PowerShell 对版本输出混入提示行，
      // 见 dev-notes/项目架构审视1009.md 3.3 本轮执行记录里 2404 错误那次排查）。
      shell: process.platform === 'win32' ? false : true,
    });
    return out.toString().trim();
  } catch {
    return null;
  }
}

// ---- 解析版本号（形如 "v24.21.0" / "Python 3.13.9" / "10.34.5"）----
function parseVersion(raw) {
  if (raw == null) return null;
  const m = raw.match(/(\d+)\.(\d+)\.(\d+)/);
  if (!m) return null;
  return { major: Number(m[1]), minor: Number(m[2]), patch: Number(m[3]) };
}
function isGte(v, [maj, min, pat]) {
  if (v == null) return false;
  if (v.major !== maj) return v.major > maj;
  if (v.minor !== min) return v.minor > min;
  return v.patch >= pat;
}

// ---- 跟 dev-notes/self-tests/00-meta/self-test-index.md §3 固定事实块对齐的
//     版本下限（实际是"这份清单在哪个版本上跑通过"，不是理论最低版本）----
const BUNDLED = {
  node:  { name: 'Node.js', min: [24, 21, 0], probe: () => process.version, installHint: 'https://nodejs.org/ （选 LTS，验证过的版本是 24.21.0）' },
  pnpm:  { name: 'pnpm',    min: [10, 34, 5], probe: () => probe('pnpm', ['--version']), installHint: 'npm install -g pnpm' },
};

// ---- Python 探测：区分"真安装"和 Windows Store 占位符 ----
// Windows 上"装了商店版 Python 但没装真 Python"是常见坑：
// `Get-Command python` 会返回 `C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\python.exe`
// （这个文件是一个 App Installer 占位符，双击会跳商店页面，从命令行调用可能
// 能"跑"但行为不可靠，且不代表真安装）。本脚本靠路径特征判断，不依赖
// Python 本身参与判断（避免循环依赖）。
function probePythonReal() {
  const raw = probe('python', ['--version']) || probe('python3', ['--version']);
  if (raw == null) return { ver: null, isStoreStub: false, raw: null };
  // 用 where.exe 拿到 python 实际指向的路径（Windows only；非 Windows 直接跳过这项判断）。
  // 判定规则：`where` 输出的第一行必须是真实安装目录，且路径中不含 WindowsApps
  // （WindowsApps 是商店版占位符，双击会跳商店页面，从命令行调用行为不可靠，
  //  不代表真安装）。后续行里出现 WindowsApps 不影响判定——只要第一行是真实安装
  //  即可（Windows 环境常见"真 Python + 商店占位符"并存的情况，占位符被真安装
  //  排在前面时不算问题）。若第一行落在 WindowsApps，说明 PATH 里没有任何真
  //  安装排在它前面，等价于"没装官方 Python"，判为占位符。
  let isStoreStub = false;
  if (process.platform === 'win32') {
    const whereOut = probe('where.exe', ['python']);
    const firstLine = whereOut ? whereOut.split(/\r?\n/)[0] : null;
    if (firstLine && /WindowsApps/i.test(firstLine)) {
      isStoreStub = true;
    }
  }
  const ver = parseVersion(raw);
  return { ver, isStoreStub, raw };
}

const PYTHON = {
  name: 'Python', min: [3, 13, 9],
  installHint: 'https://www.python.org/downloads/ （注意安装时勾选 "Add Python to PATH"；本项目锁定版本是 3.13.9，见 program-design/third_party/portable-runtime/PORTABLE_RUNTIME.md）',
};

function check(item, label, customProbe) {
  let raw, ver, isStoreStub = false;
  if (customProbe) {
    const r = customProbe();
    raw = r.raw; ver = r.ver; isStoreStub = r.isStoreStub;
  } else {
    raw = item.probe();
    ver = parseVersion(raw);
  }
  const shown = raw == null ? '未找到' : raw;
  const ok = isGte(ver, item.min) && !isStoreStub;
  const want = `>= ${item.min.join('.')}（验证版本）`;
  let extra = '';
  if (isStoreStub) extra = '（检测到 WindowsApps 占位符路径，这是商店版，不是真安装，需要装官方 Python）';
  return {
    label,
    name: item.name,
    shown: shown + extra,
    ok,
    line: ok ? `✓  ${label}：${shown}` : `✗  ${label}：${shown}${extra}，需要 ${want}`,
    hint: ok ? null : `  安装：${item.installHint}`,
  };
}

const pyInfo = probePythonReal();
const results = [
  check(BUNDLED.node,  'AGH 宿主运行'),
  check(BUNDLED.pnpm,  'AGH 宿主依赖安装（pnpm install）'),
  check(PYTHON,        '本项目 Python hooks 运行（dev-notes/self-tests 实际跑通的那一版）', probePythonReal),
];

console.log('AGH 宿主 + 本项目 hooks 环境检查（dev-notes/env-check/check-env.mjs）');
console.log('────────────────────────────────────────────────────────');
let allOk = true;
for (const r of results) {
  console.log(r.line);
  if (r.hint) { console.log(r.hint); allOk = false; }
}
console.log('────────────────────────────────────────────────────────');
console.log(allOk ? '全部通过，可以运行 AGH 宿主和 dev-notes/self-tests 验收脚本。'
  : '有未通过项，按上面的安装提示装好后再跑一次本脚本。');
process.exit(allOk ? 0 : 1);
