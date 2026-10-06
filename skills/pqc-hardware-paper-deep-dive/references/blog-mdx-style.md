# 博客 MDX 风格静态复刻

该 skill 不加载 Astro/MDX 运行时，而是用 `assets/html-theme/theme.css` 复现博客的阅读体验。
`assets/components/algorithm.html` 是正式随 skill 分发的 Algorithm 组件片段；生成算法时复制
该片段并替换示例内容，保证结构与博客 `Algorithm.astro` / `AlgorithmStep.astro` 一致。

## 组件映射

| 博客 MDX | 独立 HTML |
| --- | --- |
| `<Algorithm>` | `<figure class="algorithm">` |
| `<AlgorithmStep indent={n} keyword="...">` | `<li class="algorithm-step" style="--algorithm-indent:n">` |
| prose 图片 | `<figure><img ...><figcaption>...</figcaption></figure>` |
| Callout/blockquote | `<blockquote>...</blockquote>` |

Algorithm 必须使用内置片段中的 `.algorithm-caption`、可选 `.algorithm-io`、`.algorithm-lines`、
`.algorithm-step`、`.algorithm-line-number` 和 `.algorithm-line-content`，这样会得到博客同款的标题、
Input/Output 区、行号和缩进。不要用裸的 fenced code 代替正式算法，也不要依赖外部组件包。

## 紧凑排版约束

- 图片上下间距由主题统一控制；不要在行内 style 中追加大于 `1rem` 的 margin。
- 图注紧跟图片并写明 `来源：原论文 Figure/Table N`。
- 连续相关图片可放入同一 `<figure>` 或 `.figure-grid`，避免每张图都产生大段空白。
- PDF 由 Chromium 打印同一 HTML；修改主题后必须重新运行 `build_pdfs.py` 与 `validate_output.py`。
