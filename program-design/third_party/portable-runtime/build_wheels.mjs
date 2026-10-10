#!/usr/bin/env node
// 从本机（开发机/已装好 Python 环境的那台）烘焙 wheel 文件到
// program-design/third_party/portable-runtime/wheels/，
// 供便携运行时离线安装使用。本机需要装好 Python 3.13.9 + pip。
// 用法（从仓库根目录）：
//   node program-design/third_party/portable-runtime/build_wheels.mjs
// 版本号以 wheels/LOCKED_VERSIONS.txt 为唯一事实来源，改版本只改那里。
'use strict';
import { execSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// 锁定版本从 wheels/LOCKED_VERSIONS.txt 读取（只认 "name==version" 这种行格式，
// 忽略注释行/空行/依赖说明行），避免在脚本里再硬编码一份版本清单。
const here = dirname(fileURLToPath(import.meta.url));
const lockPath = resolve(here, 'wheels', 'LOCKED_VERSIONS.txt');
const Pinned = {};
readFileSync(lockPath, 'utf8').split('\n').forEach(line => {
  const m = line.match(/^([A-Za-z0-9_\-]+)==([0-9][^\s]*)\s*$/);
  if (m) Pinned[m[1]] = m[2];
});
if (Object.keys(Pinned).length === 0) {
  console.error('LOCKED_VERSIONS.txt 里没有解析到任何 name==version 行，请检查文件格式。');
  process.exit(1);
}

const target = resolve(here, 'wheels');
if (!existsSync(target)) {
  mkdirSync(target, { recursive: true });
}
execSync(`python -m pip download ${Object.entries(Pinned).map(([n, v]) => `${n}==${v}`).join(' ')} --dest ${target} --no-deps`, {
  stdio: 'inherit',
  shell: process.platform === 'win32' ? false : true,
});

console.log('烘焙完成，wheel 文件在：', target);
console.log('下一步（embeddable 包本体）：');
console.log('  ① 下载 https://www.python.org/ftp/python/3.13.9/python-3.13.9-embed-amd64.zip');
console.log('     解压到 program-design/third_party/portable-runtime/python/');
console.log('  ② 打开该目录下 python313._pth，把 "#import site" 的 # 去掉（注意是小写、无空格）');
console.log('  ③ 下载 https://bootstrap.pypa.io/get-pip.py 放到便携 python 目录旁，');
console.log('     跑 python/python.exe get-pip.py --target python/Lib/site-packages 装好 pip');
console.log('  ④ 跑 INSTALL.md 里的离线安装步骤，把上面烘焙好的 wheel 装进便携 python。');
