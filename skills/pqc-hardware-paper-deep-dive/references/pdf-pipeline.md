# HTML PDF Pipeline

唯一编译链为 `article.html` → Chromium headless `--print-to-pdf` → `article.pdf`。依赖是 Chromium（或 Chrome/Edge）、Poppler、ImageMagick 和中文字体；使用 `check_environment.py` 与跨平台安装脚本检测/安装。图表提取可用 Poppler/ImageMagick，HTML PDF 不依赖 Pandoc、TeX 或 Biber。

PDF 生成后检查缺失 glyph、裁剪、溢出、空白页、断裂链接和目录脚本；不要复制其他 PDF 作为结果。
