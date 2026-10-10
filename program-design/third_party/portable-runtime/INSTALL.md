# INSTALL.md — 便携运行时使用说明（Windows，给拿到仓库的用户）

前置：这套目录里的 `python/`（解压好的 embeddable 包）、`wheels/`（烘焙好的全部 21 个 wheel，见
`wheels/LOCKED_VERSIONS.txt`）、`fonts/`（CJK 字体）都已经随仓库带上了，**不需要再联网下载任何东西**，
只需要仓库本身是完整的（没有缺文件的 checkout）。

> 如果你是**开发机**、要在没有预置这套目录的新机器上从头复现一次这套包（比如 CI 上重建），
> 先跑 `node program-design/third_party/portable-runtime/build_wheels.mjs`（需要本机有 Python 3.13.9 + pip，
> 能访问 PyPI），再按下面"从头烘焙"一节走 embeddable 包本体那 4 步；否则直接从"日常使用"一节开始即可。

## 从头烘焙（只在需要重建整套包时才做，本机现在这一步已经做完、随仓库带上了）

1. 下载 `https://www.python.org/ftp/python/3.13.9/python-3.13.9-embed-amd64.zip`，解压到
   `program-design/third_party/portable-runtime/python/`。
2. 打开该目录下 `python313._pth`，把里面 `#import site` 这一行开头的 `#` 去掉（注意实际写法是**小写、无空格**的
   `#import site`，不是大写的 `#Import site`；这一步不做的话 `python.exe -m pip` 装不了任何东西，
   而且 `import` 不到下面烘焙好的第三方包）。
3. 下载 `https://bootstrap.pypa.io/get-pip.py` 放到便携 python 目录旁，跑
   `python\python.exe get-pip.py --target python\Lib\site-packages` 把 pip 本身装好（embeddable 包默认不带 pip）。
4. 跑 `node program-design/third_party/portable-runtime/build_wheels.mjs` 烘焙 wheel（版本号从
   `wheels/LOCKED_VERSIONS.txt` 读，不硬编码），再用下面"日常使用"第 2 步的命令把它们装进便携 python。

## 日常使用（仓库自带的一套已经是烘焙好的状态，直接跳到这两步）

1. **确认 `python313._pth` 里 `#import site` 的 `#` 已经去掉**（仓库自带这一份默认就是改好的，
   如果手动重建过、或者怀疑被谁动过，打开看一眼，没改就手动去掉）。

2. **如果 `python/Lib/site-packages/` 里还没有那些第三方包**（比如新 clone 的仓库，目录结构在但没跑过烘焙），
   一次性装好（离线，不需要联网）：
   ```
   program-design\third_party\portable-runtime\python\python.exe -m pip install --no-deps --target program-design\third_party\portable-runtime\python\Lib\site-packages <wheels 目录下每个 .whl 文件的完整路径，逐个列出，不要用 *.whl 通配符——Windows 下通配符在这个参数位置不会展开>
   ```
   （`--no-deps` 是因为 `LOCKED_VERSIONS.txt` 已经把依赖关系全部展开成扁平清单了，不需要 pip 再去解析一遍依赖树。）

3. **以后跑本项目的 hook 脚本，都用便携 Python 解释器**（不依赖系统装没装 Python，也不受 Windows 商店
   占位符 `python.exe` 干扰）：
   ```
   program-design\third_party\portable-runtime\python\python.exe program-design\hooks\dimensional_gate.py ...
   program-design\third_party\portable-runtime\python\python.exe program-design\hooks\boundary_gate.py ...
   program-design\third_party\portable-runtime\python\python.exe program-design\hooks\audit_log.py ...
   ```
   跑图表（Node 2.7，如果需要）时，`make_report_figures.py` 的 CJK 字体探测（`_configure_cjk_font()`）
   会自动命中 `fonts/MicrosoftYaHei.ttc`，不需要额外装字体。

## 不做的部分（保持默认不动，需要时再手动做）

把这个便携目录加进系统/用户 PATH、替换/覆盖本机已有的其他 Python 安装——这两件事永远是显式询问，
不是默认行为（见 `PORTABLE_RUNTIME.md` 的"伦理边界"一节）。

## 什么时候这套便携包救不了你

需要 MinerU（文档解析 Tier 2，重量级模型依赖，明确排除在本包外）、`ambiance`/`pymsis`
（数据源路由 Level 0 候选包，本包不带）——这两种情况按 SKILL.md §4a / §6 的指引，
停在原地等用户手动安装，不要用便携包硬凑。
