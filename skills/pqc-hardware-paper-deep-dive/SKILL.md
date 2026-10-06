---
name: pqc-hardware-paper-deep-dive
description: Generate or revise evidence-traceable Chinese paper deep dives for FPGA and ASIC implementations of post-quantum cryptography. Focus on algorithm-to-hardware mapping, arithmetic and memory architecture, scheduling, implementation efficiency, reproducibility, and research opportunities. Preserve sourced figures, bibliography, HTML, and PDF outputs.
---

# PQC Hardware Paper Deep Dive

需要复刻博客 MDX 排版时，先阅读 `references/blog-mdx-style.md`，并读取并按需复制
`assets/components/algorithm.html`。后者是正式内置的 Algorithm/AlgorithmStep 静态组件片段，
无需安装 Astro、MDX、npm 包或其他运行时组件；禁止以裸 fenced pseudocode 替代它。

输出唯一正文源文件为 `article.html`，PDF 由该 HTML 使用 Chromium 直接打印得到 `article.pdf`。
不要创建或要求 Markdown、LaTeX、Pandoc、XeLaTeX 或 Biber 源文件。
保留 `references.bib` 用于统一引用，保留 `sources.yaml` 用于事实、代码与图表溯源。
默认正文使用中文，保留必要的 English technical terms；不设固定页数。

## Workflow

1. Run `python scripts/check_environment.py`.
   If dependencies are missing, inspect the installation plan first. Request confirmation before operations that require administrator privileges, then re-run the environment check.

2. Normalize the paper identity.
   Accept a title, arXiv ID/URL, DOI, PDF, or an existing output directory.
   If the paper cannot be identified unambiguously, request a precise identifier rather than guessing.
   Prefer the user-provided name, official abbreviation, or a paper-title slug for the output directory.

3. Initialize the paper directory with `scripts/prepare_output.py`.
   Store multiple papers directly under `outputs/<paper-name>/`; do not introduce unnecessary batch or timeline directories.

4. Read:
   - `references/article-structure.md`
   - `references/pqc-hardware-checklist.md`

   Use the fixed main article structure, but activate only the technical dimensions relevant to the paper.
   Do not force lattice-specific, code-based, NTT, security, or full-accelerator analysis onto papers that do not cover them.

5. Read `references/hardware-metrics.md` whenever the paper reports hardware implementation results.
   Use it to preserve raw experimental conditions, record author-defined metrics, and recompute canonical derived metrics when the required inputs are available.
   Do not turn a single-paper deep dive into a broad literature ranking unless the user explicitly asks for cross-paper comparison.

6. Collect the strongest available primary evidence:
   original paper, supplementary material, relevant specification or standard, official implementation, project page, and released RTL/software when available.

   Use:
   - `【Paper】` for statements directly supported by the paper or supplement;
   - `【Code】` for implementation facts verified from released code or RTL;
   - `【Source】` for external primary sources such as standards, specifications, official project material, or closely related prior work;
   - `【Analysis】` for independent interpretation, derivation, recomputation, or research hypotheses.

   Record URLs, access dates, versions/commits, supported sections, and figure provenance in `sources.yaml`.

7. Inspect all relevant figures, tables, and subfigures.
   Prefer the original arXiv LaTeX source when available and preserve `\includegraphics` crop semantics.
   Use `scripts/extract_figures.py autocrop` only when necessary, then visually verify the result.

   Prioritize figures that materially help explain:
   - algorithm-to-hardware mapping;
   - arithmetic or transform structure;
   - datapath and memory organization;
   - scheduling and data movement;
   - complete accelerator architecture;
   - implementation results;
   - ablation or design-space exploration.

8. Write `article.html` directly using semantic HTML, MathML, tables, and figure captions.
   Do not generate a separate Markdown or LaTeX manuscript.

   When presenting pseudocode or algorithm procedures, copy the structure from
   `assets/components/algorithm.html` and preserve the required Algorithm/AlgorithmStep classes.

   Citation keys used in HTML must exist in `references.bib`.

