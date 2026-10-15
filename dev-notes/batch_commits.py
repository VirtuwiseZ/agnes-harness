"""
batch_commits.py — 幂等执行本地 Git Commit（严格不 push，自动跳过已提交批次）
依据：dev-notes/commit规范与暂存操作指南.md
"""
import os
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

BATCHES = [
    {
        "name": "批次 1: Hooks 与图表引擎",
        "add": [
            "physics-agent/hooks/trace_visualizer.py",
            "physics-agent/hooks/make_report_figures.py",
            "physics-agent/hooks/audit_log.py",
        ],
        "msg": (
            "feat(hooks): 重构物理报告生成器并升级科研图表引擎\n\n"
            "- 重写 trace_visualizer.py 支持块级 Markdown 状态机、离线自包含 LaTeX 编译器与双栏交互预览；\n"
            "- 升级 make_report_figures.py 增加防死线/防空白门禁、分组柱状图支持与物理阈值参考线；\n"
            "- 加固 audit_log.py CLI 接口，支持直接传递参数自动识别 append 子命令。"
        ),
    },
    {
        "name": "批次 2: 质量门禁脚本",
        "add": [
            "physics-agent/hooks/skill_bom_check.py",
            "physics-agent/hooks/report_quality_check.py",
        ],
        "msg": (
            "feat(gates): 新增 Skill BOM 自检与报告质量八维自动化门禁脚本\n\n"
            "- 新增 skill_bom_check.py 自动扫描并修复 .agh/skills/ 下的 UTF-8 BOM 缺陷；\n"
            "- 新增 report_quality_check.py 建立覆盖元导语拦截、内部黑话过滤、公式图表内联与防死线等 8 维质量门禁。"
        ),
    },
    {
        "name": "批次 3: Web 运行时与深链",
        "add": [
            "packages/web-units/src/trace.ts",
            "packages/web/src/theme-boot.ts",
            "packages/web/src/app.ts",
        ],
        "msg": (
            "feat(web): 打通 AGH 轨迹面板 URL 深度链接与跨标签页零重载切换桥接\n\n"
            "- packages/web-units/src/trace.ts 支持通过 URL 参数 ?tab=trace&seq= 自动打开轨迹视图并滚动定位；\n"
            "- packages/web/src/theme-boot.ts 建立 BroadcastChannel('agnes-trace-jump') 跨标签页极速通信与 Notification 焦点唤醒；\n"
            "- packages/web/src/app.ts 增加跨库会话 ID 回退机制，避免无效会话参数导致页面空白。"
        ),
    },
    {
        "name": "批次 4: Skills、流水线协议与正式迁移知识库",
        "add": [
            "physics-agent/plugins/physics-agent-orchestrator/index.mjs",
            ".agh/skills/physics-agent-governance/SKILL.md",
            ".agh/skills/physics-report-charting/SKILL.md",
            ".agh/skills/physics-report-writing/SKILL.md",
            ".agh/skills/physics-pipeline/SKILL.md",
            ".agh/skills/physics-auditability/SKILL.md",
            "physics-agent/knowledge/report_structure_guide.md",
            "physics-agent/knowledge/path_convention.md",
            "physics-agent/knowledge/物理竞赛与仿真数据源权威指引.md",
            "physics-agent/knowledge/network_and_vpn_guidelines.md",
            "physics-agent/knowledge/reference_data/",
        ],
        "msg": (
            "feat(skills): 统一物理流水线各 Skill 规范并迁入自包含知识库\n\n"
            "- 路由器插件完整注册 1 主 Skill + 8 子 Skill 节点路由表；\n"
            "- physics-report-charting 将 Node 2.7 升级为强制必画规则，增加防死线门禁规范；\n"
            "- physics-pipeline 补入题干物理部件 100% 映射核查与工程速算公式提炼规则；\n"
            "- physics-report-writing 与 report_structure_guide.md 升级为七条行文风格铁律；\n"
            "- 统一 path_convention.md 运行时文件归属规范至 <task-slug>/ 子目录；\n"
            "- 将数据源权威指引、网络环境诊断指南与离线参考基准数据集正式收拢至 physics-agent/knowledge/，实现路径解耦。"
        ),
    },
    {
        "name": "批次 5: 文档、备忘录与开发指引",
        "add": [
            "dev-notes/commit规范与暂存操作指南.md",
            "dev-notes/执行备忘录1013.md",
            "dev-notes/self-tests/06/E3-markdown渲染器选型调研.md",
            "dev-notes/architecture/project_consensus.md",
            "dev-notes/notes-for-ai/network_and_vpn_guidelines.md",
            "dev-notes/第三方数据/物理竞赛与仿真数据源权威指引.md",
            ".gitignore",
        ],
        "msg": (
            "docs(dev-notes): 建立 Git Commit 规范指南、测试 2-5 缺陷复盘与执行备忘录\n\n"
            "- 新建 commit规范与暂存操作指南.md，确立 A/B/C 三类文件分流与 Conventional Commit 规范；\n"
            "- 更新执行备忘录1013.md，记录 S1-S11 落地成果、测试 2-5 缺陷复盘及项目就绪假象警示；\n"
            "- 新建 E3-markdown渲染器选型调研.md，更新 project_consensus.md 与 .gitignore；\n"
            "- 沉淀网络与数据源权威指引开发档案。"
        ),
    },
    {
        "name": "批次 6: 报告与测试重绘产物",
        "add": [
            "dev-notes/self-tests/06/research_report_jupiter-moon-gravity-assist-decel.html",
            "dev-notes/redraw02-1space_diving.html",
            "dev-notes/redraw03-1sasando.html",
            "dev-notes/redraw03-2artillery.html",
            "dev-notes/redraw05-1jupiter_flyby.html",
        ],
        "msg": (
            "test(reports): 交付 Test 6 终极双栏交互报告与测试 2-5 原始数据高质量重绘图表\n\n"
            "- 交付 Test 6 木星引力弹弓双栏交互 HTML 报告（含离线 LaTeX、两张矢量图表、真实轨迹面板与返回按钮）；\n"
            "- 交付测试 02（高空跳伞）、03-1（Sasando）、03-2（火炮外弹道）、05（木星弹弓对数衰减）四份高质量科研重绘图表 HTML。"
        ),
    },
    {
        "name": "批次 7: 修正清单与反馈文档归档",
        "add": [
            "dev-notes/self-tests/06/test6-1修正清单.md",
            "dev-notes/self-tests/06/test6-1开发者反馈.md",
        ],
        "msg": (
            "docs(test6): 更新 test6-1 修正清单至全部完成并归档开发者反馈\n\n"
            "- 将 test6-1 修正清单所有待办标记为全部完成；\n"
            "- 归档 test6 原始开发者反馈文档。"
        ),
    },
]


