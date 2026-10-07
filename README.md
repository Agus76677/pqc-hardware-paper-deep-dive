# PQC Hardware Paper Deep Dive

用于单篇 PQC 硬件论文的中文精读，输出有可见引用的 HTML 和由其打印的 PDF。跨论文独立比较需明确请求。技能不含用户私人研究背景，也没有未经核验的 CFNTT/KHNTT/Meta 公式。

## 使用与依赖

将本目录安装到支持 Skill 的工具的技能目录；入口为 `SKILL.md`，显示配置在 `agents/openai.yaml`。也可直接用绝对脚本路径运行。不需要 Astro/MDX/TeX。Python 3.8+；Python 包为 PyYAML、Pillow、pypdf，见 `scripts/requirements.txt`。Chromium/Chrome/Edge 用于打印；中文字体须实际可用。Poppler/ImageMagick 只在对应图表提取步骤需要。

下面所有 `<...>` 是需替换的路径或内容；输出根目录属于用户工作区，不能指向安装目录：

```text
python "<skill-root>/scripts/check_environment.py"
python "<skill-root>/scripts/install_dependencies.py"
python "<skill-root>/scripts/prepare_output.py" --output-root "<workspace>/outputs" --name "<paper-name>" --title "<exact title>" --paper-author "<author>" --year "<year>" --paper-url "<official URL>"
python "<skill-root>/scripts/retrieve_sources.py" --paper-dir "<paper-dir>" --arxiv-id "<versioned ID>"
```

本地原论文可在初始化时传 `--pdf "<file.pdf>"`；`--resume` 仅补缺文件。检索结果与已存身份冲突时停止，需核对后明确纠正原记录，不会混合作者或悄悄覆盖身份。
来源记录可用普通 YAML 或 JSON。身份检索产生 `verification_scope: metadata`；读取并核验具体证据后才改为 `content` 和填写 supports。

```text
python "<skill-root>/scripts/render_references.py" --paper-dir "<paper-dir>"
python "<skill-root>/scripts/validate_output.py" --paper-dir "<paper-dir>" --allow-missing-pdf
python "<skill-root>/scripts/build_pdfs.py" --paper-dir "<paper-dir>"
python "<skill-root>/scripts/validate_output.py" --paper-dir "<paper-dir>"
```

浏览器可通过环境变量 `PAPER_DEEP_DIVE_BROWSER` 显式指定；检测和构建共享同一定位逻辑。构建在独立 profile 中打印，验证实际 PDF 可解析并登记输入/输出摘要。仍必须人工逐页看字体、裁剪与分页。
论文确实没有需要使用的图片时，在 sources.yaml 写 `figure_omission_reason`，给 build/validate 同时加 `--allow-no-figures`；不能用此选项逃避应有的原图解释。

## 数据与指标

`sources.yaml`、可见引用和图表 schema 见 `references/source-provenance.md`；实验记录/公式注册见 `references/hardware-metrics.md`。项目公式注册示例：

```text
python "<skill-root>/scripts/hardware_metrics.py" register --registry "<workspace>/outputs/metrics-registry.json" --definition "<user-confirmed-definition.json>"
python "<skill-root>/scripts/prepare_output.py" --output-root "<workspace>/outputs" --title "<title>" --metrics-registry "<workspace>/outputs/metrics-registry.json"
python "<skill-root>/scripts/hardware_metrics.py" compute --paper-dir "<paper-dir>"
```

初始化复制项目 registry 快照，不读隐含全局配置；已初始化文章用 compute 的 `--registry` 导入明确的项目 registry。空 registry 表示尚无统一口径，不伪造 ATP。不同 metric 版本、平台和 operation scope 均被记录；缺输入或单位不匹配会输出 cannot_compute。

所有保留的 references 均在 SKILL.md 中明确路由。`build_pdfs.py` 为主构建入口，`build_html.py` 实际打印；`check_consistency.py` 只是 validate 的兼容入口，不能替代论文事实核验。安装脚本默认仅展示计划，`--apply` 才执行；此包不会安装依赖或修改已有个人 Skill。
