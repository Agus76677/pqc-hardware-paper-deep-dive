# Revision Workflow

确认论文目录和反馈，按 accuracy、clarity、structure、depth、figures、format、provenance 分类。先用原论文及官方来源核验，再直接修改 `article.html`、`references.bib`、`sources.yaml` 或本地图表。保留已核验事实和来源，不用占位内容填补缺口。

运行 `validate_output.py --allow-missing-pdf`、`build_pdfs.py`、`validate_output.py`，并检查修订后的 HTML/PDF 视觉效果。报告已应用、拒绝或部分应用的反馈及原因。
