from __future__ import annotations

import html
import json
import re
from pathlib import Path

from nbconvert.filters.markdown_mistune import markdown2html_mistune


ROOT = Path(__file__).resolve().parent
NOTEBOOK_PATH = ROOT / "steam_narrative_viz.ipynb"
OUTPUT_PATH = ROOT / "steam_narrative_viz.html"
SAVE_PATTERN = re.compile(r"""\.save\(\s*['"]([^'"]+\.html)['"]\s*\)""")
HTML_REPLACEMENTS = {
    "chart1.html": "scene1_flood.html",
}
CUSTOM_HTML_BY_CELL_INDEX = {
    6: "scene2_attention_gap.html",
    8: "scene3_survivor_simulator.html",
    10: "scene4_winner_takes_all.html",
    12: "scene5_disappearing_middle.html",
    14: "scene6_genre_resilience.html",
    16: "scene7_survivor_portrait.html",
}
CUSTOM_HTML_HEIGHT_BY_NAME = {
    "scene1_flood.html": 760,
    "scene2_attention_gap.html": 860,
    "scene3_survivor_simulator.html": 980,
    "scene4_winner_takes_all.html": 930,
    "scene5_disappearing_middle.html": 900,
    "scene6_genre_resilience.html": 980,
    "scene7_survivor_portrait.html": 980,
}


def clean_markdown_html(markdown_text: str) -> str:
    rendered = markdown2html_mistune(markdown_text)
    rendered = re.sub(r'<a class="anchor-link" href="[^"]*">&#182;</a>', "", rendered)
    return rendered


def collect_story_blocks(notebook: dict) -> list[str]:
    blocks: list[str] = []

    for idx, cell in enumerate(notebook.get("cells", [])):
        cell_type = cell.get("cell_type")

        if cell_type == "markdown":
            source = "".join(cell.get("source", []))
            if source.strip():
                blocks.append(f'<section class="story-block prose">{clean_markdown_html(source)}</section>')
            continue

        if cell_type != "code":
            continue

        custom_html_name = CUSTOM_HTML_BY_CELL_INDEX.get(idx)
        if custom_html_name:
            custom_html_path = (ROOT / custom_html_name).resolve()
            if custom_html_path.exists():
                blocks.append(
                    '<section class="story-block viz-block">'
                    '<div class="viz-frame saved-html-frame">'
                    f'<iframe src="{html.escape(custom_html_path.name)}" title="{html.escape(custom_html_path.stem)}" loading="lazy" style="height:{CUSTOM_HTML_HEIGHT_BY_NAME.get(custom_html_name, 720)}px"></iframe>'
                    "</div></section>"
                )
                continue

        outputs = cell.get("outputs", [])
        html_outputs: list[str] = []
        text_outputs: list[str] = []

        for output in outputs:
            data = output.get("data", {})
            html_data = data.get("text/html")
            plain_data = data.get("text/plain")

            if html_data:
                html_outputs.append("".join(html_data) if isinstance(html_data, list) else str(html_data))
            elif plain_data and output.get("output_type") != "stream":
                text_outputs.append("".join(plain_data) if isinstance(plain_data, list) else str(plain_data))

        source = "".join(cell.get("source", []))
        saved_html_files: list[str] = []

        if html_outputs:
            blocks.append(
                '<section class="story-block viz-block">'
                + "".join(f'<div class="viz-frame">{chunk}</div>' for chunk in html_outputs)
                + "</section>"
            )
        else:
            saved_html_files = SAVE_PATTERN.findall(source)
            iframe_blocks: list[str] = []

            for filename in saved_html_files:
                preferred_name = HTML_REPLACEMENTS.get(filename, filename)
                html_path = (ROOT / preferred_name).resolve()
                if html_path.exists():
                    iframe_blocks.append(
                        '<div class="viz-frame saved-html-frame">'
                        f'<iframe src="{html.escape(html_path.name)}" title="{html.escape(html_path.stem)}" loading="lazy" style="height:{CUSTOM_HTML_HEIGHT_BY_NAME.get(preferred_name, 720)}px"></iframe>'
                        "</div>"
                    )

            if iframe_blocks:
                blocks.append('<section class="story-block viz-block">' + "".join(iframe_blocks) + "</section>")
        if (not html_outputs) and (not saved_html_files) and text_outputs:
            safe_text = "\n\n".join(html.escape(text) for text in text_outputs)
            blocks.append(f'<section class="story-block text-output"><pre>{safe_text}</pre></section>')

    return blocks


