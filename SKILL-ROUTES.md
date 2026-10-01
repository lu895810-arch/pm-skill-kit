# cyx 技能路由表

**用途**：`cyx-*` 技能已超过 26 个，其中需求类 8 个、分析类 2 个、部署类 2 个，名称相似度高，光看名字分不出该走哪个。本表处理的就是这件事——**先定产出物，再定落点**。

**怎么用**：技能自身 frontmatter 的 `description` 仍是第一触发依据；本表只在「几个技能的描述看起来都沾边、拿不准走哪个」时查。查法：从第一节找到你要产出的东西，再看「判据」列确认边界。

**维护**：新增、改名、降级触发等级后，同步改本表，并按 `cyx-skill-evolution` 3.4 的五处收口走一遍。

---

## 一、需求与产品规划（最密的一族，先看这里）

这一族八个技能最容易撞。判据不是「谁的名字更像」，而是**产出物的落点**：是「要做成什么」还是「先做哪个」还是「为什么长成这样」。

| 你要产出什么 | 走哪个 | 判据 / 边界 |
|---|---|---|
| 一份能看、能讲、能填的**功能需求文档**（每条带模块编号、P0~P2、验收要点） | `cyx-summary-need` | **默认入口**。只说「写 PRD / 梳理需求 / 需求文档 / 列功能点」时走这里，轻量版 |
| **工程级 PRD**：EARS 六段式需求条目、十章骨架、编号台账（D-xx / B-x / R1） | `cyx-ears-need` | **必须用户显式点名才加载**，不自动触发。点名说法：「用 cyx-ears-need」「按 EARS 六段式写」「十章 PRD」 |
| 给定**一批需求 + 一个版本目标**，逐条判 P0/P1/P2/P3，给依据、RICE 打分与风险 | `cyx-priority-need` | 只做**判定与排序**。需求本身从哪来、怎么写，不归它 |
| **《产品功能规划》**：四层架构、模块功能清单、优先级矩阵、MVP 范围、分阶段路线图 | `cyx-strcuture-need` | 落点是**规划架构**（分层 / 模块 / 路线图），不写需求条目 |
| 单产品**「为什么长成现在这样」** + 现存需求缺口 | `cyx-original-need-md`（主文档，手法以它为准） → `cyx-original-need-html`（渲染成 HTML） | 产出是**上游输入稿**：演进成因与缺口池。先 md 定内容，再交 html 渲染 |
| **从 0 到 1 定义一款新产品**（JTBD、价值主张画布、北极星指标、TAM/SAM/SOM） | `ai-product-methodology` | 产品还不存在时用它；已经存在的产品不走 |
| **两款产品横向对比**，把 A 的优势逐条写成微需求 + 验收标准，附 B 反超清单 | `cyx-compare-code-micro-demand` | 落点是**单条需求 + 可勾选验收标准** |
| **两个项目宏观对比**：定位、用户人群与场景、能力成熟度、选型建议 | `cyx-compare-macro-demand` | 落点是**选型结论**，不落到单条需求 |

**一句话判据**：

```
要做什么（轻）   → cyx-summary-need
要做什么（重）   → cyx-ears-need（点名才上）
先做哪个         → cyx-priority-need
怎么分层规划     → cyx-strcuture-need
为什么长成这样   → cyx-original-need-md / -html
从零定义产品     → ai-product-methodology
对手哪里强、抄成需求 → cyx-compare-code-micro-demand
选谁             → cyx-compare-macro-demand
```

**最容易选错的三对**：

- `cyx-summary-need` × `cyx-ears-need`：同一件事的轻重两档。判据是**用户有没有点名重装章法**，没点名一律走 summary-need。
- `cyx-strcuture-need` × `cyx-summary-need`：strcuture 产出「架构怎么分层、模块有哪些、路线图怎么排」；summary 产出「每条需求写成什么」。前者是骨，后者是肉。
- `cyx-original-need-*` × `cyx-summary-need`：original 回答「过去为什么这样」，是**上游输入稿**；summary 回答「接下来做什么」。顺序上 original 在前。

---

## 二、分析类

