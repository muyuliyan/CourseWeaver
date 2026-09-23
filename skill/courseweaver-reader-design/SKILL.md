---
name: courseweaver-reader-design
description: Design or implement CourseWeaver's course-document reading workspace, including layout, typography, document rendering, reader controls, responsive behavior, and visual QA. Use when changing the inline reader in static/index.html, static/style.css, or static/app.js; do not use for the tutoring policy, retrieval logic, or server APIs unless the reader change requires a small compatible adjustment.
---

# CourseWeaver Reader Design

Make the course document the primary work surface while keeping the path to tutor help immediate. The result should feel like a calm academic reading tool, not a stack of dashboard cards or a text-file preview.

## Start With The Existing Product

Inspect `static/index.html`, `static/style.css`, `static/app.js`, the active course manifest, and representative Markdown or text materials before editing. Preserve CourseWeaver's dependency-light local architecture, material selection, chat flow, citations, and academic-integrity behavior.

Treat the current reader's form-feed-separated content as one possible input, not as the visual model. Detect the material's actual structure and render headings, paragraphs, lists, quotations, code, tables, and slide/page boundaries semantically. Keep all document text escaped or sanitized; never inject untrusted source text as raw HTML.

## Information Architecture

Use three functional zones on wide screens:

- A restrained 264-288 px course navigator on the left, with collection tabs and scannable material rows.
- A flexible reading canvas in the center, with a 680-760 px measure aligned to the viewport rather than placed in a decorative card.
- An optional 340-400 px tutor drawer on the right. Keep it closed until the learner asks a question or opens it explicitly; opening it must not cover the document on a wide screen.

Opening a material should replace the welcome state with the reading workspace. Do not confine the document to a short top panel above chat. Give the reader the available viewport height, place its own toolbar at the top, and preserve the document scroll position when the tutor drawer opens or closes.

On narrow screens, show one surface at a time: course list, reader, or tutor. Provide obvious back navigation and retain the selected material and reading position across transitions.

## Reader Chrome

Keep controls quiet and compact. The reader toolbar should contain the material title, useful metadata such as collection or reading progress, and familiar icon controls for closing/back, table of contents, typography settings, and tutor access. Use existing icon libraries when available; otherwise use accessible text only where a familiar symbol is insufficient. Every icon button needs an accessible name and tooltip.

Avoid decorative cards, pill-shaped labels, large shadows, and repeated boxes around sections. Use a paper-white reading canvas, a slightly cooler navigation background, hairline dividers, and one restrained green accent for selection and focus. Limit border radii to 8 px.

Provide the reading controls learners actually need:

- A table of contents derived from document headings when headings exist.
- Three text-size steps, comfortable by default, without viewport-scaled font sizes.
- A line-spacing control with compact, comfortable, and spacious choices.
- Reading progress and a return-to-top action for long documents.
- Keyboard-visible focus states and a reduced-motion path for any transitions.

Do not add feature-explainer copy to the interface. Controls should communicate through conventional placement, labels, icons, and tooltips.

## Typography

Use separate typographic roles rather than one font everywhere:

- UI and navigation: `Inter`, `Segoe UI`, `PingFang SC`, `Microsoft YaHei`, system sans-serif. Use 13-14 px for secondary UI and 15-16 px for primary controls.
- English reading text: prefer `Charter` or `Source Serif 4`, then `Georgia`, serif.
- Chinese reading text: prefer `Source Han Serif SC` or `Noto Serif CJK SC`, then `Songti SC`, `SimSun`, serif.
- Code: `SFMono-Regular`, `Cascadia Code`, `Consolas`, monospace.

Use language-aware font stacks when the course language is known. Do not fetch remote fonts by default; CourseWeaver is a local, privacy-conscious tool and must remain readable with system fallbacks.

Set document body text to 17-18 px on desktop and 16-17 px on mobile, line-height 1.72-1.82, and a maximum line length near 70 characters. Keep letter spacing at `0`. Use a compact sans-serif for metadata, a serif document title around 28-34 px, and clearly descending heading sizes. Paragraph spacing should reveal structure without turning every paragraph into a separate block.

Code blocks use a subtle neutral background, preserved whitespace, horizontal scrolling, and a smaller line-height. Inline code should remain visually distinct without bright badges.

## Behavior And States

Support loading, empty, error, and selected states without shifting the layout. Use skeleton lines or a quiet loading indicator inside a stable reader frame. Errors should explain the failed material and offer retry when practical.

When a learner invokes the tutor from the document, retain enough context to identify the active material. Selection-based questions are optional; if implemented, require an explicit action and show the exact quoted passage before sending it.

Preserve scroll position per material during the session. Update active navigation state without moving row dimensions. Ensure long titles truncate or wrap without colliding with controls.

## Visual And Accessibility Checks

Verify the finished workspace at desktop and mobile widths with short prose, long prose, headings, lists, code, and form-feed-separated slides. Confirm that:

- The first viewport prioritizes readable course content.
- No text or control overlaps at supported widths.
- The document remains usable at 200% browser zoom.
- Contrast, focus order, landmarks, and accessible names are coherent.
- Opening the tutor does not reset or unexpectedly obscure the reading position.
- Loading and dynamic content do not resize fixed controls or navigation rows.

Run the repository's existing tests after implementation. For visual changes, start the local server and inspect real screenshots at desktop and mobile sizes before declaring the work complete.
