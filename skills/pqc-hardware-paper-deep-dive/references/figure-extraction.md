# Figure Extraction

先盘点论文全部 figures、tables、subfigures 与 source assets，再选择覆盖总览、方法、设置、主结果和消融/泛化的关键资产。优先复制原始 PNG/SVG；无 source 时用 `extract_figures.py` 调用 Poppler 渲染并裁剪。文件保存到 `figures/` 或 `tables/`，在 `article.html` 用相对路径 `<figure>` 引用，图注写明“来源：原论文 Figure N”，并在 `sources.yaml` 登记原编号、URL、裁剪参数和访问日期。


## 白边审计与裁剪

arXiv 栅格图片可能包含 LaTeX `trim` 未反映到原始文件的大白边。复制或渲染后使用：

```bash
python scripts/extract_figures.py autocrop --input figures/raw.png --output figures/figure.png --fuzz 3 --border 8
identify figures/raw.png figures/figure.png
```

检查标签、坐标轴和图注未被截断后再引用 autocrop 结果，并在 `sources.yaml` 记录 `crop: autocrop fuzz=3 border=8`。不要用 CSS 空白掩盖裁剪错误。
