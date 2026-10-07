---
name: pqc-hardware-paper-deep-dive
description: Generate or revise evidence-traceable Chinese deep dives of FPGA and ASIC post-quantum cryptography papers, with original experimental tables, architectural reasoning, traceable metrics, and HTML/PDF outputs. Use for paper reading and revision; broader independent cross-paper comparison requires an explicit request.
---

# PQC Hardware Paper Deep Dive

默认深入读一篇论文：理解算法到架构的机制，保留原始实验结果及条件，再形成有证据的研究假设。唯一正文为 `article.html`，PDF 由同一 HTML 经 Chromium 打印；不建立 Markdown/LaTeX 正文或使用 Pandoc/TeX/Biber。

## Paths and loading

先确定安装目录 `<skill-root>` 和用户工作区绝对路径 `<output-root>`。所有脚本使用 `python "<skill-root>/scripts/NAME.py"`，不能假定当前目录是安装目录。每篇论文保存在 `<output-root>/<paper-name>/`；修订现有文章时保留原目录和核验记录。

始终读取：
- [references/article-structure.md](references/article-structure.md)：固定主结构及小节归属。
- [references/pqc-hardware-checklist.md](references/pqc-hardware-checklist.md)：选择论文实际覆盖的技术维度。
- [references/source-provenance.md](references/source-provenance.md)：来源 schema、核验状态、可见引用。

按需读取：
- 有 FPGA/ASIC 实验结果：[references/hardware-metrics.md](references/hardware-metrics.md)。
- 提取、核对或裁剪图表：[references/figure-extraction.md](references/figure-extraction.md)。
- 写算法步骤或复刻博客样式：[references/blog-mdx-style.md](references/blog-mdx-style.md) 及 `assets/components/algorithm.html`。
- 获取来源、依赖、构建或验证失败：[references/troubleshooting.md](references/troubleshooting.md)。

## Execution

1. 用 `scripts/check_environment.py` 检测核心依赖；需要 PDF 渲染/裁图时加 `--require-figure-tools`。安装计划由 `scripts/install_dependencies.py` 展示，确认实际缺失项后按当前环境权限处理；不自动引入管理员权限。Python 依赖见 `scripts/requirements.txt`。
2. 确认论文 title、authors、year、DOI/arXiv **版本** 或用户 PDF。身份不唯一时请求确切标识，不能接受低置信检索结果为事实。用 `scripts/prepare_output.py --output-root "<output-root>" --name "<paper-name>" --title "<title>" ...` 初始化；已有目录可 `--resume`，但不会覆盖元数据或正文。
3. 按 provenance reference 用 `scripts/retrieve_sources.py` 登记官方 metadata 和来源。脚本取得 metadata 只证明身份，不表示读过论文。阅读全文、补充材料、标准、官方代码后，手动登记具体 supports、version/commit、verified 和 verification_scope；代码未公开就明确缺口。
4. 盘点论文全部 figures、tables、subfigures。脚本 inventory 仅作候选清单，需对照最终 PDF 核对。原图裁剪需保持 trim/clip 语义，并视觉检查标签/坐标/子图；本地资产须在输出目录内。
5. 直接改写初始化的 `article.html`，保留固定九个主标题，按论文范围增删小节。使用语义 HTML、MathML、表格、图注和内置 Algorithm 片段；不要强加 NTT、全加速器、代码映射或安全分析。
6. 保存原始实验表、逐行来源和设计点。作者 ATP 原值/定义与 `【Analysis】` 重算分开。用户给定统一口径时，按 metrics reference 登记项目 registry 并用 `scripts/hardware_metrics.py compute --paper-dir "<paper-dir>"` 重算。没有已核验定义时不猜权重，不宣称自动记住标杆论文公式。
7. 运行 `scripts/render_references.py --paper-dir "<paper-dir>"`，生成正文可见引用、文末 bibliography 和目录。再运行 `scripts/validate_output.py --paper-dir "<paper-dir>" --allow-missing-pdf` 做预检。
8. 运行 `scripts/build_pdfs.py --paper-dir "<paper-dir>"`。它会再生成可见引用、预检、使用隔离浏览器目录打印新 PDF，并保存 `build-manifest.json`。随后运行 `scripts/validate_output.py --paper-dir "<paper-dir>"`。HTML、图像、样式、来源或指标记录变化后必须重新构建。
9. 逐页视觉检查 PDF 的中文/公式字体、图表裁剪、分页、溢出、空白页、引用和目录链接。结构校验不证明技术事实或排版正确，`scripts/check_consistency.py` 只是预检兼容入口。修订重复第 7–9 步；依赖或证据不足时保留文件，明确未完成项，不能交付旧 PDF 冒充新结果。

正文所有事实段落用 `【Paper】` / `【Code】` / `【Source】`，推导、重算与假设用 `【Analysis】`。事实段落给可见 `a[data-cite]` 引用；Paper/Code 定位到页、节、图表或代码路径/行/commit。未核验引用必须显式标记且登记 evidence gap，不得暗示已证明。

只有用户明确要求，才开展独立的跨论文 comparison mode。保存/解释作者原 comparison table、核验关键引用不等于授权主动建立外部排行榜。资源、范围、版本、平台、测量阶段、保护等级与指标定义不同，不能只因算法同名就直接比较。

## Architectural reasoning and delivery

追踪“算法结构 → 表示/运算依赖 → 算术与存储 → 调度/并行 → 物理实现 → 结果”；区分运算减少、单元成本、访存减少、利用率、频率和系统收益。局部核的影响边界要清楚；完整加速器需解释模块间速率、数据与资源复用关系。研究假设需说明残留瓶颈、改变的机制、最近基线、最小实验和否定条件，不把猜测写成贡献。

交付 `article.html`、`article.pdf`、`theme.css`、`references.bib`、`sources.yaml`、图表、`metrics.json`、`metrics-registry.json`、`build-manifest.json`；说明实际执行的核验和视觉检查、证据缺口及未完成项。不以个人工程路径、研究目标、Zotero key 或固定标杆论文充当通用运行配置。
