# Generation Workflow

解析论文身份与官方来源，运行 `prepare_output.py` 初始化独立目录，然后建立证据映射并提取关键图表。直接撰写 `article.html`，使用插件 `theme.css`、语义标题、MathML、表格、伪代码和 `<figure>`；事实必须带来源标记，引用键登记在 `references.bib`，细节和图表 provenance 登记在 `sources.yaml`。

完成后先运行 `validate_output.py --allow-missing-pdf`，再运行 `build_pdfs.py` 生成 `article.pdf`，最后再次验证并检查 PDF 中字体、图表、分页、链接和目录。多篇论文使用并列的 `outputs/<paper-name>/`，不创建 batch 或 papers 层。
