#!/usr/bin/env python3
"""Generate a side-by-side PDF report for sampled inventory policies.

The report is assembled as landscape HTML and printed with headless Chrome.
Policy source is parsed but never executed.
"""

from __future__ import annotations

import argparse
import html
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python_to_math.policy_to_math import (  # noqa: E402
    UnsupportedCompactPolicyError,
    policy_source_to_compact_math,
    policy_source_to_math,
)


DEFAULT_MATHJAX_URL = "https://cdn.jsdelivr.net/npm/mathjax@4/tex-svg.js"
DEFAULT_CHROME_PATHS = (
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
)


@dataclass(frozen=True)
class SourceChunk:
    start_line: int
    lines: tuple[str, ...]

    @property
    def end_line(self) -> int:
        return self.start_line + len(self.lines) - 1


@dataclass(frozen=True)
class FormulaChunk:
    latex: str
    start_row: int
    end_row: int


@dataclass(frozen=True)
class RenderedPolicy:
    path: Path
    source: str
    formula: str
    formula_mode: str
    metadata: dict[str, str]
    source_chunks: tuple[SourceChunk, ...]
    formula_chunks: tuple[FormulaChunk, ...]

    @property
    def page_count(self) -> int:
        return max(len(self.source_chunks), len(self.formula_chunks))


