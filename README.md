# CourseWeaver

CourseWeaver is a small, course-grounded tutoring agent framework. It combines local course materials, retrieval, a configurable tutor role, and an academic-integrity boundary. The tutor explains, asks questions, and reviews a learner's work without producing submission-ready answers.

CourseWeaver 是一个轻量、基于课程资料的学习 Agent 框架。它将本地课程资料、检索、可配置的教师角色和学术诚信边界组合在一起：帮助学生理解、提问和复盘，但不直接生成可提交的作业答案。

## Features / 功能

- Course packs are data, not hard-coded UI: each course supplies a manifest, materials, an index, and a tutor prompt.
- Agent access is configured in a local JSON file; shell-specific environment setup is not required.
- Supports OpenAI Responses API and OpenAI-compatible Chat Completions endpoints.
- Displays original course PDFs with the browser's native page, zoom, search, print, and download controls while retaining extracted text for retrieval.
- Provides a focused reading workspace with a compact collection selector and an on-demand course tutor toggled with `Ctrl + \``.
- Runs with Python's standard library on Windows, macOS, Linux, and containers.
- Includes an MIT-licensed miniature compiler course as a safe example.
- Keeps downloaded third-party materials, generated indexes, secrets, and local configuration out of Git.

- 课程以数据包形式加载，界面不再写死 Lectures 或 Assignments。
- Agent 通过本地 JSON 配置接入，不要求使用 PowerShell 设置环境变量。
- 支持 OpenAI Responses API 和兼容 OpenAI Chat Completions 的端点。
- 可直接使用浏览器原生 PDF 阅读器查看课程原稿，同时保留抽取文本用于检索和引用。
- 提供专注阅读界面、紧凑的资料分类选择器，以及可通过 `Ctrl + \`` 开关的课程导师。
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
    "use_system_proxy": false,
    "api_key": "your-api-key",
    "model": "gpt-5-mini",
    "timeout_seconds": 120,
    "store": false
  }
}
```

Treat this file as a secret and restrict its filesystem permissions on shared machines. Environment variables remain available as optional deployment overrides: `COURSEWEAVER_CONFIG`, `COURSEWEAVER_COURSE_PATH`, `COURSEWEAVER_API_KEY`, `COURSEWEAVER_MODEL`, `COURSEWEAVER_HOST`, and `COURSEWEAVER_PORT`. `COURSEWEAVER_COURSE_PATH` overrides the active `course_path` without editing JSON.

Agent requests connect directly by default so unrelated shell proxy variables cannot redirect the configured API. Set `agent.use_system_proxy` to `true` only when the API must be reached through the operating system's proxy configuration.

请将该文件视为密钥文件，在多人共用的设备上限制其文件权限。环境变量仍可作为容器或部署环境的可选覆盖项（例如用 `COURSEWEAVER_COURSE_PATH` 覆盖当前课程目录，无需修改 JSON），但不是日常使用的必要步骤。

3. Start the application from any terminal. / 在任意终端启动。

```text
python app.py
```

Open <http://127.0.0.1:8143>. Stop the foreground server with `Ctrl+C`.

浏览器访问 <http://127.0.0.1:8143>。前台运行时按 `Ctrl+C` 停止服务。

## Reading workspace / 阅读工作区

Choose a collection from the left sidebar, then open a course item. When an item defines `display_file`, CourseWeaver embeds the original PDF and uses the browser's native controls for page navigation, zoom, search, printing, and downloading. Items without `display_file` use the built-in Markdown/text reader.

The desktop reader enters a focused layout that gives the document the available viewport. Select **Ask tutor** or press `Ctrl + \`` (the same physical key as `~`) to open the tutor above a PDF; press the shortcut again to close it. The shortcut also works when focus is inside the embedded PDF viewer. On narrow screens, the material list, document, and tutor appear as separate views to preserve usable reading space.

在左侧选择资料分类并打开课程内容。配置了 `display_file` 的项目会直接嵌入原始 PDF，并使用浏览器自带的翻页、缩放、搜索、打印和下载功能；未配置 `display_file` 的项目则使用内置 Markdown/文本阅读器。

桌面端进入资料后会切换到专注阅读布局。点击 **Ask tutor** 或按 `Ctrl + \``（与 `~` 相同的物理按键）可以在 PDF 上方打开导师，再按一次即可关闭；即使焦点位于嵌入的 PDF 查看器内，快捷键也能生效。窄屏设备会分别显示资料目录、文档和导师，以保留足够的阅读空间。

## Agent providers / Agent 供应商

`openai_responses` calls `{base_url}/responses`. The checked-in template uses the OpenAI API with `store: false`.

`openai_responses` 调用 `{base_url}/responses`。仓库模板默认使用 OpenAI API，并设置 `store: false`。

`openai_compatible_chat` calls `{base_url}/chat/completions` and can connect to services that implement the compatible request and response shape. Start from `config/settings.compatible.example.json`. Compatibility depends on the selected service; CourseWeaver does not claim that every provider supports the same models, privacy properties, or semantics.

