# Source Provenance and Visible Citations

优先原论文/补充材料、官方代码、标准与规范、官方项目资料。来源类型标签不等于已核验，identity metadata 和技术内容必须区分。

## sources.yaml

允许普通 YAML 或 JSON，脚本写 JSON（有效 YAML 子集）。`id` 与 BibTeX key 完全相同、全局唯一；不重用 ID 指向别的来源。修改 URL/version/commit 时撤销旧核验和 supports，重新读证据。模板：

```yaml
schema_version: 2
paper:
  title: Exact paper title
  authors: [Author One]
  year: '2026'
  url: https://arxiv.org/abs/2401.12345v2
  arxiv_id: 2401.12345v2
sources:
  - id: paper
    type: paper
    title: Exact paper title
    url: https://arxiv.org/abs/2401.12345v2
    accessed: '2026-10-06'
    version: 2401.12345v2
    supports: ['Section 4 architecture', 'Table III design A']
    verified: true
    verification_scope: content
figures:
  - id: architecture
    path: figures/architecture.png
    original_figure: Figure 2
    caption: Original caption or faithful explanation
    source_id: paper
    source_file: source/arch.pdf
    crop: 'none'
    accessed: '2026-10-06'
evidence_gaps: []
figure_omission_reason: ''
```

日期示例不能原样冒充实际访问日期。year/authors 未报告时 HTML 标 `未报告`，不要填 Unknown 或猜值。本地 PDF 可用 local_path 记录原件，并以初始化复制文件的 file URI 作为 paper.url；HTML/BibTeX/manifest 的身份要一致。
`verified: true` 表示 supports 中列出的内容已经人工核验，不是整个仓库/论文所有事实已被验证。metadata retrieval 不赋予 content 核验。代码须锁定 commit，并以路径/模块/行作定位。

## Authoring citations

事实段落示例：

```html
<p><span class="fact paper">【Paper】</span>具体事实。
<a data-cite="paper" data-locator="Table III, row A">[paper]</a></p>
```

多个来源分别写多个 a 标签，每个 data-cite 只放一个 key。Paper/Code 引用必须有 locator。用 `【Analysis】` 标记推导、重算及假设；同样可以引用其依据。
未核验来源只可明确保留为缺口：a 加 `data-uncertain="true"`，正文写 `未核验`，并在 evidence_gaps 添加 `{source_id: key, reason: why}`。不能以此支持确定性技术结论。

`references.bib` 支持手工维护的 @article/@online 等、字面 braced/quoted 字段；不解析 @string、宏拼接或完整 TeX 命令。人工条目放 AUTO 块外，键不能重复。retrieve_sources 只更新 AUTO 块。
在第九节放 `<div id="bibliography"></div>`，使用 `render_references.py` 将 data-cite 渲染为可点击编号和文末可读条目，同时生成目录；结果写回唯一正文 article.html，PDF 不依赖额外运行时。

## Figure registration

路径为输出目录内相对完整路径；basename 相同不代表同一资产。字段统一为 original_figure，不使用旧 paper_figure。source_id 必须已登记；crop 明确 none 或参数，不能空白。
用 `extract_figures.py register --paper-dir ... --file <absolute-file> --paper-figure 'Figure 2' --caption '...' --source-id paper --crop 'none'` 登记。论文表格若重建成 HTML，逐行出处进入 metrics.json/正文引用；不是必须截图。

结构验证检查关键字段和引用关联，但不能判断引用是否真实支持论断。交付前人工核对所有关键事实、推导、图号和实验行。
