# CourseWeaver

CourseWeaver is a small, course-grounded tutoring agent framework. It combines local course materials, retrieval, a configurable tutor role, and an academic-integrity boundary. The tutor explains, asks questions, and reviews a learner's work without producing submission-ready answers.

CourseWeaver 是一个轻量、基于课程资料的学习 Agent 框架。它将本地课程资料、检索、可配置的教师角色和学术诚信边界组合在一起：帮助学生理解、提问和复盘，但不直接生成可提交的作业答案。

## Features / 功能

- Course packs are data, not hard-coded UI: each course supplies a manifest, materials, an index, and a tutor prompt.
- Agent access is configured in a local JSON file; shell-specific environment setup is not required.
- Supports OpenAI Responses API and OpenAI-compatible Chat Completions endpoints.
- Runs with Python's standard library on Windows, macOS, Linux, and containers.
- Includes an MIT-licensed miniature compiler course as a safe example.
- Keeps downloaded third-party materials, generated indexes, secrets, and local configuration out of Git.

- 课程以数据包形式加载，界面不再写死 Lectures 或 Assignments。
- Agent 通过本地 JSON 配置接入，不要求使用 PowerShell 设置环境变量。
- 支持 OpenAI Responses API 和兼容 OpenAI Chat Completions 的端点。
- 使用 Python 标准库，可运行于 Windows、macOS、Linux 和容器。
- 内置采用 MIT 许可的微型编译器示例课程。
- 第三方下载资料、生成索引、密钥和本机配置不会进入 Git。

## Quick start / 快速开始

Requirements: Python 3.10 or newer. No package installation is required for the bundled Markdown example.

环境要求：Python 3.10 或更高版本。运行自带的 Markdown 示例无需安装第三方包。

1. Create a local configuration from the template. / 从模板创建本机配置。

Windows Command Prompt:

```bat
copy config\settings.example.json config\settings.local.json
```

Windows PowerShell:

```powershell
Copy-Item config/settings.example.json config/settings.local.json
```

macOS, Linux, Git Bash, or WSL:

```bash
cp config/settings.example.json config/settings.local.json
```

2. Open `config/settings.local.json` and replace `agent.api_key`. This file is ignored by Git. / 打开 `config/settings.local.json`，填写 `agent.api_key`。该文件已被 Git 忽略。

```json
{
  "server": {"host": "127.0.0.1", "port": 8143},
  "course_path": "examples/compiler-foundations",
  "retrieval": {"max_chunks": 6},
  "agent": {
    "provider": "openai_responses",
    "base_url": "https://api.openai.com/v1",
    "api_key": "your-api-key",
    "model": "gpt-5-mini",
    "timeout_seconds": 120,
    "store": false
  }
}
```

Treat this file as a secret and restrict its filesystem permissions on shared machines. Environment variables remain available as optional deployment overrides: `COURSEWEAVER_CONFIG`, `COURSEWEAVER_API_KEY`, `COURSEWEAVER_MODEL`, `COURSEWEAVER_HOST`, and `COURSEWEAVER_PORT`.

请将该文件视为密钥文件，在多人共用的设备上限制其文件权限。环境变量仍可作为容器或部署环境的可选覆盖项，但不是日常使用的必要步骤。

3. Start the application from any terminal. / 在任意终端启动。

```text
python app.py
```

Open <http://127.0.0.1:8143>. Stop the foreground server with `Ctrl+C`.

浏览器访问 <http://127.0.0.1:8143>。前台运行时按 `Ctrl+C` 停止服务。

## Agent providers / Agent 供应商

`openai_responses` calls `{base_url}/responses`. The checked-in template uses the OpenAI API with `store: false`.

`openai_responses` 调用 `{base_url}/responses`。仓库模板默认使用 OpenAI API，并设置 `store: false`。

`openai_compatible_chat` calls `{base_url}/chat/completions` and can connect to services that implement the compatible request and response shape. Start from `config/settings.compatible.example.json`. Compatibility depends on the selected service; CourseWeaver does not claim that every provider supports the same models, privacy properties, or semantics.

