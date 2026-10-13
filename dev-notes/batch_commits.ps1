# ==============================================================================
# 本地增量 Git Commit 幂等执行脚本（严格不执行 git push，自动跳过无变动批次）
# 依据：dev-notes/commit规范与暂存操作指南.md
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ">>> 正在执行本地提交（自动跳过已提交批次，严格不 push）..." -ForegroundColor Cyan

function Safe-Commit {
    param(
        [string]$BatchName,
        [string[]]$AddPaths,
        [string]$Title,
        [string]$Body
    )
    foreach ($p in $AddPaths) {
        if (Test-Path $p) {
            git add $p 2>$null
        }
    }
    $staged = git diff --cached --name-only
    if ($staged) {
        Write-Host "[$BatchName] 发现待提交文件，正在提交..." -ForegroundColor Green
        git commit -m $Title -m $Body
    } else {
        Write-Host "[$BatchName] 无新增变动或此前已提交，自动跳过。" -ForegroundColor DarkGray
    }
}

# 批次 1: Hooks 与图表引擎
Safe-Commit "批次 1: Hooks" @(
    "physics-agent/hooks/trace_visualizer.py",
    "physics-agent/hooks/make_report_figures.py",
    "physics-agent/hooks/audit_log.py"
) "feat(hooks): 重构物理报告生成器并升级科研图表引擎" "重写 trace_visualizer 支持 Markdown 状态机与离线 LaTeX；升级 make_report_figures 增加防死线门禁与柱状图；加固 audit_log CLI 接口。"

# 批次 2: 质量门禁脚本
Safe-Commit "批次 2: Gates" @(
    "physics-agent/hooks/skill_bom_check.py",
    "physics-agent/hooks/report_quality_check.py"
) "feat(gates): 新增 Skill BOM 自检与报告质量八维自动化门禁脚本" "新增 skill_bom_check 自动扫描修复 BOM 缺陷；新增 report_quality_check 建立 8 维质量门禁。"

# 批次 3: Web 运行时与深链
Safe-Commit "批次 3: Web" @(
    "packages/web-units/src/trace.ts",
    "packages/web/src/theme-boot.ts",
    "packages/web/src/app.ts"
) "feat(web): 打通 AGH 轨迹面板 URL 深度链接与跨标签页零重载切换桥接" "支持通过 URL 参数 ?tab=trace&seq= 自动定位；建立 BroadcastChannel 跨标签页极速通信与 Notification 焦点唤醒。"

# 批次 4: Skills、流水线协议与正式迁移知识库
Safe-Commit "批次 4: Skills 与知识库" @(
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
    "physics-agent/knowledge/reference_data/"
) "feat(skills): 统一物理流水线各 Skill 规范并迁入自包含知识库" "路由器插件注册 1 主 + 8 子 Skill 路由表；将数据源权威指引、网络环境诊断与离线参考基准数据集收拢至 physics-agent/knowledge/，实现路径解耦。"

# 批次 5: 文档、备忘录与开发指引
Safe-Commit "批次 5: 文档与备忘录" @(
    "dev-notes/commit规范与暂存操作指南.md",
    "dev-notes/执行备忘录1013.md",
    "dev-notes/self-tests/06/E3-markdown渲染器选型调研.md",
    "dev-notes/architecture/project_consensus.md",
    "dev-notes/notes-for-ai/network_and_vpn_guidelines.md",
    "dev-notes/第三方数据/物理竞赛与仿真数据源权威指引.md",
    ".gitignore"
) "docs(dev-notes): 建立 Git Commit 规范指南、测试 2-5 缺陷复盘与执行备忘录" "新建 commit 规范指南，确立 A/B/C 三类文件分流；更新执行备忘录，记录 S1-S11 落地成果与就绪假象警示；更新 .gitignore 忽略测试大体积快照。"

# 批次 6: 报告与测试重绘产物
Safe-Commit "批次 6: 报告产物" @(
    "dev-notes/self-tests/06/research_report_jupiter-moon-gravity-assist-decel.html",
    "dev-notes/redraw02-1space_diving.html",
    "dev-notes/redraw03-1sasando.html",
    "dev-notes/redraw03-2artillery.html",
    "dev-notes/redraw05-1jupiter_flyby.html"
) "test(reports): 交付 Test 6 终极双栏交互报告与测试 2-5 原始数据高质量重绘图表" "交付 Test 6 木星引力弹弓双栏交互 HTML 报告；交付测试 02、03-1、03-2、05 四份高质量科研重绘图表 HTML。"

# 批次 7: 修正清单与反馈文档归档
Safe-Commit "批次 7: 修正清单" @(
    "dev-notes/self-tests/06/test6-1修正清单.md",
    "dev-notes/self-tests/06/test6-1开发者反馈.md"
) "docs(test6): 更新 test6-1 修正清单至全部完成并归档开发者反馈" "将 test6-1 修正清单所有待办标记为全部完成；归档 test6 原始开发者反馈文档。"

Write-Host ">>> [完成] 全部待提交改动均已处理完毕！严格未执行 git push。" -ForegroundColor Green