`openai_compatible_chat` 调用 `{base_url}/chat/completions`，可以接入实现相同请求和响应格式的服务。可从 `config/settings.compatible.example.json` 开始配置。不同平台的模型、隐私策略和行为并不等价，请以对应平台文档为准。

To add a different API protocol, implement a provider with a `generate(instructions, prompt)` method in `providers.py`, then register it in `create_provider`.

如需接入不同 API 协议，在 `providers.py` 中实现带有 `generate(instructions, prompt)` 方法的 provider，并在 `create_provider` 中注册。

## Tutor role / 教师角色配置

Agent connection settings and tutor behavior live in different files:

- `config/settings.local.json` selects the model provider, API endpoint, API key, model, active `course_path`, and retrieval limit.
- `<course_path>/tutor.md` defines the tutor's role, teaching style, response structure, and assignment-help boundary.

Agent 的连接参数与教师行为分别保存在两个位置：

- `config/settings.local.json`：配置模型平台、API 地址、API Key、模型、当前 `course_path` 和检索数量。
- `<course_path>/tutor.md`：配置教师身份、教学风格、回答结构以及作业帮助边界。

For the bundled example, edit `examples/compiler-foundations/tutor.md`. For a local CS143 pack configured as `"course_path": "courses/local/cs143"`, edit `courses/local/cs143/tutor.md`. Changes to the active `tutor.md` apply to the next chat request. Restart CourseWeaver after changing `settings.local.json`, including when switching `course_path`.

使用内置示例时，修改 `examples/compiler-foundations/tutor.md`。如果本地 CS143 课程包配置为 `"course_path": "courses/local/cs143"`，则修改 `courses/local/cs143/tutor.md`。当前课程的 `tutor.md` 会在下一次对话请求时生效；修改 `settings.local.json`（包括切换 `course_path`）后需要重启 CourseWeaver。

The tutor file is plain Markdown. A useful structure is `Role`, `Teaching behavior`, `Integrity boundary`, and `Response style`. Keep the integrity boundary when adapting the prompt for assignment-based courses.

教师配置是普通 Markdown 文件，建议包含 `Role`、`Teaching behavior`、`Integrity boundary` 和 `Response style`。针对包含作业的课程调整提示词时，建议保留学术诚信边界。

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

Set `course_path` in `config/settings.local.json` to that directory, or set the `COURSEWEAVER_COURSE_PATH` environment variable. The bundled indexer supports UTF-8 Markdown and text files. For PDF-based courses, convert handouts to UTF-8 text with an external tool such as `pdftotext` before building the index, so the core remains dependency-free.

在 `config/settings.local.json` 中将 `course_path` 指向新目录，或设置 `COURSEWEAVER_COURSE_PATH` 环境变量。内置索引器支持 UTF-8 Markdown 和纯文本；对于以 PDF 为主的课程，可先用 `pdftotext` 等外部工具转成 UTF-8 文本再建索引，以保持核心零依赖。

To display the original PDF while retaining extracted text for retrieval, keep `file` pointed at the UTF-8 text and add an optional `display_file` to the same manifest item:

```json
{
  "id": "lecture-01",
  "title": "Course Overview",
  "file": "lectures/lecture-01.txt",
  "display_file": "pdf/lectures/lecture01.pdf",
  "retrieval_enabled": true
}
```

配置 `display_file` 后，阅读器会直接显示原始 PDF；`file` 指向的文本只用于本地检索与导师引用。未配置 `display_file` 的资料仍使用内置的 Markdown/文本阅读器。

## Trying Stanford CS143 / 使用 Stanford CS143 尝试

Stanford CS143 is a good real-world course for trying CourseWeaver, and the project author is also using the framework while studying it. You can download the materials you need from the [official CS143 page](https://web.stanford.edu/class/cs143/), build a local course pack under `courses/local/cs143/`, and point `course_path` to it. This lets you use the tutor for course-grounded explanations, progressive hints, and review without adding the course files to this repository. A typical local pack points `course_path` at `courses/local/cs143` in `config/settings.local.json`, or sets `COURSEWEAVER_COURSE_PATH=courses/local/cs143`, then restarts CourseWeaver.

Stanford CS143 很适合作为 CourseWeaver 的实际学习案例，项目作者本人也正在使用这个框架学习该课程。你可以从 [CS143 官方页面](https://web.stanford.edu/class/cs143/) 获取所需资料，在 `courses/local/cs143/` 下建立本地课程包，然后将 `course_path` 指向该目录。这样即可使用基于课程资料的讲解、渐进式提示和复盘功能，同时不需要把课程文件加入本仓库。本地课程包通常把 `config/settings.local.json` 的 `course_path` 设为 `courses/local/cs143`，或设置 `COURSEWEAVER_COURSE_PATH=courses/local/cs143`，然后重启 CourseWeaver。

Course materials remain under their respective terms; this repository only provides the framework and example pack. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the short third-party materials note.

课程资料仍遵循其各自的使用条款，本仓库只提供框架和示例课程包。简要的第三方资料说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

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