`openai_compatible_chat` 调用 `{base_url}/chat/completions`，可以接入实现相同请求和响应格式的服务。可从 `config/settings.compatible.example.json` 开始配置。不同平台的模型、隐私策略和行为并不等价，请以对应平台文档为准。

To add a different API protocol, implement a provider with a `generate(instructions, prompt)` method in `providers.py`, then register it in `create_provider`.

如需接入不同 API 协议，在 `providers.py` 中实现带有 `generate(instructions, prompt)` 方法的 provider，并在 `create_provider` 中注册。

## Course pack format / 课程包格式

A course pack contains:

```text
my-course/
├── manifest.json   # Metadata, collections, and material paths
├── tutor.md        # Teaching role and integrity rules
├── chunks.json     # Searchable excerpts
├── lesson-01.md
└── practice-01.md
```

课程包由元数据、教学角色、检索片段和课程材料组成。`manifest.json` 中的 `collections` 可以是 Lessons、Readings、Labs、Assignments 或任何课程需要的分类。

Copy `examples/compiler-foundations`, edit its content and manifest, then rebuild the index:

复制 `examples/compiler-foundations`，修改内容和清单，然后重新生成索引：

```text
python scripts/build_index.py path/to/my-course
```

Set `course_path` in `config/settings.local.json` to that directory. The bundled indexer supports UTF-8 Markdown and text files. PDF ingestion should be implemented as an optional adapter so the core remains dependency-free.

在 `config/settings.local.json` 中将 `course_path` 指向新目录。内置索引器支持 UTF-8 Markdown 和纯文本；PDF 导入建议作为可选适配器实现，以保持核心零依赖。

## Stanford CS143 and copyright / Stanford CS143 与版权

Stanford CS143 can be a useful real-world course for trying CourseWeaver. The project author is also using this framework as a personal study companion while working through CS143. You can configure a private CS143 course pack to explore course-grounded explanations, progressive hints, and review workflows. This is a personal learning use case, not an official Stanford integration, affiliation, or endorsement.

Stanford CS143 可以作为体验 CourseWeaver 的实际课程案例。项目作者本人也正在使用这个框架辅助学习 CS143。你可以在本地配置私有的 CS143 课程包，用来体验基于课程资料的讲解、渐进式提示和复盘流程。这只是个人学习场景，并非 Stanford 官方集成，也不代表与 Stanford 存在关联或获得其认可。

This repository does **not** include Stanford CS143 lecture slides, assignments, solutions, or extracted text. Public availability on a website is not the same as permission to redistribute. CourseWeaver's MIT License cannot relicense third-party teaching materials.

本仓库**不包含** Stanford CS143 的讲义、作业、答案或抽取文本。网页可以公开访问，并不等同于允许第三方重新分发；CourseWeaver 的 MIT License 也不能覆盖第三方课程资料。

