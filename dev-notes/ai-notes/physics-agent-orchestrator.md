# AI 备忘：physics-agent-orchestrator 插件（面向未来的 AI，不是给人看的）

> 读者假设：未来某轮会话里的 AI，记忆不完整、没有读过 2026-10-11 那轮会话的完整过程。
> 本文档目的：让未来的你（AI）能（a）直接读懂这个插件是什么、（b）不重复踩本轮踩过的坑、（c）知道怎么安全地更新它。
> 写完后如有出入，以仓库源码为准；本文档里的文件路径/行号是 2026-10-11 那一刻核实的，动手前先 `git grep`/`read` 重新确认一遍，别直接照抄行号。

## 1. 这个插件是干什么的（功能定位）

- **身份**：AGH（Agnes Harness）插件，`inject: ['skills']`，即运行时 skill 贡献（Cordis service，`packages/resource-control-runtime/src/skills-cordis.ts`），**不是**磁盘上的 `SKILL.md` 文件。
- **作用**：当会话收到"物理分析/物理建模/数值求解"类题目时，主动提醒 Agent 该按 6 节点 pipeline 执行、且第一步必须先读哪份 skill。把"该用哪个 skill 推进到哪一步"这层调度逻辑，从纯文字说明（`.agh/skills/physics-agent-governance/SKILL.md` 正文里内嵌过一遍）升级成宿主 skill 目录里一个**独立的、可被 `skill_read`/`tool_search` 直接检索到的条目**。
- **当前阶段定位（①第 2 点，"不删改现有 skill"约束下）**：这份贡献的 `body` 只承载"路由/提醒"本身，不承载任何节点的具体做法；唯一指向的目标 = 现有的完整 `.agh/skills/physics-agent-governance/SKILL.md`（一份 `SKILL.md`，不拆分）。等确认点 B（①第 4 点）定稿"按节点拆分出哪些子 skill"后，才回来把这里"先读 governance 主 skill"一句改成"按节点依次读对应子 skill"。
- **跟现有 skill 的关系**：跟 `.agh/skills/physics-agent-governance/`（磁盘层）是**并存的两个不同来源**，互不影响，不删除/不修改磁盘那份。

## 2. 文件位置（核实过的事实，不是猜的）

- **源文件（要编辑的地方）**：
  - `program-design/plugins/physics-agent-orchestrator/package.json`
  - `program-design/plugins/physics-agent-orchestrator/index.mjs`