9. Build the PDF with:

   `python scripts/build_pdfs.py --paper-dir <dir>`

   or the corresponding HTML build command supported by the repository.

   The PDF must be generated from `article.html` through Chromium and must not be substituted with an unrelated or pre-existing PDF.

10. Run:

   `python scripts/validate_output.py --paper-dir <dir>`

   Fix validation errors before delivery.
   Verify HTML integrity, local figures, citation keys, source registration, placeholders, and PDF validity.

## Analysis Principles

Trace the complete causal chain when the evidence permits:

algorithmic structure
→ mathematical or representation choice
→ operation count and data dependency
→ datapath and memory organization
→ scheduling and parallelism
→ physical implementation behavior
→ measured performance.

Do not stop at labels such as “higher parallelism”, “deeper pipeline”, or “resource sharing”.
Explain the concrete architectural mechanism and the resource or dependency it changes.

Distinguish carefully between:

- fewer mathematical operations;
- cheaper implementation of each operation;
- reduced memory traffic;
- improved scheduling or utilization;
- higher achievable frequency;
- increased hardware parallelism;
- system-level speedup.

Do not treat them as interchangeable explanations.

For local-kernel papers, analyze the kernel deeply but state the boundary of its impact on the complete cryptographic operation.

For complete accelerators, connect arithmetic, memory, scheduling, hashing/sampling/decoding, and top-level protocol execution rather than discussing each block in isolation.

## Evidence and Comparison Discipline

Never present values from different implementations as directly comparable solely because they implement algorithms with the same name.

When hardware results are reported, preserve:
- exact algorithm/version and parameter set;
- implementation scope;
- device or technology;
- tool and implementation stage;
- resource counts;
- cycle count, frequency, latency, throughput, and energy/power when available;
- the author's own derived metrics and their formulas.

Use `references/hardware-metrics.md` for derived metrics.

Keep reported results separate from recomputed metrics and independent analysis.

Use `未报告` or `未核验` when evidence is unavailable rather than filling the gap with assumptions.

Do not infer standard compliance solely from similar parameters or algorithm names.
Verify the exact specification or algorithm revision when compliance matters.

Do not claim side-channel or fault resistance unless the corresponding property is supported by evidence.
Constant-time behavior alone does not establish comprehensive side-channel security.

## Research Analysis

Research analysis should emerge from the paper itself:

prior bottleneck
→ proposed mechanism
→ hardware effect
→ measured evidence
→ remaining bottleneck
→ candidate research hypothesis.

Prefer testable hypotheses over generic optimization suggestions.

A useful research direction should identify, when possible:

- the architectural mechanism to change;
- why the current design leaves room for improvement;
- the expected resource/performance effect;
- the closest relevant baseline;
- the minimum experiment needed to test the idea;
- the condition under which the hypothesis would be rejected.

Do not present speculative architectural ideas as established contributions.

## HTML Metadata and Style

`article.html` must include:

- `lang="zh-CN"`
- `<title>`
- `paper-title`
- `paper-authors`
- `paper-year`
- `paper-url`
- `code-url`
- `project-url`
- `dataset-url`
- `domains`

Use the bundled `theme.css`.
Do not depend on external blog runtime components or project-specific paths.

## Revision and Failure Handling

When revising an existing deep dive, edit the existing `article.html` and preserve already verified sources and local figures whenever possible.

If paper retrieval, figure extraction, browser rendering, or PDF generation fails, read
`references/troubleshooting.md`.

Report evidence gaps explicitly.
Do not publish fabricated details, unresolved placeholders, or guessed implementation facts.

## Delivery

Report:

- output directory;
- `article.html`;
- `article.pdf`;
- `references.bib`;
- `sources.yaml`;
- figure directory;
- unresolved evidence gaps;
- important warnings;
- commands actually executed.
