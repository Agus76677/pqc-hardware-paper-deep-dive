# Troubleshooting

- **标题无法确认**：提供 arXiv ID、DOI 或 PDF；不要猜测论文身份。
- **图表提取失败**：确认 Poppler/ImageMagick；优先下载 arXiv source，失败时用高分辨率 PDF 渲染并记录裁剪来源。
- **HTML 图不显示**：使用相对路径（如 `figures/figure-1.png`），确认文件在输出目录内，并用浏览器直接打开 HTML。
- **PDF 失败**：运行 `check_environment.py`，设置 `PAPER_DEEP_DIVE_BROWSER` 指向 Chromium/Chrome/Edge，检查浏览器日志和 HTML 控制台错误。
- **中文乱码**：安装 Noto CJK/思源字体并重启终端；不要依赖 TeX 字体。
- **引用或 provenance 错误**：确保 `data-cite` 键存在于 `references.bib`，每个本地图表在 `sources.yaml` 的 `figures` 中登记。
