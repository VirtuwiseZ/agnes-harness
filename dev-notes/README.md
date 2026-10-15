# dev-notes/ — 研发档案与技术备忘目录 (Development Notes & Archives)

> **目录属性**：项目内部研发档案、设计共识、技术备忘与测试留档库  
> **使用原则**：本目录属于开发侧辅助档案，不进入对外发布的 `physics-agent-release` 分支，亦不作为物理智能体运行时的外部依赖。  

---

## 目录架构一览

```
dev-notes/
├── notes-for-ai/        # [核心重点] AI 会话专属知识库、语言风格规范、Prompt 模板与工程避坑备忘
│   ├── README.md        # AI 知识库目录索引与使用指南
│   ├── 通用语言风格与AI提示词指南.md # 双场景通用 Prompt 模板与负向拦截词库
│   ├── 历史核心架构决策与演进备忘.md # 提炼自 1009/1011/1013 庞杂日志的核心设计与问题备忘
│   ├── network_and_vpn_guidelines.md # 代理虚拟网卡开启但关闭覆写DNS的实测结论备忘
│   ├── physics-agent-orchestrator.md # 原生路由器插件设计与子技能按需激活机制
│   ├── commit规范与暂存操作指南.md  # Git 规范与 PowerShell 5.1 纯 ASCII 防乱码铁律
│   ├── AI可自主检索与处理的数据源.md # 公开数据检索指引（Level 1 数据源）
│   ├── 需人工查找与整理的数据源.md   # 受限数据人机协作标准流程
│   └── heatmap推荐数据源.md         # 二维参数场数据接入标准
├── architecture/        # 系统架构设计共识与核心协议基线
│   ├── project_consensus.md # 项目架构演进核心共识文档
│   └── project_consensus_03_report_redesign.md # 双栏交互学术报告重设计共识
├── release-job/         # 面向开源发布的专项工程报告与零侵入性审计档案 (01~08)
├── competition/         # 赛事申报材料、路演讲稿与三类实测样例说明文档
├── self-tests/          # 核心回归测试案例库 (涵盖 01~09 自测用例、仿真脚本与运行资产)
├── reference-solutions/ # 经典参考文献与题目背景材料归档
└── README.md            # 本说明文件
```

---

## 核心维护规范
1. **重点维护 `notes-for-ai/`**：后续参与开发与维护的 AI 智能体，应优先查阅 `notes-for-ai/` 获取核心设计决策与避坑指南；
2. **遵守通用语言风格**：任何新增或修改的内部技术备忘，均须遵循平实务实、简明扼要、不讲黑话、杜绝自吹自擂的标准语言风格；
3. **保持发布分支纯净**：日常开发与演进在 `physics-agent` 分支上进行，提交至 `physics-agent-release` 分支时必须完全排除 `dev-notes/` 目录。