def build_document(blocks: list[str]) -> str:
    body = "\n".join(blocks)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Steam Narrative Visualization</title>
  <style>
    :root {{
      --bg: #f7f4ee;
      --paper: #fffdf8;
      --ink: #1f2933;
      --muted: #52606d;
      --line: rgba(31, 41, 51, 0.12);
      --shadow: 0 18px 48px rgba(31, 41, 51, 0.08);
    }}

    * {{
      box-sizing: border-box;
    }}

    html {{
      scroll-behavior: smooth;
    }}

    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top, rgba(42, 157, 143, 0.10), transparent 32%),
        linear-gradient(180deg, #faf7f2 0%, var(--bg) 100%);
      line-height: 1.7;
    }}

    main {{
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 40px 0 72px;
    }}

    .story-block {{
      width: 100%;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 22px;
      box-shadow: var(--shadow);
      padding: 28px 32px;
      margin: 0 0 26px;
      overflow: hidden;
    }}

    .prose hr {{
      border: 0;
      border-top: 1px solid var(--line);
      margin: 1.5rem 0;
    }}

    .prose h1,
    .prose h2,
    .prose h3 {{
      line-height: 1.2;
      margin: 0 0 0.8rem;
      color: #102a43;
    }}

    .prose h1 {{
      font-size: clamp(2.2rem, 4vw, 3.6rem);
    }}

    .prose h2 {{
      font-size: clamp(1.5rem, 2.6vw, 2.2rem);
      margin-top: 0.2rem;
    }}

    .prose h3 {{
      font-size: 1.15rem;
      color: var(--muted);
    }}

    .prose p,
    .prose blockquote,
    .prose ul {{
      font-size: 1.05rem;
      margin: 0 0 1rem;
    }}

    .prose blockquote {{
      margin: 1.2rem 0;
      padding: 0.2rem 0 0.2rem 1rem;
      border-left: 4px solid #2a9d8f;
      color: #334e68;
      font-style: italic;
    }}

    .prose ul {{
      padding-left: 1.2rem;
    }}

    .viz-block {{
      padding: 22px;
    }}

    .viz-frame {{
      width: 100%;
      overflow-x: auto;
    }}

    .viz-frame > div:first-child {{
      width: 100%;
    }}

    .saved-html-frame {{
      border-radius: 16px;
      border: 1px solid var(--line);
      background: #ffffff;
      padding: 8px;
    }}

    .saved-html-frame iframe {{
      width: 100%;
      min-height: 720px;
      border: 0;
      display: block;
      background: #ffffff;
    }}

    .text-output pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: Consolas, "SFMono-Regular", monospace;
      font-size: 0.95rem;
    }}

    @media (max-width: 800px) {{
      main {{
        width: min(100vw - 18px, 100%);
        padding: 18px 0 44px;
      }}

      .story-block {{
        border-radius: 16px;
        padding: 18px 16px;
        margin-bottom: 18px;
      }}

      .viz-block {{
        padding: 12px 8px;
      }}

      .saved-html-frame iframe {{
        min-height: 620px;
      }}

    }}
  </style>
</head>
<body>
  <main>
    {body}
  </main>
</body>
</html>
"""


def main() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    blocks = collect_story_blocks(notebook)
    OUTPUT_PATH.write_text(build_document(blocks), encoding="utf-8")
    print(f"Exported HTML to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
