# Troubleshooting

- 身份冲突或标题不唯一：核对 DOI/arXiv 版本/原 PDF；明确纠正已有 metadata 后再检索。不用 --accept-best 把未知论文标成已核验。
- Windows 浏览器：check_environment 与 build 共用定位；可设置 PAPER_DEEP_DIVE_BROWSER 为可执行文件绝对路径。无需把系统全部 PATH 重写。
- 裁图工具：默认只检测核心依赖，提取前加 --require-figure-tools。系统 convert.exe 不算 ImageMagick；查看 install_dependencies 的实际缺失项计划。
- YAML：支持 JSON 和普通 YAML；PyYAML 缺失时装 scripts/requirements.txt，不把文档名改成其他格式绕过 schema。
- 引用：每个 key 同时出现在 BibTeX 和 sources；Paper/Code 给 locator；先 render_references 再 validate。不要重复键，旧 document ID 不得换目标。
- 未核验证据：登记明确 evidence_gaps 并标注 data-uncertain；正文不能据此做确定性结论。缺代码无需伪造 Code 内容。
- 图表/样式：保持相对路径且文件在输出目录内；SVG/CSS 嵌套资源也须本地可用。图号字段为 original_figure。
- PDF：查看 build/browser.log；输出必须能被 pypdf 解析且匹配 build-manifest 输入/输出摘要。修改任何正文/图表/记录后重新 build，不接受旧 PDF 代替。
- 字体/分页：系统需中文字体；Windows 可用微软雅黑/宋体，Linux/macOS 可安装 Noto/思源。检测只是提示，必须看 PDF 的中文/数学符号及表格分页。
- 校验通过仍有事实问题：validate 和兼容 check_consistency 不是论文事实验证器。回到原表、原图、代码和公式逐项人工核验。
