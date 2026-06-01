import tempfile
import unittest
from pathlib import Path

from python_to_math.generate_policy_pdf import (
    build_report_html,
    generate_report,
    render_policy,
    split_source,
)


FOLDER = Path(__file__).resolve().parent
SAMPLED_POLICIES = FOLDER / "sampled_policies"


class GeneratePolicyPdfTests(unittest.TestCase):
    def test_long_source_is_split_into_continuation_pages(self):
        source = "\n".join(f"value_{index} = {index}" for index in range(130))

        chunks = split_source(source, max_visual_rows=20)

        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].start_line, 1)
        self.assertEqual(chunks[-1].end_line, 130)

    def test_render_policy_uses_compact_and_declarative_modes(self):
        compact = render_policy(next(SAMPLED_POLICIES.glob("sample_001*.py")))
        declarative = render_policy(next(SAMPLED_POLICIES.glob("sample_005*.py")))

        self.assertEqual(compact.formula_mode, "compact")
        self.assertIn(r"H_L=\sum_{i=1}^{L}\frac{1}{i}", compact.formula)
        self.assertEqual(declarative.formula_mode, "declarative")
        self.assertIn(r"\mathrm{weighted\_pipeline\_sum} = \sum_{i=0}^{L-1}", declarative.formula)
        self.assertNotIn(r"\text{for }", declarative.formula)

    def test_html_only_report_contains_every_sampled_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            html_output = Path(folder) / "report.html"

            policies = generate_report(SAMPLED_POLICIES, html_output, None)
            report = html_output.read_text()

        self.assertEqual(len(policies), 100)
        self.assertEqual(report.count('data-policy="'), sum(policy.page_count for policy in policies))
        self.assertIn('data-policy-count="100"', report)
        self.assertIn('data-render-mode="compact"', report)
        self.assertIn('data-render-mode="declarative"', report)
        self.assertIn("source continuation", report)

        formulas = "\n".join(policy.formula for policy in policies)
        self.assertNotIn(r"\text{for }", formulas)
        self.assertNotIn(r"\textbf{for", formulas)
        self.assertNotIn(r"\gets", formulas)
        self.assertNotIn(r"\operatorname{enumerate}", formulas)

    def test_html_loads_mathjax_svg_renderer(self):
        policy = render_policy(next(SAMPLED_POLICIES.glob("sample_003*.py")))

        report = build_report_html([policy])

        self.assertIn("https://cdn.jsdelivr.net/npm/mathjax@4/tex-svg.js", report)
        self.assertIn('document.body.dataset.mathReady = "true"', report)


if __name__ == "__main__":
    unittest.main()