def run_cmd(cmd):
    res = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, encoding="utf-8")
    return res.returncode, res.stdout.strip(), res.stderr.strip()


def main():
    print(f">>> 目标仓库目录: {REPO_ROOT}")
    print(">>> 开始执行本地提交（自动检测变动，已提交批次自动跳过，严格不 push）...\n")

    for i, b in enumerate(BATCHES, 1):
        # 1. 尝试添加现有文件
        existing_files = [f for f in b["add"] if os.path.exists(os.path.join(REPO_ROOT, f))]
        if existing_files:
            run_cmd(["git", "add"] + existing_files)
        # 2. 检查暂存区是否有该批次的变动
        rc, out, _ = run_cmd(["git", "diff", "--cached", "--name-only"])
        if out:
            print(f"[{i}/7 {b['name']}] 发现新增改动，正在提交...")
            rc, commit_out, err = run_cmd(["git", "commit", "-m", b["msg"]])
            if rc == 0:
                print(f"  ✓ 提交成功")
            else:
                print(f"  ✕ 提交失败: {err or commit_out}")
        else:
            print(f"[{i}/7 {b['name']}] 无新增变动或此前已提交，自动跳过。")

    print("\n>>> [完成] 全部待提交改动均已处理完毕！严格未执行 git push。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