| 你要产出什么 | 走哪个 | 判据 / 边界 |
|---|---|---|
| **本地文件夹**（桌面软件、未上线工程、解压即用分发包）的「产品 × 技术」双视角分析报告 | `cyx-folder-analysis` | 起点是**本地路径** |
| **GitHub 开源项目**的「产品 × 技术」双视角分析报告 | `cyx-github-analysis` | 起点是**仓库链接** |
| **一批同类项 GitHub 仓库**的横向盘点（逐个核验元数据，按业务链路排序，单文件 HTML 报告） | `cyx-multi-project-analysis` | 起点是**仓库清单**（≥3 个，构成一条生产/使用链）；不深读单仓实现，只核元数据并按流水线组织 |
| GitHub 上某个方向的**开源生态调研**：可复用组件、类似产品、关键词矩阵、授权建议 | `cyx-github-search` | 不是分析某一个仓库，是**扫一片**找选型 |

判据一句话：**分析一个本地工程 → folder-analysis｜分析一个仓库（深读） → github-analysis｜盘点一批同类项（横读） → multi-project-analysis｜扫一片找组件 → search-github**。

---

## 三、运行与部署类

| 你要产出什么 | 走哪个 | 判据 / 边界 |
|---|---|---|
| 从**仓库链接**到**第一次真跑通**（含核心业务动作冒烟） | `cyx-github-deploy` | 起点是链接，终点是「写操作真跑成功」 |
| **本地已有文件夹**跑不起来，系统性排查原因 | `cyx-folder-deploy` | 起点是本地目录，终点是定位到「为什么起不来」 |
| 把本地技能目录或任意文件树**推送到 GitHub**（本机无凭据助手 → 用 PAT 一次推送） | `cyx-git-push` | 只管推送这一步 |

判据一句话：**起点是链接 → github-deploy｜起点是本地目录 → folder-deploy｜只推代码 → git-push**。
两个 deploy 之间有接力：github-deploy 验证失败时转入 folder-deploy 的排查链路。

---

## 四、课件类

| 你要产出什么 | 走哪个 | 判据 / 边界 |
|---|---|---|
| **锁总时长**的课堂课件（全时长版 + 快线双轨、游戏化晋升） | `cyx-course-html` | 时长轨制。用户说「XX 分钟课堂版」「双轨快线」「讲台版 + 备课版」 |
| **不锁时长、按章节推进**的简版课件 + **A4 可打印学案**（双轨交付） | `cyx-brief-course` | 章节制。用户说「简版课件」「图为主字极简」「配套学生学案」 |

判据一句话：**内容骨架是不是章节制**——每章以一件产物收尾、且该产物被后面的章节接着用。是 → brief-course；否则 → course-html。
两套模板的 CSS 不通用（互缺对方的类），别混着抄。

---

## 五、短剧创作链（有上下游顺序，按链走）

```
大纲  →  剧本  →  分镜
  │        │        │
  │        │        └─ 段 → 分镜 → 分镜图，每段一条视频提示词
  │        └─ 场次 + 节拍流，逐句带说话人与语气
  └─ 改编说明 / 人物表 / 爽点表 / 分集梗概 / 资产清单

并行资产线：角色设定 · 美术设定（随大纲走，供分镜取参考图）
```

| 链条位置 | 走哪个 | 产出物 / 边界 |
|---|---|---|
| 第 1 环 · 大纲 | `cyx-shuohao-outline` | 小说改编成短剧大纲五件套，产出 `outline.json` |
| 第 2 环 · 剧本 | `cyx-shuohao-script` | 分集梗概落成场次 + 节拍流。**不分镜头、无镜号、不写生成提示词** |
| 第 3 环 · 分镜 | `cyx-shuohao-storyboard` | 段 → 分镜 → 分镜图，每段配一条视频提示词 |
| 并行资产 · 角色 | `cyx-shuohao-characters` | 角色表、人物画像、形象与音色提示词、角色设定图 |
| 并行资产 · 美术 | `cyx-shuohao-art` | 场景 + 叙事道具设定集，跨集一致性锚点 |

两条纪律：**剧本管戏、分镜管拍**，别在第 2 环写生成提示词；**上游产物是下游输入**（`outline.json` seed 预填脚本与美术），顺序不能倒。

---

## 六、调研与写作类