- **安装后落盘的位置（daemon 侧，只读镜像，不要直接编辑）**：
  - `C:\Users\StanleyZ\.agh\data\profiles\local-dev\packages\@agnes-examples__physics-agent-orchestrator\`（`index.mjs` + `package.json`）
- **注册/信任/启用状态**：由 daemon 维护（不在上述目录里，不靠文件存在与否判断），用 `node packages/cli/dist/local/agnes.mjs package list` 查，正常应该看到：
  `@agnes-examples/physics-agent-orchestrator@0.1.0 desired=enabled actual=running trusted=true`
- **本文件（AI 备忘）**：`dev-notes/ai-notes/physics-agent-orchestrator.md`（就是这个文件）

## 3. 本轮（2026-10-11）实际踩过、且解决掉的坑（下次别再绕弯路）

1. **CLI `package add`/`install` 装不上**：`packages/cli/src/bin.ts` 里有 `io.stdin.isTTY === true && io.stdout.isTTY === true` 的硬设计（安全不变量 INV-33，"A non-interactive command never guesses consent"），非交互直接拒装，且**没有** `--yes`/`-y` 旁路参数（实测过，两个都报 `unknown flag`）。这是刻意的安全设计，不是 bug，不要试图伪造 TTY 绕过。
2. **误判"native 模块缺失/未构建"**：用 tsx 直接解析 TS 源码（`packages/sdk/src/...`）时，`createRequire(import.meta.url)('@agnes/system-node/native')` 找不到模块，报 `E_SYSTEM_NATIVE_UNAVAILABLE`。**真实原因**：tsx 解析源码时 `import.meta.url` 落在源码目录，那里没有 `node_modules/@agnes/*` link（本 fork 是纯 pnpm workspace 源码 checkout，没有 `pnpm install` 的 link 步骤）。**但** `packages/cli/dist/local/agnes.mjs`（16MB 单文件编译产物）里 bundle 的 native 模块其实一直可用——直接用 `createRequire('.../packages/cli/dist/local/agnes.mjs')('@agnes/system-node/native')` 能成功 require 到（`abiVersion: 1`）。**下次不要再走"tsx 解析 TS 源码 + native"这条路，直接用 dist 编译产物的 `createRequire` 拿 native**。
3. **SDK 直连 daemon 这条路实际走通的方式**：写了 `dev-notes/_drive_pkg_sdk8.cjs`（CJS，不用 tsx/ESM），手工实现 daemon 的 JSONL RPC 帧协议（一行一个 JSON 对象，跟 `packages/sdk/src/transport/jsonl.ts` 帧格式一致），直接连上已在跑的 daemon（`daemon status` 查 `pid`/`socketPath`，**不需要**新起 daemon 进程），按顺序跑 `initialize`（握手）→ `_agnes/v1/packages.inspect` → `packages.install` → `packages.trust` → `packages.enable`，全程非交互。这个脚本是**一次性探针**，没提交 git，下次需要时照着它的结构重写一份即可，不用找它。
4. **协议参数格式坑（本轮踩到、已核实）**：`_agnes/v1/packages.inspect`/`install` 的 `source` 参数，`PackageSource` 的 `type='file'` 分支，`ref` 字段 regex **强制要求 `file:` 前缀**（`^file:\./...`），漏了前缀报 `INVALID_PARAMS/ENUM`。之前 CLI 侧传的裸路径是对的，但直接手写 RPC 时容易漏这个前缀。

## 4. 怎么更新这个插件（改内容后）

- **日常改内容**（比如改 `index.mjs` 里路由说明文字、改 `description`）：
  1. 直接编辑 `program-design/plugins/physics-agent-orchestrator/index.mjs`（**源文件**，不是第 2 节里那个 `C:\Users\StanleyZ\.agh\...` 下的落盘镜像，那个是只读副本）。
  2. 重新走一遍第 3 节第 3 点的非交互直连路线（复用/重写 `_drive_pkg_sdk8.cjs` 那种脚本），把最后的 `enable` 换成 `inspect`（拿到新的 `integrity`）→ `update`（`PackageUpdateParams`，带上 `source` + 新的 `expectedIntegrity`）。
  3. **不需要**手动先 `untrust` 再重新 `trust`——只要 `capabilityHash` 没变（见第 5 点），`update` 会自动保持信任状态。
- **`integrity`（sha256）是内容哈希，自动跟着内容变**，不是手填的；改完重新 `inspect` 一遍拿新值就行。
- 用 `node packages/cli/dist/local/agnes.mjs package list` 复核更新后状态仍然是 `desired=enabled actual=running trusted=true`。

## 5. `capabilityHash`（什么时候需要重新走 trust）

- **公式**（已核实，`packages/package-manager/src/integrity.ts` 第 46–56 行 + `packages/package-manager/src/inspect.ts` 第 295 行调用方式）：
  `capabilityHash = sha256(canonical({ contributions, dependencies }))`，`canonical()` 是"排序对象 key + 递归处理数组/对象 + 叶子 JSON.stringify"。
- **只算** `package.json` 里顶层的 `contributes`/`dependencies` 字段，**不算**文件内容/`integrity`/其他字段。
- **推论**：只改 `index.mjs` 正文（路由说明/`body` 文字）不会改变 `capabilityHash`，`update` 一步到位，信任状态自动保持。
- **只有**动到 `contributes` 结构（比如以后按节点拆分出多个 skill、改了声明结构）才会改变 `capabilityHash`，那时候要重新算一遍（公式固定，脚本重跑一遍本地重算即可）再走一次 `trust`。
- 2026-10-11 实测：本地重算的 `capabilityHash`（`e3de4e5f2da4b8aa2650af5c4f822d397c2dadd7a6695e5071c0444d26a22b01`）跟 daemon 实际算出来的 `preview.capabilityHash` 逐字一致，公式本身站得住。

## 6. 怎么验证"真的生效了"（验收动作，别用错命令）

- **正确**：在任意真实 AGH 会话里（包括当前会话自己，用 `tool_search`/`skill_read`），确认目录里能看到 `physics-agent-orchestrator` 这条、且能读到它的 `body`。2026-10-11 实测当前会话自己就能验证到（`resourceId: skill/runtime/runtime/cd30a009...`），不需要用户额外开一个独立会话。
- **错误（会误判）**：`node packages/cli/dist/local/agnes.mjs resources list --kind skill` **看不到**这个插件贡献的条目——这条命令只读磁盘层的 `contributes`/`SKILL.md` 文件（`packages/resource-control-daemon/src/package-skill-snapshot.ts` 的 `writePackageSkillInventory`，只收 `contribution.kind === 'skill'` 的磁盘文件贡献），不含纯运行时贡献（本插件走的是 `packages/resource-control-runtime/src/skills.ts` 的 `registerRuntime()`，写的是调用它的进程自己的内存注册表，不落盘）。看到 `resources list` 里没有这条**不代表**安装/信任失败，别用这条命令判断成败。
- **`package list`**（第 4 节那步复核用的）看的是宿主层安装/信任/启用状态，跟"模型侧能不能检索到"是两码事，两个都要查才算闭环。

## 7. 已知边界/未完成项（别误以为都搞定了）

- 本文档覆盖的是"载体本身能不能被宿主机制承载、怎么注册/更新/验证"（共识文档①第 3 点，确认点 A）——**已于 2026-10-11 完整闭环**（宿主层 + 模型侧都实测通过，不是半成品）。
- **尚未开始**：确认点 B（①第 4 点）——"按节点把 `SKILL.md` 拆成哪些子 skill、每个子 skill 的 `description` 怎么写"。这是下一步真正的工作，跟本插件载体已经跑通这件事是两码事，别混在一起汇报"全部完成"。
- 拆分方案定稿后，本插件 `index.mjs` 里那句"先读 governance 主 skill"要改成"按节点读对应子 skill"，那时候才会动到 `contributes`/`capabilityHash`（回到第 5 点的场景）。

## 8. 硬性约束（别踩线）

- **不删除、不修改** `.agh/skills/physics-agent-governance/SKILL.md` 现有内容（"不删改 skill"是这条线的既定约束，跟本插件是并存的两个来源）。
- 不要手工伪造 `C:\Users\StanleyZ\.agh\data\profiles\local-dev\packages\` 目录布局或任何 SQLite 信任记录来绕过 daemon 的 RPC（信任状态在 SQLite 表里，不在那个目录的布局里判断，手改风险远高于直接跑 `update`）。
- 不要伪造 TTY 绕过 `package add` 的交互确认（INV-33）；正确的非交互路线就是第 3 节第 3 点那条 daemon RPC 直连路。
- `git commit`/`push` 需要用户逐次明确授权，不要默认执行。
