# Figure Extraction

先对照最终论文 PDF 盘点 figures、tables、subfigures、算法和源资产，再选择帮助理解机制与实验的内容。优先原始 PNG/SVG/PDF，留意图内外的 LaTeX 裁剪、旋转及字体。文件存到 paper-dir 内 figures/ 或 tables/，在 sources.yaml 登记完整相对路径。

脚本用绝对 Skill 路径执行，input/output/workspace 也用绝对路径：

```text
python "<skill-root>/scripts/extract_figures.py" download-source --arxiv-id "<versioned ID>" --workspace "<paper-dir>/build/arxiv"
python "<skill-root>/scripts/extract_figures.py" inventory --source-dir "<paper-dir>/build/arxiv/source" --output "<paper-dir>/build/figure-inventory.json"
python "<skill-root>/scripts/extract_figures.py" render --input "<source.pdf>" --output "<paper-dir>/figures/raw.png" --page 1 --dpi 300
```

inventory 是候选清单，识别 includegraphics、graphicspath 和浮动体，不能可靠展开所有宏、TikZ、subcaption 或解析最终图号。多 caption 或边界不明时不猜，必须人工核对。

## Exact crop before white-margin trimming

`autocrop` 只是去均匀边缘，不能代替 includegraphics 的 trim/clip。对于实际同时生效的 `trim={L B R T},clip`：

```text
python "<skill-root>/scripts/extract_figures.py" latex-crop --input "<original.pdf>" --output "<paper-dir>/figures/figure.png" --trim 10bp 5bp 10bp 0bp --dpi 300
```

四值顺序为左、下、右、上；默认裸值用 bp，支持 bp/pt/mm/cm/in；raster 输入必须给其固有 DPI，不猜 CSS 显示尺寸。仅非负裁剪；负 trim、旋转、viewport、选页等复杂语义需手动准确处理并记录。PDF 默认第一页；其他页先 render。没有 clip 的 trim 可能改变布局但不裁去图像，不能直接按上述命令截断。
剩余白边需要处理时再 autocrop：

```text
python "<skill-root>/scripts/extract_figures.py" autocrop --input "<paper-dir>/figures/raw.png" --output "<paper-dir>/figures/figure.png" --fuzz 3 --border 8
```

每次裁剪后视觉核对标签、坐标轴、边缘线条、子图与色标。crop 记录完整步骤，图注注明原 Figure/Table N。register 和 verify 用法见脚本 --help；verify 会解码图像/解析 SVG/PDF，不代表裁剪或图号已经正确。