| 你要产出什么 | 走哪个 | 判据 / 边界 |
|---|---|---|
| **市场 / 行业调研报告**：数据来源标注、可信级标签、口径边界 | `cyx-research-report` | 落点是行业格局、市场规模、赛道评估 |
| ├ 视觉侧规范（暗色科技风配色与组件、去 AI 味禁词） | `cyx-research-report/cyx-html-style` | 任何 HTML 产出都可引用，不限调研报告 |
| └ Markdown 报告写作规范（五段式骨架、编号口径、来源三级标注） | `cyx-research-report/cyx-md-style` | 以 Markdown 为事实源时引用 |
| 从抖音视频页面提取完整内容（标题、正文要点、评论、标签） | `cyx-douyin-extract` | 抖音是 SSR 空壳，别用 WebFetch 硬试 |

注：`cyx-html-style` 与 `cyx-md-style` 是 `cyx-research-report` 包内的**子技能**，路径在 `cyx-research-report/` 目录下，不是顶层技能。

---

## 七、文档治理与工程杂项

| 你要产出什么 | 走哪个 | 判据 / 边界 |
|---|---|---|
| 文档产出前的**分区与精简归档**：素材备份区 + 本次产出区两段式、`更N-` 命名、控制文件数量 | `cyx-doc-separate` | 只要这项工作会有文档产出就该触发，不必用户提「分区」二字 |
| 把**界面截图里的 bug / 体验问题**整理成可持续迭代的 **Excel 问题台账**（三表：明细 + 统计图表 + 截图证据页），支持多轮追加 / 删除 / 排序 / 图表美化 | `cyx-bug-demand` | 材料是**截图 + 一句话反馈**，落点是**问题台账**（现状缺陷 + 修复建议）；要写「要做什么 + 验收标准」的需求条目则回需求族 |
| 把**派生文档**（讲课稿 / 大纲 / 学案 / 旧副本）对齐到**内容基准**的口径与事实 | `cyx-doc-align-baseline` | 保留原文体例，只同步页码 / 编号 / 术语 / 跨页引用 |
| 技能**自我进化母版**：判定「通用还是个案」、往哪本账本写 | `cyx-skill-evolution` | 任何 cyx 技能被使用后的反馈处理，都先过它 |

判据一句话：**产出前先分区 → doc-separate｜已有文档对口径 → doc-align-baseline｜改技能本身 → skill-evolution**。

---

## 八、邻居技能（非 `cyx-` 前缀，但常一起出现）

| 技能 | 什么时候用 |
|---|---|
| `ai-product-methodology` | 从 0 到 1 定义新产品，产出产品定义画布 |
| `ai-course-md-to-html` / `course-html-to-md` | 课件 Markdown 与 HTML 之间的格式互转 |
| `buddy-diagram-design` | 要画任何图（41 类），暗色优先，优先用这个而不是重造 |
| `deck-*`（40 余个） | 做 PPT / 演示稿时按风格选，属模板库，不纳入 cyx 方法论体系 |
| `pdf` / `pptx` / `docx` / `xlsx` | 格式读写工具，非方法论技能 |

---

## 九、当前需要治理的问题

按影响程度排：

1. **`cyx-strcuture-need` 是拼写错误**——`strcuture` 应为 `structure`。建议改名为 `cyx-structure-need`。
   影响面 5 个文件：本技能 `SKILL.md` + `references/structure-playbook.md` + `references/feedback-log.md`，以及交叉引用它的 `cyx-priority-need/SKILL.md`、`cyx-compare-code-micro-demand/SKILL.md`。改名前需按 `cyx-skill-evolution` 3.4 的五处收口执行。
2. **需求类八个技能的名称不含层次信息**——全是 `*-need` / `*-demand`，光看名字分不出轻重与落点。本表第一节是兜底，但根因在命名。若要治本，可考虑在名称里补维度词（如 `-brief` / `-prd` / `-priority` / `-plan`），代价是触发词与交叉引用要全量收口。
3. **`cyx-original-need-html` 与 `cyx-original-need-md` 是同一件事的两种渲染形态**——内容手法以 md 版为准，html 版只管渲染。两个入口并列，容易在触发时各加载一半。建议在两者的 `description` 里都写明「手法以 md 版为准」，或后续合并为一个技能的两种输出模式。
4. **部分技能缺 `display_name`**（显示为空）——`cyx-research-report`、`cyx-folder-deploy`、`cyx-git-push`、`cyx-github-deploy`、`cyx-douyin-extract`。不影响功能，但技能列表里认不出来是干什么的。