def _metadata_from_source(source: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in source.splitlines():
        if not line.startswith("# "):
            break
        key, separator, value = line[2:].partition(":")
        if separator:
            metadata[key.strip()] = value.strip()
    return metadata


def _source_visual_rows(line: str, characters_per_row: int) -> int:
    expanded = line.expandtabs(4)
    return max(1, math.ceil(max(1, len(expanded)) / characters_per_row))


def split_source(
    source: str,
    *,
    max_visual_rows: int = 46,
    characters_per_row: int = 102,
) -> tuple[SourceChunk, ...]:
    """Split source while accounting for wrapped long lines."""

    lines = source.rstrip().splitlines()
    if not lines:
        return (SourceChunk(start_line=1, lines=("",)),)

    chunks: list[SourceChunk] = []
    current: list[str] = []
    current_rows = 0
    current_start = 1
    for line_number, line in enumerate(lines, start=1):
        line_rows = _source_visual_rows(line, characters_per_row)
        if current and current_rows + line_rows > max_visual_rows:
            chunks.append(SourceChunk(start_line=current_start, lines=tuple(current)))
            current = []
            current_rows = 0
            current_start = line_number
        current.append(line)
        current_rows += line_rows
    if current:
        chunks.append(SourceChunk(start_line=current_start, lines=tuple(current)))
    return tuple(chunks)


def _aligned_rows(formula: str) -> list[str]:
    start_marker = r"\begin{aligned}"
    end_marker = r"\end{aligned}"
    start = formula.find(start_marker)
    end = formula.rfind(end_marker)
    if start == -1 or end == -1 or end <= start:
        return [formula.strip()]
    body = formula[start + len(start_marker) : end]
    return [line.strip() for line in body.splitlines() if line.strip()]


def split_formula(formula: str, *, max_rows: int = 22) -> tuple[FormulaChunk, ...]:
    """Split aligned LaTeX into independently renderable display chunks."""

    rows = _aligned_rows(formula)
    chunks = []
    for start in range(0, len(rows), max_rows):
        selected_rows = rows[start : start + max_rows]
        latex = "\\[\n\\begin{aligned}\n" + "\n".join(selected_rows) + "\n\\end{aligned}\n\\]"
        chunks.append(
            FormulaChunk(
                latex=latex,
                start_row=start + 1,
                end_row=start + len(selected_rows),
            )
        )
    return tuple(chunks)


def render_policy(path: Path) -> RenderedPolicy:
    source = path.read_text()
    try:
        formula = policy_source_to_compact_math(source)
        formula_mode = "compact"
    except UnsupportedCompactPolicyError:
        formula = policy_source_to_math(source)
        formula_mode = "declarative"
    return RenderedPolicy(
        path=path,
        source=source,
        formula=formula,
        formula_mode=formula_mode,
        metadata=_metadata_from_source(source),
        source_chunks=split_source(source),
        formula_chunks=split_formula(formula),
    )


def _render_source_lines(chunk: SourceChunk) -> str:
    items = []
    for line in chunk.lines:
        content = html.escape(line.expandtabs(4)) or " "
        items.append(f"<li><code>{content}</code></li>")
    return (
        f'<ol class="source-lines" start="{chunk.start_line}">'
        + "".join(items)
        + "</ol>"
    )


def _panel_repeat_note(index: int, count: int, label: str) -> str:
    if index < count:
        return ""
    return f'<p class="repeat-note">{html.escape(label)} repeated on this continuation page.</p>'


def _metadata_summary(policy: RenderedPolicy) -> str:
    parts = []
    for key in ("sample_id", "distribution", "generation", "objective", "test_objective"):
        value = policy.metadata.get(key)
        if value:
            parts.append(f"{key}: {value}")
    return " | ".join(parts)


def _render_policy_pages(policy: RenderedPolicy) -> str:
    pages = []
    source_count = len(policy.source_chunks)
    formula_count = len(policy.formula_chunks)
    for index in range(policy.page_count):
        source_chunk = policy.source_chunks[min(index, source_count - 1)]
        if policy.formula_mode == "compact":
            formula_chunk = policy.formula_chunks[0]
            formula_repeat = index > 0
        else:
            formula_chunk = policy.formula_chunks[min(index, formula_count - 1)]
            formula_repeat = index >= formula_count

        source_title = f"Python source lines {source_chunk.start_line}-{source_chunk.end_line}"
        formula_title = (
            "Compact mathematical formula"
            if policy.formula_mode == "compact"
            else f"Declarative mathematical formula rows {formula_chunk.start_row}-{formula_chunk.end_row}"
        )
        source_note = _panel_repeat_note(
            index,
            source_count,
            "The final source-code segment",
        )
        repeat_note = (
            '<p class="repeat-note">The compact formula is repeated for this source continuation.</p>'
            if formula_repeat and policy.formula_mode == "compact"
            else _panel_repeat_note(index, formula_count, "The final formula segment")
        )
        mode_note = (
            '<p class="mode-note">This policy is rendered as declarative equations. '
            "Reductions use summation notation and stateful updates use recurrences.</p>"
            if policy.formula_mode == "declarative"
            else ""
        )
        pages.append(
            f"""
<section class="report-page" data-policy="{html.escape(policy.path.name)}"
         data-policy-page="{index + 1}" data-render-mode="{policy.formula_mode}">
  <header class="page-header">
    <div>
      <h1>{html.escape(policy.path.name)}</h1>
      <p>{html.escape(_metadata_summary(policy))}</p>
    </div>
    <div class="page-number">Policy page {index + 1}/{policy.page_count}</div>
  </header>
  <main class="columns">
    <article class="panel source-panel">
      <h2>{source_title}</h2>
      {source_note}
      {_render_source_lines(source_chunk)}
    </article>
    <article class="panel formula-panel">
      <h2>{formula_title}</h2>
      {repeat_note}
      {mode_note}
      <div class="math-display">{html.escape(formula_chunk.latex)}</div>
    </article>
  </main>
</section>
"""
        )
    return "".join(pages)


def build_report_html(policies: list[RenderedPolicy], mathjax_url: str = DEFAULT_MATHJAX_URL) -> str:
    compact_count = sum(policy.formula_mode == "compact" for policy in policies)
    declarative_count = len(policies) - compact_count
    pages = "".join(_render_policy_pages(policy) for policy in policies)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Sampled inventory policies: Python source and mathematics</title>
  <style>
    @page {{ size: A4 landscape; margin: 0; }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; color: #17212b; font-family: Arial, sans-serif; }}
    .report-page {{
      width: 297mm; height: 210mm; padding: 8mm 9mm 7mm;
      break-after: page; page-break-after: always; overflow: hidden;
      display: flex; flex-direction: column; background: #fff;
    }}
    .report-page:last-child {{ break-after: auto; page-break-after: auto; }}
    .page-header {{
      min-height: 14mm; display: flex; justify-content: space-between; gap: 8mm;
      border-bottom: 0.4mm solid #1f5d7a; margin-bottom: 3mm; padding-bottom: 2mm;
    }}
    h1 {{ font-size: 11pt; margin: 0 0 1mm; color: #123e57; }}
    .page-header p {{ font-size: 6.8pt; margin: 0; color: #52606d; }}
    .page-number {{ font-size: 7pt; color: #52606d; white-space: nowrap; }}
    .columns {{ flex: 1; min-height: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }}
    .panel {{
      min-width: 0; overflow: hidden; border: 0.25mm solid #c8d2d9;
      border-radius: 1.5mm; padding: 2.5mm; background: #fbfcfd;
    }}
    h2 {{ font-size: 8.5pt; margin: 0 0 1.8mm; color: #28546b; }}
    .source-lines {{
      margin: 0; padding-left: 6mm; font: 5.8pt/1.27 Menlo, Monaco, "Courier New", monospace;
      white-space: pre-wrap; overflow-wrap: anywhere;
    }}
    .source-lines li {{ padding-left: 0.8mm; }}
    .source-lines li::marker {{ color: #7b8794; }}
    .repeat-note, .mode-note {{
      margin: 0 0 1.3mm; padding: 1mm 1.4mm; border-radius: 1mm;
      font-size: 6.3pt; line-height: 1.25; color: #4a5562; background: #eef4f7;
    }}
    .mode-note {{ background: #fff8e7; color: #71541c; }}
    .math-display {{ font-size: 7.4pt; line-height: 1.12; color: #101820; }}
    mjx-container[jax="SVG"] {{ margin: 0 !important; max-width: 100%; text-align: left !important; }}
    mjx-container[jax="SVG"] > svg {{ max-width: 100%; height: auto; }}
  </style>
  <script>
    window.MathJax = {{
      svg: {{ fontCache: "global" }},
      startup: {{
        pageReady: () => MathJax.startup.defaultPageReady().then(() => {{
          document.body.dataset.mathReady = "true";
        }})
      }}
    }};
  </script>
  <script defer id="MathJax-script" src="{html.escape(mathjax_url)}"></script>
</head>
<body data-policy-count="{len(policies)}" data-compact-count="{compact_count}"
      data-declarative-count="{declarative_count}">
{pages}
</body>
</html>
"""


def find_chrome(explicit_path: str | None = None) -> Path:
    candidates = []
    if explicit_path:
        candidates.append(Path(explicit_path).expanduser())
    env_path = os.environ.get("CHROME_PATH")
    if env_path:
        candidates.append(Path(env_path).expanduser())
    candidates.extend(DEFAULT_CHROME_PATHS)
    for command in ("google-chrome", "chromium", "chromium-browser"):
        executable = shutil.which(command)
        if executable:
            candidates.append(Path(executable))
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError("Could not find Chrome. Pass --chrome-path or set CHROME_PATH.")


def _chrome_base_command(chrome: Path, profile_dir: Path, virtual_time_budget_ms: int) -> list[str]:
    return [
        str(chrome),
        "--headless=new",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--allow-file-access-from-files",
        "--run-all-compositor-stages-before-draw",
        f"--virtual-time-budget={virtual_time_budget_ms}",
        f"--user-data-dir={profile_dir}",
    ]


def _check_mathjax_url(mathjax_url: str) -> None:
    request = urllib.request.Request(mathjax_url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status >= 400:
                raise RuntimeError(f"MathJax CDN returned HTTP {response.status}")
    except (OSError, urllib.error.URLError) as error:
        raise RuntimeError(
            "Could not reach the MathJax CDN. Check network access or rerun with "
            "--allow-unrendered-math to print the raw LaTeX fallback."
        ) from error


def print_html_to_pdf(
    html_path: Path,
    pdf_path: Path,
    *,
    chrome_path: str | None = None,
    mathjax_url: str = DEFAULT_MATHJAX_URL,
    virtual_time_budget_ms: int = 60_000,
    allow_unrendered_math: bool = False,
) -> None:
    chrome = find_chrome(chrome_path)
    html_uri = html_path.resolve().as_uri()
    pdf_path = pdf_path.resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.unlink(missing_ok=True)
    if not allow_unrendered_math:
        _check_mathjax_url(mathjax_url)
    with tempfile.TemporaryDirectory(prefix="python-to-math-chrome-") as profile:
        profile_dir = Path(profile)
        base_command = _chrome_base_command(chrome, profile_dir, virtual_time_budget_ms)
        with tempfile.TemporaryFile(mode="w+") as chrome_log:
            process = subprocess.Popen(
                [
                    *base_command,
                    "--no-pdf-header-footer",
                    "--print-to-pdf-no-header",
                    f"--print-to-pdf={pdf_path}",
                    html_uri,
                ],
                stdout=chrome_log,
                stderr=subprocess.STDOUT,
                text=True,
            )
            deadline = time.monotonic() + 300
            previous_size = -1
            stable_checks = 0
            completed_pdf = False
            while process.poll() is None and time.monotonic() < deadline:
                size = pdf_path.stat().st_size if pdf_path.is_file() else 0
                if size > 0 and size == previous_size:
                    stable_checks += 1
                else:
                    stable_checks = 0
                    previous_size = size
                if stable_checks >= 5:
                    completed_pdf = True
                    process.terminate()
                    break
                time.sleep(1)
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
            if not completed_pdf and pdf_path.is_file() and pdf_path.stat().st_size > 0:
                completed_pdf = True
            if not completed_pdf:
                chrome_log.seek(0)
                details = chrome_log.read().strip()
                raise RuntimeError(f"Chrome failed to create {pdf_path}: {details}")


def generate_report(
    policies_dir: Path,
    html_output: Path,
    pdf_output: Path | None,
    *,
    mathjax_url: str = DEFAULT_MATHJAX_URL,
    chrome_path: str | None = None,
    virtual_time_budget_ms: int = 60_000,
    allow_unrendered_math: bool = False,
) -> list[RenderedPolicy]:
    paths = sorted(policies_dir.glob("*.py"))
    if not paths:
        raise FileNotFoundError(f"No Python policies found in {policies_dir}")
    policies = [render_policy(path) for path in paths]
    html_output.parent.mkdir(parents=True, exist_ok=True)
    html_output.write_text(build_report_html(policies, mathjax_url=mathjax_url))
    if pdf_output is not None:
        print_html_to_pdf(
            html_output,
            pdf_output,
            chrome_path=chrome_path,
            mathjax_url=mathjax_url,
            virtual_time_budget_ms=virtual_time_budget_ms,
            allow_unrendered_math=allow_unrendered_math,
        )
    return policies


def _parse_args() -> argparse.Namespace:
    folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Generate a side-by-side PDF of sampled Python policies and mathematical formulas."
    )
    parser.add_argument(
        "--policies-dir",
        type=Path,
        default=folder / "sampled_policies",
        help="folder containing sampled .py policies",
    )
    parser.add_argument(
        "--html-output",
        type=Path,
        default=folder / "sampled_policy_math_report.html",
        help="intermediate HTML report path",
    )
    parser.add_argument(
        "--pdf-output",
        type=Path,
        default=folder / "sampled_policy_math_report.pdf",
        help="PDF report path",
    )
    parser.add_argument("--html-only", action="store_true", help="write HTML without invoking Chrome")
    parser.add_argument("--chrome-path", help="Chrome executable path")
    parser.add_argument("--mathjax-url", default=DEFAULT_MATHJAX_URL, help="MathJax tex-svg.js URL")
    parser.add_argument(
        "--virtual-time-budget-ms",
        type=int,
        default=60_000,
        help="Chrome virtual time budget for MathJax rendering",
    )
    parser.add_argument(
        "--allow-unrendered-math",
        action="store_true",
        help="print raw LaTeX if MathJax cannot be loaded",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    policies = generate_report(
        args.policies_dir,
        args.html_output,
        None if args.html_only else args.pdf_output,
        mathjax_url=args.mathjax_url,
        chrome_path=args.chrome_path,
        virtual_time_budget_ms=args.virtual_time_budget_ms,
        allow_unrendered_math=args.allow_unrendered_math,
    )
    page_count = sum(policy.page_count for policy in policies)
    compact_count = sum(policy.formula_mode == "compact" for policy in policies)
    declarative_count = len(policies) - compact_count
    print(f"Policies: {len(policies)}")
    print(f"Pages: {page_count}")
    print(f"Compact formulas: {compact_count}")
    print(f"Declarative formulas: {declarative_count}")
    print(f"HTML: {args.html_output.resolve()}")
    if not args.html_only:
        print(f"PDF: {args.pdf_output.resolve()}")


if __name__ == "__main__":
    main()
