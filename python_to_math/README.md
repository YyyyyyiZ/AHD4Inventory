# Python Policy to Math

This folder contains the inventory-policy-to-mathematics tooling:

- `policy_to_math.py`: AST-based translator and command-line interface.
- `generate_policy_pdf.py`: batch side-by-side HTML and PDF report generator.
- `policy_to_math_example.ipynb`: worked examples for recognized policy families.
- `sampled_policies/`: policy source files included in the batch report.
- `test_policy_to_math.py`: regression tests.
- `Archive.zip`: archived earlier notebook and test copies.

Use the compact renderer from Python:

```python
from python_to_math import policy_source_to_compact_math

latex = policy_source_to_compact_math(policy_source)
```

Run the tests from the repository root:

```bash
python3 -m unittest discover -s python_to_math -v
```

Generate the combined PDF report:

```bash
python3 -m python_to_math.generate_policy_pdf
```

Each sampled policy begins on a new landscape page. Long policies continue onto
additional pages with source-code line numbers. Recognized policy families use a
compact formula. Other policies use declarative equations: loops are rewritten
as summations when possible, branches use piecewise notation or conditional
equation systems, and stateful loops use recurrence notation. Displayed policy
constants are rounded to one decimal place for readability.

The PDF step uses headless Chrome and MathJax's `tex-svg.js` browser component
from the [MathJax CDN](https://docs.mathjax.org/en/latest/web/loading.html), so
network access is required for rendered formulas. To generate only the
inspectable HTML intermediate:

```bash
python3 -m python_to_math.generate_policy_pdf --html-only
```