For private study, a user may create a local course pack from materials they are authorized to download from the [official CS143 page](https://web.stanford.edu/class/cs143/). Keep that pack under `courses/local/` or `course/`; both are ignored by Git. Do not publish course files, generated text indexes, or solution material without explicit permission from the rights holder. Also follow the course's academic-integrity policy.

个人学习时，用户可以从 [CS143 官方页面](https://web.stanford.edu/class/cs143/) 下载自己有权使用的资料并创建本地课程包。请将其放在 `courses/local/` 或 `course/` 下，这些路径已被 Git 忽略。未经权利人明确授权，不要发布课程文件、抽取后的文本索引或答案资料，同时应遵守课程的学术诚信政策。

The default `examples/compiler-foundations` pack is an example course covered by the repository's MIT License. This README explains how CS143 may be used locally; [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) records the repository's third-party rights boundary. Neither document grants permission to redistribute Stanford materials.

默认的 `examples/compiler-foundations` 是示例课程，受仓库 MIT License 覆盖。本 README 说明如何在本地将 CS143 用作学习案例；[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 集中声明仓库与第三方资料之间的权利边界。两份文档都不构成对 Stanford 课程资料再分发的授权。

## Repository layout / 仓库结构

```text
CourseWeaver/
├── app.py                         # HTTP server, retrieval, and course loading
├── providers.py                   # Agent API provider adapters
├── config/
│   ├── settings.example.json      # OpenAI Responses configuration template
│   ├── settings.compatible.example.json
│   │                               # OpenAI-compatible endpoint template
│   └── settings.local.json        # Local secrets and active settings (ignored)
├── examples/
│   └── compiler-foundations/      # MIT-licensed example course
│       ├── manifest.json          # Course metadata, collections, and files
│       ├── tutor.md               # Tutor role and integrity boundary
│       ├── chunks.json            # Searchable course excerpts
│       ├── lesson-01.md
│       ├── lesson-02.md
│       └── practice-01.md
├── scripts/
│   └── build_index.py             # Markdown/text index builder
├── static/
│   ├── index.html                 # Browser interface
│   ├── app.js                     # Course and chat interactions
│   └── style.css                  # Interface styles
├── tests/
│   └── test_app.py                # Unit and regression tests
├── course/                        # Optional local course data (ignored)
├── courses/
│   └── local/                     # Optional local course packs (ignored)
├── .gitignore
├── LICENSE                        # MIT license for framework/example course
├── THIRD_PARTY_NOTICES.md         # Third-party material boundaries
└── README.md
```

The committed framework is divided into four layers: `app.py` handles the local service and retrieval, `providers.py` isolates model APIs, `static/` contains the browser client, and each directory under `examples/` is a self-contained course pack. `scripts/build_index.py` converts UTF-8 Markdown or text materials into the `chunks.json` retrieval index.

仓库中可提交的框架分为四层：`app.py` 负责本地服务和检索，`providers.py` 隔离不同模型 API，`static/` 保存浏览器端界面，而 `examples/` 下的每个目录都是一个独立课程包。`scripts/build_index.py` 用于把 UTF-8 Markdown 或纯文本资料转换为 `chunks.json` 检索索引。

`config/settings.example.json` and `config/settings.compatible.example.json` are safe templates. Copy one to `config/settings.local.json` for actual use. The local file may contain an API key and is intentionally excluded by `.gitignore`.

`config/settings.example.json` 和 `config/settings.compatible.example.json` 是可以提交的安全模板。实际使用时复制其中一个为 `config/settings.local.json`；本机配置可能包含 API Key，因此已被 `.gitignore` 排除。

Use `examples/` only for material that may be redistributed under the repository license. Put downloaded, private, or third-party course packs under `course/` or `courses/local/`. Those directories and common document formats such as PDF, PPTX, and DOCX are ignored to prevent accidental publication.

`examples/` 只应放置可以按照仓库许可证再分发的资料。下载的、私人的或第三方课程包应放入 `course/` 或 `courses/local/`；这些目录及 PDF、PPTX、DOCX 等常见文档格式均被忽略，以防误提交到公开仓库。

## Security / 安全

- Never commit `config/settings.local.json`, API keys, private notes, or downloaded course material.
- Review a third-party provider's retention and training policy before sending course excerpts or student work.
- Bind to `127.0.0.1` by default. Changing the host to `0.0.0.0` exposes the service to the surrounding network and should only be done with appropriate authentication and firewall controls.

- 不要提交 `config/settings.local.json`、API Key、私人笔记或下载的课程资料。
- 在发送课程片段或学生作业前，检查第三方模型平台的数据保留与训练政策。
- 默认只监听 `127.0.0.1`。改为 `0.0.0.0` 会向所在网络暴露服务，必须配套身份认证和防火墙控制。

## License / 许可证

CourseWeaver source code and the included example course are licensed under the [MIT License](LICENSE). Third-party course materials are excluded.

CourseWeaver 源代码与仓库内的示例课程采用 [MIT License](LICENSE)；第三方课程资料不在授权范围内。
