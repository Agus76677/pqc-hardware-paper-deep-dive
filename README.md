# PQC Hardware Paper Deep Dive

一个面向后量子密码硬件论文的 Codex skill，用于生成或修订默认中文的 Paper Deep Dive。输入 arXiv、DOI、PDF、论文标题或已有输出目录，输出博客风格 HTML 和由同一 HTML 打印得到的 PDF。



面向 FPGA/ASIC 的格密码和编码密码，包括 Kyber、Dilithium、Falcon、HQC 与可核验原始规范的中国后量子算法。重点解释数学变换如何影响算术、存储、调度、物理时序和系统收益；优先分析 ATP，同时区分真实硬件利用率，给出有证据的创新假设与验证方案。

## 功能

- 生成或修订单篇/多篇论文深度解读
- 提取关键 Figure/Table，记录原论文来源与裁剪参数
- 维护 `references.bib` 和 `sources.yaml`，让引用、来源和图表可溯源
- 使用静态 HTML + Chromium 编译 PDF，不依赖 Astro、MDX、LaTeX 或 Pandoc
- 论文身份无法唯一确认时不会猜测，会请求补充 arXiv/DOI/PDF

## 安装

```bash
git clone git@github.com:Minakanmi-Yuki/paper-deep-dive-skill.git
cd paper-deep-dive-skill
```

在 Codex App 中选择“从本地目录导入 plugin”，指向该仓库目录；或放入你的 marketplace 后通过 `codex plugin add ai-paper-deep-dive@<marketplace-name>` 安装。安装后新开一个会话。

脚本运行需要 Python 3、Chrome/Chromium、Poppler 和 ImageMagick：

```bash
python3 skills/ai-paper-deep-dive/scripts/check_environment.py
```

## 调用

新开 Codex 会话后，直接用自然语言指定论文来源即可：

```text
使用 $ai-paper-deep-dive 生成 Paper Deep Dive，文章是 <https://arxiv.org/abs/1706.03762>。
```

也可以同时处理多篇论文或修订已有报告：

```text
调用 $ai-paper-deep-dive 处理这三篇论文，每篇输出到独立目录。
```

## 输出

每篇论文生成一个独立目录：

```text
outputs/<paper-name>/
├── article.html
├── article.pdf
├── references.bib
├── sources.yaml
└── figures/
```

许可证：Apache-2.0，见 [LICENSE](LICENSE)。

