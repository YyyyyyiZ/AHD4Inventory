#!/usr/bin/env python3
"""Render an inventory policy as compact LaTeX or structured mathematics.

The translator parses policy source code without executing it.  It intentionally
keeps some loops and branches explicit when a policy-specific compact formula is
not available, because an arbitrary Python function does not necessarily have a
useful single closed-form representation.
"""

from __future__ import annotations

import argparse
import ast
import copy
import inspect
import re
import sys
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import Any


class UnsupportedSyntaxError(ValueError):
    """Raised when structured mathematical rendering is not implemented for a node."""


class UnsupportedCompactPolicyError(ValueError):
    """Raised when a policy has no implemented compact mathematical renderer."""


DEFAULT_SYMBOL_ALIASES = {
    "on_hand_inventory": "h",
    "pipeline_orders": r"\mathbf{q}",
}

_COMPACT_PIPELINE_PARAMETERS = (
    "base_stock",
    "safety_stock",
    "anticipation_factor",
    "smoothing_factor",
    "min_order",
    "max_order",
    "urgency_factor",
    "urgency_threshold",
    "coverage_periods",
    "cost_ratio_factor",
    "pattern_weight",
    "risk_sensitivity",
)

_COMPACT_PIPELINE_POLICY_TEMPLATE = """
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 0
    safety_stock = 0
    anticipation_factor = 0
    smoothing_factor = 0
    min_order = 0
    max_order = 0
    urgency_factor = 0
    urgency_threshold = 0
    coverage_periods = 0
    cost_ratio_factor = 0
    pattern_weight = 0
    risk_sensitivity = 0
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    weighted_demand_estimate = 0
    total_weight = 0
    L = len(pipeline_orders)
    for i, q in enumerate(pipeline_orders):
        weight = (L - i) / L
        weighted_demand_estimate += q * weight
        total_weight += weight
    if total_weight > 0:
        avg_weighted_demand = weighted_demand_estimate / total_weight
    else:
        avg_weighted_demand = 100.0
    if L >= 3:
        recent_trend = 0
        for i in range(L - 1):
            if pipeline_orders[i + 1] > pipeline_orders[i]:
                recent_trend += 1
            elif pipeline_orders[i + 1] < pipeline_orders[i]:
                recent_trend -= 1
        trend_factor = 1.0 + (recent_trend / L) * pattern_weight
        pattern_adjusted_demand = avg_weighted_demand * trend_factor
    else:
        pattern_adjusted_demand = avg_weighted_demand
    adjusted_base_stock = base_stock + anticipation_factor * (pattern_adjusted_demand - 100.0)
    near_pipeline = sum(pipeline_orders[:min(2, L)])
    if near_pipeline < urgency_threshold:
        urgency_adjustment = 1.0 + (urgency_threshold - near_pipeline) / urgency_threshold * (urgency_factor - 1.0)
        adjusted_base_stock *= urgency_adjustment
    lead_time_demand = pattern_adjusted_demand * L
    coverage_adjustment = lead_time_demand * coverage_periods
    final_base_stock = max(adjusted_base_stock, coverage_adjustment)
    risk_adjustment = 1.0 + (risk_sensitivity * (1.0 - min(1.0, inventory_position / final_base_stock)))
    final_base_stock *= risk_adjustment
    cost_adjusted_base_stock = final_base_stock * cost_ratio_factor
    target_inventory_position = cost_adjusted_base_stock + safety_stock
    raw_order = max(0, target_inventory_position - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * min_order
    bounded_order = max(min_order, min(max_order, smoothed_order))
    order_amount = int(round(bounded_order))
    return order_amount
"""

_COMPACT_BOUNDED_BASE_STOCK_PARAMETERS = (
    "base_stock",
    "safety_stock",
    "demand_forecast",
)

_COMPACT_BOUNDED_BASE_STOCK_POLICY_TEMPLATE = """
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 0
    safety_stock = 0
    demand_forecast = 0
    lead_time = len(pipeline_orders)
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    expected_lead_time_demand = demand_forecast * lead_time
    target_inventory = expected_lead_time_demand + safety_stock
    order_amount = max(0, target_inventory - inventory_position)
    order_amount = min(order_amount, max(0, base_stock - inventory_position))
    return order_amount
"""

_COMPACT_RECIPROCAL_PIPELINE_PARAMETERS = (
    "base_stock",
    "demand_anticipation_factor",
    "recent_demand_weight",
    "pipeline_urgency_factor",
    "holding_cost_weight",
    "lost_sales_cost_weight",
    "smoothing_factor",
    "min_order_size",
    "safety_stock",
    "safety_adjustment_factor",
    "lost_sales_multiplier",
)

_COMPACT_RECIPROCAL_PIPELINE_POLICY_TEMPLATE = """
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 0
    demand_anticipation_factor = 0
    recent_demand_weight = 0
    pipeline_urgency_factor = 0
    holding_cost_weight = 0
    lost_sales_cost_weight = 0
    smoothing_factor = 0
    min_order_size = 0
    safety_stock = 0
    safety_adjustment_factor = 0
    lost_sales_multiplier = 0
    L = len(pipeline_orders)
    if L > 0:
        weighted_pipeline = 0.0
        total_weight = 0.0
        for i, q in enumerate(pipeline_orders):
            weight = 1.0 / (1.0 + i)
            weighted_pipeline += q * weight
            total_weight += weight
        effective_pipeline = weighted_pipeline / total_weight if total_weight > 0 else sum(pipeline_orders)
        pipeline_urgency = 0.0
        if L >= 2:
            near_pipeline = sum(pipeline_orders[:L // 2])
            far_pipeline = sum(pipeline_orders[L // 2 :])
            total_pipeline = near_pipeline + far_pipeline
            if total_pipeline > 0:
                pipeline_urgency = far_pipeline / total_pipeline
    else:
        effective_pipeline = 0.0
        pipeline_urgency = 0.0
    inventory_position = on_hand_inventory + effective_pipeline
    dynamic_safety_stock = base_stock * (1.0 + pipeline_urgency * pipeline_urgency_factor)
    safety_adjusted_level = dynamic_safety_stock
    if inventory_position < safety_stock:
        deficit_ratio = max(0, (safety_stock - inventory_position) / max(1, safety_stock))
        adjustment = safety_adjustment_factor * (1.0 + deficit_ratio * lost_sales_multiplier)
        safety_adjusted_level += adjustment
    cost_ratio = lost_sales_cost_weight / holding_cost_weight
    cost_balanced_level = safety_adjusted_level * (1.0 + demand_anticipation_factor * (cost_ratio - 1.0))
    raw_order = max(0.0, cost_balanced_level - inventory_position)
    urgency_adjusted_smoothing = smoothing_factor * (1.0 - pipeline_urgency * 0.5)
    smoothed_order = raw_order * urgency_adjusted_smoothing
    if smoothed_order < min_order_size:
        smoothed_order = 0.0
    order_amount = int(round(smoothed_order))
    return order_amount
"""


def _escape_latex(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "{": r"\{",
        "}": r"\}",
        "$": r"\$",
    }
    return "".join(replacements.get(char, char) for char in value)


def _format_compact_constant(value: int | float) -> str:
    """Format policy parameters with one digit after the decimal point."""

    return f"{value:.1f}"


def _identifier(name: str, aliases: dict[str, str]) -> str:
    if name in aliases:
        return aliases[name]
    if len(name) == 1 and name.isalpha():
        return name
    return rf"\mathrm{{{_escape_latex(name)}}}"


def _node_location(node: ast.AST) -> str:
    line = getattr(node, "lineno", None)
    return f" on line {line}" if line is not None else ""


def _find_policy_function(
    source: str,
    function_name: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    try:
        module = ast.parse(textwrap.dedent(source))
    except SyntaxError as error:
        raise ValueError(f"Could not parse policy source: {error}") from error

    functions = [
        node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name
    ]
    if not functions:
        raise ValueError(f"Could not find a top-level function named {function_name!r}")
    if len(functions) > 1:
        raise ValueError(f"Found more than one top-level function named {function_name!r}")
    return functions[0]


def _opt_parameter_names(source: str) -> set[str]:
    pattern = re.compile(r"^\s*([A-Za-z_]\w*)\s*=.*#\s*OPT_PARAM:", re.MULTILINE)
    return set(pattern.findall(source))


class _ExpressionRenderer(ast.NodeVisitor):
    """Convert Python expressions to LaTeX while preserving Python semantics."""

    _binary_operators = {
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: r"\cdot",
        ast.MatMult: r"\mathbin{@}",
        ast.Mod: r"\bmod",
        ast.LShift: r"\ll",
        ast.RShift: r"\gg",
        ast.BitOr: r"\mathbin{|}",
        ast.BitXor: r"\oplus",
        ast.BitAnd: r"\mathbin{\&}",
    }
    _comparison_operators = {
        ast.Eq: "=",
        ast.NotEq: r"\ne",
        ast.Lt: "<",
        ast.LtE: r"\le",
        ast.Gt: ">",
        ast.GtE: r"\ge",
        ast.Is: r"\mathrel{\mathrm{is}}",
        ast.IsNot: r"\mathrel{\mathrm{is\ not}}",
        ast.In: r"\in",
        ast.NotIn: r"\notin",
    }

    def __init__(self, aliases: dict[str, str], notes: set[str]) -> None:
        self.aliases = aliases
        self.notes = notes

    def render(self, node: ast.AST) -> str:
        return self.visit(node)

    def generic_visit(self, node: ast.AST) -> str:
        raise UnsupportedSyntaxError(
            f"Unsupported expression {type(node).__name__}{_node_location(node)}"
        )

    def visit_Name(self, node: ast.Name) -> str:
        return _identifier(node.id, self.aliases)

    def visit_Constant(self, node: ast.Constant) -> str:
        if node.value is None:
            return r"\mathrm{None}"
        if node.value is True:
            return r"\mathrm{True}"
        if node.value is False:
            return r"\mathrm{False}"
        if isinstance(node.value, str):
            return rf"\text{{{_escape_latex(node.value)}}}"
        if isinstance(node.value, float):
            if node.value != 0 and abs(node.value) < 0.05:
                return f"{node.value:.1e}"
            return _format_compact_constant(node.value)
        return repr(node.value)

    def visit_BinOp(self, node: ast.BinOp) -> str:
        left = self.render(node.left)
        right = self.render(node.right)
        if isinstance(node.op, ast.Div):
            return rf"\frac{{{left}}}{{{right}}}"
        if isinstance(node.op, ast.FloorDiv):
            return rf"\left\lfloor\frac{{{left}}}{{{right}}}\right\rfloor"
        if isinstance(node.op, ast.Pow):
            return rf"\left({left}\right)^{{{right}}}"
        operator = self._binary_operators.get(type(node.op))
        if operator is None:
            raise UnsupportedSyntaxError(
                f"Unsupported operator {type(node.op).__name__}{_node_location(node)}"
            )
        return rf"\left({left} {operator} {right}\right)"

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        operand = self.render(node.operand)
        if isinstance(node.op, ast.USub):
            return rf"-\left({operand}\right)"
        if isinstance(node.op, ast.UAdd):
            return rf"+\left({operand}\right)"
        if isinstance(node.op, ast.Not):
            return rf"\neg\left({operand}\right)"
        if isinstance(node.op, ast.Invert):
            return rf"\mathord{{\sim}}\left({operand}\right)"
        raise UnsupportedSyntaxError(
            f"Unsupported unary operator {type(node.op).__name__}{_node_location(node)}"
        )

    def visit_BoolOp(self, node: ast.BoolOp) -> str:
        operator = r"\land" if isinstance(node.op, ast.And) else r"\lor"
        return rf"\left({' {} '.format(operator).join(self.render(v) for v in node.values)}\right)"

    def visit_Compare(self, node: ast.Compare) -> str:
        chunks = [self.render(node.left)]
        for operator_node, comparator in zip(node.ops, node.comparators):
            operator = self._comparison_operators.get(type(operator_node))
            if operator is None:
                raise UnsupportedSyntaxError(
                    "Unsupported comparison "
                    f"{type(operator_node).__name__}{_node_location(node)}"
                )
            chunks.extend((operator, self.render(comparator)))
        return " ".join(chunks)

    def visit_IfExp(self, node: ast.IfExp) -> str:
        return (
            r"\begin{cases}"
            rf"{self.render(node.body)}, & {self.render(node.test)} \\ "
            rf"{self.render(node.orelse)}, & \text{{otherwise}}"
            r"\end{cases}"
        )

    def visit_Attribute(self, node: ast.Attribute) -> str:
        return rf"{self.render(node.value)}.\mathrm{{{_escape_latex(node.attr)}}}"

    def visit_Subscript(self, node: ast.Subscript) -> str:
        if isinstance(node.value, ast.Name) and node.value.id == "pipeline_orders":
            return rf"q_{{{self.render(node.slice)}}}"
        return rf"{self.render(node.value)}_{{{self.render(node.slice)}}}"

    def visit_Slice(self, node: ast.Slice) -> str:
        lower = self.render(node.lower) if node.lower is not None else ""
        upper = self.render(node.upper) if node.upper is not None else ""
        if node.step is None:
            return f"{lower}:{upper}"
        return f"{lower}:{upper}:{self.render(node.step)}"

    def visit_Tuple(self, node: ast.Tuple) -> str:
        return rf"\left({', '.join(self.render(element) for element in node.elts)}\right)"

    def visit_List(self, node: ast.List) -> str:
        return rf"\left[{', '.join(self.render(element) for element in node.elts)}\right]"

    def visit_Set(self, node: ast.Set) -> str:
        return rf"\left\{{{', '.join(self.render(element) for element in node.elts)}\right\}}"

    def visit_Dict(self, node: ast.Dict) -> str:
        pairs = (
            f"{self.render(key)}: {self.render(value)}"
            for key, value in zip(node.keys, node.values)
            if key is not None
        )
        return rf"\left\{{{', '.join(pairs)}\right\}}"

    def visit_Starred(self, node: ast.Starred) -> str:
        return rf"*{self.render(node.value)}"

    def visit_Lambda(self, node: ast.Lambda) -> str:
        arguments = ", ".join(_identifier(arg.arg, self.aliases) for arg in node.args.args)
        return rf"\left({arguments} \mapsto {self.render(node.body)}\right)"

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> str:
        return self._render_comprehension(node.elt, node.generators, r"\left\{", r"\right\}")

    def visit_ListComp(self, node: ast.ListComp) -> str:
        return self._render_comprehension(node.elt, node.generators, r"\left[", r"\right]")

    def visit_SetComp(self, node: ast.SetComp) -> str:
        return self._render_comprehension(node.elt, node.generators, r"\left\{", r"\right\}")

    def _render_comprehension(
        self,
        element: ast.AST,
        generators: list[ast.comprehension],
        left_delimiter: str,
        right_delimiter: str,
    ) -> str:
        clauses = self._comprehension_clauses(generators)
        return rf"{left_delimiter}{self.render(element)} \mid {clauses}{right_delimiter}"

    def _comprehension_clauses(self, generators: list[ast.comprehension]) -> str:
        clauses: list[str] = []
        for generator in generators:
            if generator.is_async:
                raise UnsupportedSyntaxError("Async comprehensions are not supported")
            clauses.append(f"{self.render(generator.target)} \\in {self.render(generator.iter)}")
            clauses.extend(self.render(condition) for condition in generator.ifs)
        return ", ".join(clauses)

    def visit_Call(self, node: ast.Call) -> str:
        name = self._python_call_name(node.func)
        short_name = name.rsplit(".", maxsplit=1)[-1] if name is not None else None

        if short_name == "sum" and len(node.args) == 1:
            rendered_sum = self._render_sum(node.args[0])
            if rendered_sum is not None:
                return rendered_sum

        arguments = [self.render(argument) for argument in node.args]
        arguments.extend(
            rf"\mathrm{{{_escape_latex(keyword.arg or '**')}}}={self.render(keyword.value)}"
            for keyword in node.keywords
        )
        rendered_arguments = ", ".join(arguments)

        if short_name in {"min", "max"}:
            return rf"\{short_name}\left({rendered_arguments}\right)"
        if short_name == "abs":
            return rf"\left|{rendered_arguments}\right|"
        if short_name == "sqrt" and len(arguments) == 1:
            return rf"\sqrt{{{arguments[0]}}}"
        if short_name == "len" and len(arguments) == 1:
            if isinstance(node.args[0], ast.Name) and node.args[0].id == "pipeline_orders":
                return "L"
            return rf"\operatorname{{len}}\left({arguments[0]}\right)"
        if short_name == "round" and len(arguments) == 1 and not node.keywords:
            return rf"\operatorname{{round}}_{{\mathrm{{even}}}}\left({arguments[0]}\right)"
        if (
            short_name == "int"
            and len(node.args) == 1
            and not node.keywords
            and isinstance(node.args[0], ast.Call)
            and self._python_call_name(node.args[0].func) == "round"
        ):
            return self.render(node.args[0])

        operator_name = self._operator_name(node.func, name)
        if name is not None and short_name not in {
            "enumerate",
            "range",
            "round",
            "int",
            "float",
            "sum",
            "mean",
            "std",
            "quantile",
            "log",
            "exp",
            "ceil",
            "floor",
            "diff",
            "array",
        }:
            self.notes.add(
                f"Call '{name}' is preserved as an uninterpreted mathematical operator."
            )
        return rf"\operatorname{{{operator_name}}}\left({rendered_arguments}\right)"

    def _operator_name(self, function: ast.AST, python_name: str | None) -> str:
        if python_name is not None:
            return _escape_latex(python_name)
        return _escape_latex(ast.unparse(function))

    def _render_sum(self, argument: ast.AST) -> str | None:
        if isinstance(argument, ast.GeneratorExp):
            indexed_sum = self._render_indexed_generator_sum(argument)
            if indexed_sum is not None:
                return indexed_sum
            clauses = self._comprehension_clauses(argument.generators)
            return rf"\sum_{{{clauses}}} {self.render(argument.elt)}"

        sequence_sum = self._render_pipeline_slice_sum(argument)
        if sequence_sum is not None:
            return sequence_sum
        return None

    def _render_indexed_generator_sum(self, generator: ast.GeneratorExp) -> str | None:
        if len(generator.generators) != 1:
            return None
        comprehension = generator.generators[0]
        if comprehension.ifs or comprehension.is_async:
            return None
        if (
            isinstance(comprehension.iter, ast.Call)
            and isinstance(comprehension.iter.func, ast.Name)
            and comprehension.iter.func.id == "enumerate"
            and len(comprehension.iter.args) == 1
            and isinstance(comprehension.target, ast.Tuple)
            and len(comprehension.target.elts) == 2
            and all(isinstance(element, ast.Name) for element in comprehension.target.elts)
        ):
            sequence = comprehension.iter.args[0]
            if isinstance(sequence, ast.Name) and sequence.id == "pipeline_orders":
                pipeline_value = lambda index: rf"q_{{{index}}}"
            elif (
                isinstance(sequence, ast.Call)
                and isinstance(sequence.func, ast.Name)
                and sequence.func.id == "reversed"
                and len(sequence.args) == 1
                and isinstance(sequence.args[0], ast.Name)
                and sequence.args[0].id == "pipeline_orders"
            ):
                pipeline_value = lambda index: rf"q_{{L-1-{index}}}"
            else:
                return None
            index_name = comprehension.target.elts[0].id
            value_name = comprehension.target.elts[1].id
            renderer = _ExpressionRenderer(
                {
                    **self.aliases,
                    index_name: index_name,
                    value_name: pipeline_value(index_name),
                },
                self.notes,
            )
            return rf"\sum_{{{index_name}=0}}^{{L-1}} {renderer.render(generator.elt)}"
        return None

    def _render_pipeline_slice_sum(self, argument: ast.AST) -> str | None:
        sequence_name = self._pipeline_sequence_name(argument)
        if sequence_name is not None:
            return r"\sum_{i=0}^{L-1} q_i"

        if (
            isinstance(argument, ast.Subscript)
            and isinstance(argument.value, ast.Name)
            and argument.value.id == "pipeline_orders"
            and isinstance(argument.slice, ast.Slice)
        ):
            start = self._slice_start(argument.slice.lower)
            end = self._slice_end(argument.slice.upper)
            return rf"\sum_{{i={start}}}^{{{end}}} q_i"
        return None

    def _pipeline_sequence_name(self, argument: ast.AST) -> str | None:
        if isinstance(argument, ast.Name) and argument.id == "pipeline_orders":
            return argument.id
        return None

    def _slice_start(self, lower: ast.AST | None) -> str:
        if lower is None:
            return "0"
        if isinstance(lower, ast.Constant) and lower.value == 0:
            return "0"
        if isinstance(lower, ast.UnaryOp) and isinstance(lower.op, ast.USub):
            return rf"L-\left({self.render(lower.operand)}\right)"
        return self.render(lower)

    def _slice_end(self, upper: ast.AST | None) -> str:
        if upper is None:
            return r"L-1"
        return rf"\left({self.render(upper)}\right)-1"

    def _python_call_name(self, function: ast.AST) -> str | None:
        if isinstance(function, ast.Name):
            return function.id
        if isinstance(function, ast.Attribute):
            parent = self._python_call_name(function.value)
            return f"{parent}.{function.attr}" if parent is not None else function.attr
        return None


class _PolicyRenderer:
    """Render statements from one policy function as structured mathematics."""

    def __init__(
        self,
        function: ast.FunctionDef | ast.AsyncFunctionDef,
        parameter_names: set[str] | None = None,
    ) -> None:
        self.function = function
        self.parameter_names = parameter_names or set()
        self.notes: set[str] = {
            "This is a structured mathematical transcription, not necessarily a single closed-form expression.",
            "Indices and slices retain Python's zero-based and negative-index semantics.",
        }
        self.aliases = dict(DEFAULT_SYMBOL_ALIASES)
        self.expression = _ExpressionRenderer(self.aliases, self.notes)
        self.function_lhs = self._function_lhs()
        self.latest_values: dict[str, str] = {}

    def render(self) -> str:
        if isinstance(self.function, ast.AsyncFunctionDef):
            raise UnsupportedSyntaxError("Async policy functions are not supported")

        lines = [rf"\text{{Inputs: }} {self._inputs()}"]
        loop_initializer_lines = self._zero_loop_initializer_lines(self.function.body)
        for statement in self.function.body:
            parameter = self._literal_parameter_assignment(statement)
            if parameter is not None:
                name, value = parameter
                rendered_value = self.expression.render(value)
                self.latest_values[name] = rendered_value
                self.aliases[name] = rendered_value
                continue
            if getattr(statement, "lineno", None) in loop_initializer_lines:
                self._remember_assignment(statement.targets, self.expression.render(statement.value))
                continue
            lines.extend(self._render_statement(statement, indent=0))

        aligned_lines = " \\\\\n".join(f"&{line}" for line in lines)
        note_lines = "\n".join(f"% - {note}" for note in sorted(self.notes))
        return (
            "% Mathematical policy generated from Python source.\n"
            "% Notes:\n"
            f"{note_lines}\n"
            "\\[\n"
            "\\begin{aligned}\n"
            f"{aligned_lines}\n"
            "\\end{aligned}\n"
            "\\]"
        )

    def _function_lhs(self) -> str:
        arguments = ", ".join(
            _identifier(argument.arg, self.aliases) for argument in self.function.args.args
        )
        return rf"Q\left({arguments}\right)"

    def _inputs(self) -> str:
        return r"h=\text{on-hand inventory},\quad \mathbf{q}=(q_0,\ldots,q_{L-1})"

    def _render_statement(self, statement: ast.stmt, indent: int) -> list[str]:
        prefix = r"\quad " * indent
        expression = self.expression

        piecewise_line = self._render_if_as_piecewise(statement, prefix)
        if piecewise_line is not None:
            return [piecewise_line]

        if isinstance(statement, ast.Assign):
            targets = [self._render_target(target) for target in statement.targets]
            value = expression.render(statement.value)
            self._remember_assignment(statement.targets, value)
            if len(targets) == 1 and targets[0] == value:
                return []
            return [f"{prefix}{' = '.join(targets)} = {value}"]
        if isinstance(statement, ast.AnnAssign):
            value = expression.render(statement.value)
            self._remember_assignment([statement.target], value)
            return [
                f"{prefix}{self._render_target(statement.target)}"
                rf" = {value}"
            ]
        if isinstance(statement, ast.AugAssign):
            target = self._render_target(statement.target)
            operator = expression.render(
                ast.BinOp(left=statement.target, op=statement.op, right=statement.value)
            )
            self._remember_assignment([statement.target], operator)
            return [f"{prefix}{target} = {operator}"]
        if isinstance(statement, ast.If):
            condition = expression.render(statement.test)
            lines = [self._render_conditional_system(statement.body, condition, prefix)]
            if statement.orelse:
                lines.append(
                    self._render_conditional_system(
                        statement.orelse,
                        rf"\neg\left({condition}\right)",
                        prefix,
                    )
                )
            return lines
        if isinstance(statement, (ast.For, ast.AsyncFor)):
            if isinstance(statement, ast.AsyncFor):
                raise UnsupportedSyntaxError("Async loops are not supported")
            return self._render_for_as_math(statement, prefix)
        if isinstance(statement, ast.While):
            lines = [rf"{prefix}\text{{while }} {expression.render(statement.test)}"]
            lines.extend(self._render_block(statement.body, indent + 1))
            if statement.orelse:
                lines.append(rf"{prefix}\text{{if the loop completes}}")
                lines.extend(self._render_block(statement.orelse, indent + 1))
            return lines
        if isinstance(statement, ast.Return):
            value = r"\mathrm{None}" if statement.value is None else expression.render(statement.value)
            return [rf"{prefix}\boxed{{{self.function_lhs} = {value}}}"]
        if isinstance(statement, ast.Expr):
            if isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                return []
            return [rf"{prefix}{expression.render(statement.value)}"]
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            self.notes.add("Import statements are omitted; referenced functions remain visible as operators.")
            return []
        if isinstance(statement, ast.Assert):
            return [rf"{prefix}\text{{require }} {expression.render(statement.test)}"]
        if isinstance(statement, ast.Pass):
            return [rf"{prefix}\text{{pass}}"]
        if isinstance(statement, ast.Break):
            return [rf"{prefix}\text{{break}}"]
        if isinstance(statement, ast.Continue):
            return [rf"{prefix}\text{{continue}}"]
        raise UnsupportedSyntaxError(
            f"Unsupported statement {type(statement).__name__}{_node_location(statement)}"
        )

    def _remember_assignment(self, targets: list[ast.expr], value: str) -> None:
        for target in targets:
            if isinstance(target, ast.Name):
                self.latest_values[target.id] = value
                if target.id not in DEFAULT_SYMBOL_ALIASES:
                    self.aliases.pop(target.id, None)

    def _render_target(self, target: ast.expr) -> str:
        if isinstance(target, ast.Name):
            return _identifier(target.id, DEFAULT_SYMBOL_ALIASES)
        return self.expression.render(target)

    def _literal_parameter_assignment(
        self,
        statement: ast.stmt,
    ) -> tuple[str, ast.Constant] | None:
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id in self.parameter_names
            and isinstance(statement.value, ast.Constant)
            and not isinstance(statement.value.value, (bool, str))
            and isinstance(statement.value.value, (int, float))
        ):
            return statement.targets[0].id, statement.value
        return None

    def _zero_loop_initializer_lines(
        self,
        statements: list[ast.stmt],
    ) -> set[int]:
        lines: set[int] = set()
        for index, statement in enumerate(statements):
            if not isinstance(statement, ast.For):
                continue
            augmented_names = {
                node.target.id
                for node in ast.walk(statement)
                if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name)
            }
            previous_index = index - 1
            while previous_index >= 0:
                previous = statements[previous_index]
                if (
                    not isinstance(previous, ast.Assign)
                    or len(previous.targets) != 1
                    or not isinstance(previous.targets[0], ast.Name)
                    or not isinstance(previous.value, ast.Constant)
                    or previous.value.value not in {0, 0.0}
                ):
                    break
                if previous.targets[0].id in augmented_names:
                    lines.add(previous.lineno)
                previous_index -= 1
        return lines

    def _render_block(self, statements: list[ast.stmt], indent: int) -> list[str]:
        lines: list[str] = []
        for statement in statements:
            lines.extend(self._render_statement(statement, indent))
        return lines

    def _render_conditional_system(
        self,
        statements: list[ast.stmt],
        condition: str,
        prefix: str,
    ) -> str:
        equations = self._render_block(statements, indent=0)
        body = r" \\ ".join(equations) or r"\text{no change}"
        return (
            rf"{prefix}\left.\begin{{gathered}}{body}\end{{gathered}}"
            rf"\right\}}\quad \left({condition}\right)"
        )

    def _render_for_as_math(self, statement: ast.For, prefix: str) -> list[str]:
        domain, loop_aliases, index_symbol = self._loop_context(statement)
        reductions = self._loop_reductions(
            statement.body,
            domain=domain,
            loop_aliases=loop_aliases,
            index_symbol=index_symbol,
        )
        if reductions is not None and not statement.orelse:
            lines = []
            for accumulator, terms in reductions.items():
                target = _identifier(accumulator, self.aliases)
                initial = self.latest_values.get(accumulator, "0")
                summand = " + ".join(terms)
                total = rf"{self._sum_operator(domain)}\left({summand}\right)"
                if initial not in {"0", "0.0"}:
                    total = rf"{initial}+{total}"
                lines.append(rf"{prefix}{target} = {total}")
                self.latest_values[accumulator] = target
            return lines

        recurrence_expression = _ExpressionRenderer(
            {**self.aliases, **loop_aliases},
            self.notes,
        )
        previous_expression = self.expression
        self.expression = recurrence_expression
        try:
            equations = self._render_block(statement.body, indent=0)
        finally:
            self.expression = previous_expression
        body = r" \\ ".join(equations) or r"\text{no change}"
        lines = [
            rf"{prefix}\left.\begin{{gathered}}{body}\end{{gathered}}"
            rf"\right\}}\quad \left({domain};\ \text{{recurrence}}\right)"
        ]
        if statement.orelse:
            lines.extend(self._render_block(statement.orelse, indent=0))
        return lines

    def _sum_operator(self, domain: str) -> str:
        separator = r",\ldots,"
        if "=" in domain and separator in domain:
            lower, upper = domain.split(separator, maxsplit=1)
            return rf"\sum_{{{lower}}}^{{{upper}}}"
        return rf"\sum_{{{domain}}}"

    def _loop_context(self, statement: ast.For) -> tuple[str, dict[str, str], str]:
        iterator = statement.iter
        target = statement.target

        if (
            isinstance(iterator, ast.Call)
            and isinstance(iterator.func, ast.Name)
            and iterator.func.id == "enumerate"
            and len(iterator.args) == 1
            and isinstance(target, ast.Tuple)
            and len(target.elts) == 2
            and all(isinstance(element, ast.Name) for element in target.elts)
        ):
            index_name = target.elts[0].id
            value_name = target.elts[1].id
            sequence = iterator.args[0]
            rendered_sequence = self.expression.render(sequence)
            length = "L" if self._is_pipeline_orders(sequence) else rf"\left|{rendered_sequence}\right|"
            value = (
                rf"q_{{{index_name}}}"
                if self._is_pipeline_orders(sequence)
                else rf"\left({rendered_sequence}\right)_{{{index_name}}}"
            )
            return (
                rf"{index_name}=0,\ldots,{length}-1",
                {index_name: index_name, value_name: value},
                index_name,
            )

        if (
            isinstance(iterator, ast.Call)
            and isinstance(iterator.func, ast.Name)
            and iterator.func.id == "range"
            and isinstance(target, ast.Name)
        ):
            index_name = target.id
            if len(iterator.args) == 1:
                lower = "0"
                upper = rf"{self.expression.render(iterator.args[0])}-1"
            elif len(iterator.args) == 2:
                lower = self.expression.render(iterator.args[0])
                upper = rf"{self.expression.render(iterator.args[1])}-1"
            else:
                return (
                    rf"{index_name}\in\operatorname{{range}}\left("
                    rf"{', '.join(self.expression.render(arg) for arg in iterator.args)}\right)",
                    {index_name: index_name},
                    index_name,
                )
            return (
                rf"{index_name}={lower},\ldots,{upper}",
                {index_name: index_name},
                index_name,
            )

        if self._is_pipeline_orders(iterator) and isinstance(target, ast.Name):
            return (
                "i=0,\ldots,L-1",
                {target.id: "q_i"},
                "i",
            )

        rendered_iterator = self.expression.render(iterator)
        rendered_target = self.expression.render(target)
        return (
            rf"{rendered_target}\in {rendered_iterator}",
            {},
            "i",
        )

    def _is_pipeline_orders(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Name) and node.id == "pipeline_orders"

    def _loop_reductions(
        self,
        statements: list[ast.stmt],
        *,
        domain: str,
        loop_aliases: dict[str, str],
        index_symbol: str,
    ) -> dict[str, list[str]] | None:
        del domain
        local_aliases = dict(loop_aliases)
        multiplier_targets = self._loop_multiplier_aliases(
            statements,
            local_aliases=local_aliases,
            index_symbol=index_symbol,
        )
        reductions: dict[str, list[str]] = {}
        if not self._collect_loop_reductions(
            statements,
            reductions=reductions,
            local_aliases=local_aliases,
            multiplier_targets=multiplier_targets,
            condition=None,
        ):
            return None
        return reductions or None

    def _loop_multiplier_aliases(
        self,
        statements: list[ast.stmt],
        *,
        local_aliases: dict[str, str],
        index_symbol: str,
    ) -> set[str]:
        targets: set[str] = set()
        for statement in statements:
            if (
                isinstance(statement, ast.AugAssign)
                and isinstance(statement.op, ast.Mult)
                and isinstance(statement.target, ast.Name)
            ):
                name = statement.target.id
                factor = self._render_loop_expression(statement.value, local_aliases)
                initial = self.latest_values.get(name, _identifier(name, self.aliases))
                local_aliases[name] = rf"\left({initial}\right)\left({factor}\right)^{{{index_symbol}}}"
                targets.add(name)
        return targets

    def _collect_loop_reductions(
        self,
        statements: list[ast.stmt],
        *,
        reductions: dict[str, list[str]],
        local_aliases: dict[str, str],
        multiplier_targets: set[str],
        condition: str | None,
    ) -> bool:
        for statement in statements:
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
                target = statement.targets[0]
                if not isinstance(target, ast.Name) or target.id in self.latest_values:
                    return False
                local_aliases[target.id] = self._render_loop_expression(
                    statement.value,
                    local_aliases,
                )
                continue

            if isinstance(statement, ast.AugAssign) and isinstance(statement.target, ast.Name):
                name = statement.target.id
                if isinstance(statement.op, ast.Mult) and name in multiplier_targets:
                    continue
                if not isinstance(statement.op, (ast.Add, ast.Sub)):
                    return False
                term = self._render_loop_expression(statement.value, local_aliases)
                if isinstance(statement.op, ast.Sub):
                    term = rf"-\left({term}\right)"
                if condition is not None:
                    term = rf"\mathbf{{1}}_{{\{{{condition}\}}}}\left({term}\right)"
                reductions.setdefault(name, []).append(term)
                continue

            if isinstance(statement, ast.If):
                rendered_condition = self._render_loop_expression(statement.test, local_aliases)
                if not self._collect_loop_reductions(
                    statement.body,
                    reductions=reductions,
                    local_aliases=dict(local_aliases),
                    multiplier_targets=multiplier_targets,
                    condition=self._combine_conditions(condition, rendered_condition),
                ):
                    return False
                if statement.orelse and not self._collect_loop_reductions(
                    statement.orelse,
                    reductions=reductions,
                    local_aliases=dict(local_aliases),
                    multiplier_targets=multiplier_targets,
                    condition=self._combine_conditions(
                        condition,
                        rf"\neg\left({rendered_condition}\right)",
                    ),
                ):
                    return False
                continue

            return False
        return True

    def _render_loop_expression(self, node: ast.AST, local_aliases: dict[str, str]) -> str:
        return _ExpressionRenderer(
            {**self.aliases, **local_aliases},
            self.notes,
        ).render(node)

    def _combine_conditions(self, outer: str | None, inner: str) -> str:
        if outer is None:
            return inner
        return rf"\left({outer}\right)\land\left({inner}\right)"

    def _render_if_as_piecewise(self, statement: ast.stmt, prefix: str) -> str | None:
        if not isinstance(statement, ast.If):
            return None

        body_assignment = self._assignment_like(statement.body)
        else_assignment = self._assignment_like(statement.orelse) if statement.orelse else None

        if body_assignment is None:
            return None

        target, body_value = body_assignment
        condition = self.expression.render(statement.test)

        if else_assignment is not None:
            else_target, else_value = else_assignment
            if else_target != target:
                return None
            return (
                rf"{prefix}{target} = \begin{{cases}}"
                rf"{body_value}, & {condition} \\ "
                rf"{else_value}, & \text{{otherwise}}"
                r"\end{cases}"
            )

        if statement.orelse:
            return None

        return (
            rf"{prefix}{target} = \begin{{cases}}"
            rf"{body_value}, & {condition} \\ "
            rf"{target}, & \text{{otherwise}}"
            r"\end{cases}"
        )

    def _assignment_like(self, statements: list[ast.stmt]) -> tuple[str, str] | None:
        if len(statements) != 1:
            return None

        statement = statements[0]
        expression = self.expression
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            return self._render_target(statement.targets[0]), expression.render(statement.value)
        if isinstance(statement, ast.AnnAssign) and statement.value is not None:
            return self._render_target(statement.target), expression.render(statement.value)
        if isinstance(statement, ast.AugAssign):
            target = self._render_target(statement.target)
            value = expression.render(
                ast.BinOp(left=statement.target, op=statement.op, right=statement.value)
            )
            return target, value
        return None


def _normalise_parameterised_function(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parameter_names: tuple[str, ...],
) -> str:
    function_copy = copy.deepcopy(function)
    for statement in ast.walk(function_copy):
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id in parameter_names
        ):
            statement.value = ast.Constant(value=0)
    body = ast.Module(body=function_copy.body, type_ignores=[])
    return ast.dump(body, include_attributes=False)


def _compact_pipeline_parameters(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, int | float]:
    if isinstance(function, ast.AsyncFunctionDef):
        raise UnsupportedCompactPolicyError("Async policy functions are not supported")
    arguments = [argument.arg for argument in function.args.args]
    if arguments != ["on_hand_inventory", "pipeline_orders"]:
        raise UnsupportedCompactPolicyError(
            "Compact rendering requires inputs named on_hand_inventory and pipeline_orders"
        )

    parameters: dict[str, int | float] = {}
    for statement in function.body:
        if (
            not isinstance(statement, ast.Assign)
            or len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
            or statement.targets[0].id not in _COMPACT_PIPELINE_PARAMETERS
        ):
            continue
        name = statement.targets[0].id
        if name in parameters:
            raise UnsupportedCompactPolicyError(f"Parameter {name!r} is assigned more than once")
        try:
            value = ast.literal_eval(statement.value)
        except ValueError as error:
            raise UnsupportedCompactPolicyError(
                f"Parameter {name!r} must be a numeric literal"
            ) from error
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise UnsupportedCompactPolicyError(f"Parameter {name!r} must be a numeric literal")
        parameters[name] = value

    missing = sorted(set(_COMPACT_PIPELINE_PARAMETERS) - parameters.keys())
    if missing:
        raise UnsupportedCompactPolicyError(
            f"Compact rendering does not recognize this policy; missing parameters: {missing}"
        )

    template = _find_policy_function(
        _COMPACT_PIPELINE_POLICY_TEMPLATE,
        function_name="compute_order_amount",
    )
    if _normalise_parameterised_function(
        function,
        _COMPACT_PIPELINE_PARAMETERS,
    ) != _normalise_parameterised_function(template, _COMPACT_PIPELINE_PARAMETERS):
        raise UnsupportedCompactPolicyError(
            "Compact rendering does not recognize this policy structure. "
            "Use policy_source_to_math() for the structured fallback."
        )
    return parameters


def _compact_pipeline_formula(parameters: dict[str, int | float]) -> str:
    base_stock = _format_compact_constant(parameters["base_stock"])
    safety_stock = _format_compact_constant(parameters["safety_stock"])
    anticipation_factor = _format_compact_constant(parameters["anticipation_factor"])
    smoothing_factor = _format_compact_constant(parameters["smoothing_factor"])
    min_order = _format_compact_constant(parameters["min_order"])
    max_order = _format_compact_constant(parameters["max_order"])
    urgency_factor = _format_compact_constant(parameters["urgency_factor"])
    urgency_threshold = _format_compact_constant(parameters["urgency_threshold"])
    coverage_periods = _format_compact_constant(parameters["coverage_periods"])
    cost_ratio_factor = _format_compact_constant(parameters["cost_ratio_factor"])
    pattern_weight = _format_compact_constant(parameters["pattern_weight"])
    risk_sensitivity = _format_compact_constant(parameters["risk_sensitivity"])
    return (
        "% Compact mathematical representation of the recognized inventory policy.\n"
        "% Policy constants are rounded to one decimal place for readability.\n"
        "% round_even means Python's nearest-integer rounding, with ties rounded to even.\n"
        "\\[\n"
        "\\begin{aligned}\n"
        r"&\text{Inputs: } h=\text{on-hand inventory},\quad "
        r"\mathbf{q}=(q_1,\ldots,q_L)=\text{pipeline orders}. \\"
        "\n"
        r"&I = h+\sum_{i=1}^{L}q_i "
        r"\qquad \text{(inventory position)}. \\[3pt]"
        "\n"
        r"&\bar d ="
        r"\begin{cases}"
        r"\displaystyle \frac{2}{L(L+1)}\sum_{i=1}^{L}(L-i+1)q_i, & L>0, \\"
        r"100, & L=0"
        r"\end{cases}"
        r"\qquad \text{(weighted pipeline-demand estimate)}. \\[6pt]"
        "\n"
        r"&s=\sum_{i=1}^{L-1}\operatorname{sgn}(q_{i+1}-q_i)"
        r"\qquad \text{(pipeline trend score)}. \\[3pt]"
        "\n"
        r"&d="
        r"\begin{cases}"
        rf"\bar d\left(1+\dfrac{{{pattern_weight}}}{{L}}s\right), & L\ge 3, \\"
        r"\bar d, & L<3"
        r"\end{cases}"
        r"\qquad \text{(trend-adjusted demand estimate)}. \\[6pt]"
        "\n"
        r"&n=\sum_{i=1}^{\min(2,L)}q_i"
        r"\qquad \text{(near-term pipeline)}. \\[3pt]"
        "\n"
        r"&u(n)="
        r"\begin{cases}"
        rf"1+\dfrac{{{urgency_threshold}-n}}{{{urgency_threshold}}}"
        rf"\left({urgency_factor}-1\right), & n<{urgency_threshold}, \\"
        rf"1, & n\ge {urgency_threshold}"
        r"\end{cases}"
        r"\qquad \text{(urgency multiplier)}. \\[6pt]"
        "\n"
        rf"&B=u(n)\left[{base_stock}+{anticipation_factor}(d-100)\right]. \\[3pt]"
        "\n"
        rf"&G=\max\left(B,\;{coverage_periods}Ld\right). \\[3pt]"
        "\n"
        rf"&R=G\left[1+{risk_sensitivity}"
        r"\left(1-\min\left(1,\frac{I}{G}\right)\right)\right]. \\[3pt]"
        "\n"
        rf"&T={cost_ratio_factor}R+{safety_stock}"
        r"\qquad \text{(target inventory position)}. \\[6pt]"
        "\n"
        rf"&\operatorname{{clip}}_{{[{min_order},{max_order}]}}(x)"
        rf"=\max\left({min_order},\min\left({max_order},x\right)\right). \\[3pt]"
        "\n"
        rf"&\boxed{{Q(h,\mathbf{{q}})=\operatorname{{round}}_{{\mathrm{{even}}}}"
        rf"\left(\operatorname{{clip}}_{{[{min_order},{max_order}]}}"
        rf"\left({smoothing_factor}\max(0,T-I)"
        rf"+(1-{smoothing_factor}){min_order}\right)\right)}}."
        "\n"
        "\\end{aligned}\n"
        "\\]"
    )


def _compact_bounded_base_stock_parameters(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, int | float]:
    if isinstance(function, ast.AsyncFunctionDef):
        raise UnsupportedCompactPolicyError("Async policy functions are not supported")
    arguments = [argument.arg for argument in function.args.args]
    if arguments != ["on_hand_inventory", "pipeline_orders"]:
        raise UnsupportedCompactPolicyError(
            "Compact rendering requires inputs named on_hand_inventory and pipeline_orders"
        )

    parameters: dict[str, int | float] = {}
    for statement in function.body:
        if (
            not isinstance(statement, ast.Assign)
            or len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
            or statement.targets[0].id not in _COMPACT_BOUNDED_BASE_STOCK_PARAMETERS
        ):
            continue
        name = statement.targets[0].id
        if name in parameters:
            raise UnsupportedCompactPolicyError(f"Parameter {name!r} is assigned more than once")
        try:
            value = ast.literal_eval(statement.value)
        except (TypeError, ValueError) as error:
            raise UnsupportedCompactPolicyError(
                f"Parameter {name!r} must be a numeric literal"
            ) from error
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise UnsupportedCompactPolicyError(f"Parameter {name!r} must be a numeric literal")
        parameters[name] = value

    missing = sorted(set(_COMPACT_BOUNDED_BASE_STOCK_PARAMETERS) - parameters.keys())
    if missing:
        raise UnsupportedCompactPolicyError(
            f"Compact rendering does not recognize this policy; missing parameters: {missing}"
        )

    template = _find_policy_function(
        _COMPACT_BOUNDED_BASE_STOCK_POLICY_TEMPLATE,
        function_name="compute_order_amount",
    )
    if _normalise_parameterised_function(
        function,
        _COMPACT_BOUNDED_BASE_STOCK_PARAMETERS,
    ) != _normalise_parameterised_function(template, _COMPACT_BOUNDED_BASE_STOCK_PARAMETERS):
        raise UnsupportedCompactPolicyError(
            "Compact rendering does not recognize this policy structure. "
            "Use policy_source_to_math() for the structured fallback."
        )
    return parameters


def _compact_bounded_base_stock_formula(parameters: dict[str, int | float]) -> str:
    base_stock = _format_compact_constant(parameters["base_stock"])
    safety_stock = _format_compact_constant(parameters["safety_stock"])
    demand_forecast = _format_compact_constant(parameters["demand_forecast"])
    return (
        "% Compact mathematical representation of the recognized inventory policy.\n"
        "% Policy constants are rounded to one decimal place for readability.\n"
        "% [x]^+ means max(0, x).\n"
        "\\[\n"
        "\\begin{aligned}\n"
        r"&\text{Inputs: } h=\text{on-hand inventory},\quad "
        r"\mathbf{q}=(q_1,\ldots,q_L)=\text{pipeline orders}. \\"
        "\n"
        r"&I(h,\mathbf{q})=h+\sum_{i=1}^{L}q_i"
        r"\qquad \text{(inventory position)}. \\[3pt]"
        "\n"
        rf"&T(L)={demand_forecast}L+{safety_stock}"
        r"\qquad \text{(lead-time demand plus safety stock)}. \\[3pt]"
        "\n"
        r"&[x]^+=\max(0,x). \\[3pt]"
        "\n"
        rf"&\boxed{{Q(h,\mathbf{{q}})="
        rf"\left[\min\left({base_stock},T(L)\right)-I(h,\mathbf{{q}})\right]^+}}."
        "\n"
        "\\end{aligned}\n"
        "\\]"
    )


def _compact_reciprocal_pipeline_parameters(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, int | float]:
    if isinstance(function, ast.AsyncFunctionDef):
        raise UnsupportedCompactPolicyError("Async policy functions are not supported")
    arguments = [argument.arg for argument in function.args.args]
    if arguments != ["on_hand_inventory", "pipeline_orders"]:
        raise UnsupportedCompactPolicyError(
            "Compact rendering requires inputs named on_hand_inventory and pipeline_orders"
        )

    parameters: dict[str, int | float] = {}
    for statement in function.body:
        if (
            not isinstance(statement, ast.Assign)
            or len(statement.targets) != 1
            or not isinstance(statement.targets[0], ast.Name)
            or statement.targets[0].id not in _COMPACT_RECIPROCAL_PIPELINE_PARAMETERS
        ):
            continue
        name = statement.targets[0].id
        if name in parameters:
            raise UnsupportedCompactPolicyError(f"Parameter {name!r} is assigned more than once")
        try:
            value = ast.literal_eval(statement.value)
        except (TypeError, ValueError) as error:
            raise UnsupportedCompactPolicyError(
                f"Parameter {name!r} must be a numeric literal"
            ) from error
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise UnsupportedCompactPolicyError(f"Parameter {name!r} must be a numeric literal")
        parameters[name] = value

    missing = sorted(set(_COMPACT_RECIPROCAL_PIPELINE_PARAMETERS) - parameters.keys())
    if missing:
        raise UnsupportedCompactPolicyError(
            f"Compact rendering does not recognize this policy; missing parameters: {missing}"
        )

    template = _find_policy_function(
        _COMPACT_RECIPROCAL_PIPELINE_POLICY_TEMPLATE,
        function_name="compute_order_amount",
    )
    if _normalise_parameterised_function(
        function,
        _COMPACT_RECIPROCAL_PIPELINE_PARAMETERS,
    ) != _normalise_parameterised_function(
        template,
        _COMPACT_RECIPROCAL_PIPELINE_PARAMETERS,
    ):
        raise UnsupportedCompactPolicyError(
            "Compact rendering does not recognize this policy structure. "
            "Use policy_source_to_math() for the structured fallback."
        )
    return parameters


def _compact_reciprocal_pipeline_formula(parameters: dict[str, int | float]) -> str:
    base_stock = _format_compact_constant(parameters["base_stock"])
    demand_anticipation_factor = _format_compact_constant(
        parameters["demand_anticipation_factor"]
    )
    pipeline_urgency_factor = _format_compact_constant(parameters["pipeline_urgency_factor"])
    holding_cost_weight = _format_compact_constant(parameters["holding_cost_weight"])
    lost_sales_cost_weight = _format_compact_constant(parameters["lost_sales_cost_weight"])
    smoothing_factor = _format_compact_constant(parameters["smoothing_factor"])
    min_order_size = _format_compact_constant(parameters["min_order_size"])
    safety_stock = _format_compact_constant(parameters["safety_stock"])
    safety_adjustment_factor = _format_compact_constant(parameters["safety_adjustment_factor"])
    lost_sales_multiplier = _format_compact_constant(parameters["lost_sales_multiplier"])
    safety_denominator = (
        safety_stock
        if parameters["safety_stock"] >= 1
        else rf"\max\left(1,{safety_stock}\right)"
    )
    return (
        "% Compact mathematical representation of the recognized inventory policy.\n"
        "% Policy constants are rounded to one decimal place for readability.\n"
        "% round_even means Python's nearest-integer rounding, with ties rounded to even.\n"
        "% recent_demand_weight is omitted because it is assigned in the Python code but never used.\n"
        "\\[\n"
        "\\begin{aligned}\n"
        r"&\text{Inputs: } h=\text{on-hand inventory},\quad "
        r"\mathbf{q}=(q_1,\ldots,q_L)=\text{pipeline orders}. \\"
        "\n"
        r"&[x]^+=\max(0,x). \\[3pt]"
        "\n"
        r"&H_L=\sum_{i=1}^{L}\frac{1}{i}. \\[3pt]"
        "\n"
        r"&e(\mathbf{q})="
        r"\begin{cases}"
        r"\displaystyle \frac{\sum_{i=1}^{L}q_i/i}{H_L}, & L>0, \\"
        r"0, & L=0"
        r"\end{cases}"
        r"\qquad \text{(reciprocal-weighted pipeline)}. \\[6pt]"
        "\n"
        r"&u(\mathbf{q})="
        r"\begin{cases}"
        r"\displaystyle \frac{\sum_{i=\lfloor L/2\rfloor+1}^{L}q_i}{\sum_{i=1}^{L}q_i},"
        r" & L\ge 2 \text{ and } \sum_{i=1}^{L}q_i>0, \\"
        r"0, & \text{otherwise}"
        r"\end{cases}"
        r"\qquad \text{(share of pipeline arriving later)}. \\[6pt]"
        "\n"
        r"&I(h,\mathbf{q})=h+e(\mathbf{q}). \\[3pt]"
        "\n"
        rf"&D_0(\mathbf{{q}})={base_stock}\left(1+{pipeline_urgency_factor}u(\mathbf{{q}})\right)."
        r" \\[3pt]"
        "\n"
        rf"&A(h,\mathbf{{q}})="
        r"\begin{cases}"
        rf"{safety_adjustment_factor}\left(1+{lost_sales_multiplier}"
        rf"\dfrac{{{safety_stock}-I(h,\mathbf{{q}})}}{{{safety_denominator}}}\right),"
        rf" & I(h,\mathbf{{q}})<{safety_stock}, \\"
        r"0, & I(h,\mathbf{q})\ge "
        rf"{safety_stock}"
        r"\end{cases}"
        r"\qquad \text{(shortage boost)}. \\[6pt]"
        "\n"
        rf"&T(h,\mathbf{{q}})=\left(D_0(\mathbf{{q}})+A(h,\mathbf{{q}})\right)"
        rf"\left[1+{demand_anticipation_factor}"
        rf"\left(\frac{{{lost_sales_cost_weight}}}{{{holding_cost_weight}}}-1\right)\right]."
        r" \\[3pt]"
        "\n"
        rf"&x(h,\mathbf{{q}})={smoothing_factor}\left(1-\frac{{u(\mathbf{{q}})}}{{2}}\right)"
        rf"[T(h,\mathbf{{q}})-I(h,\mathbf{{q}})]^+. \\[3pt]"
        "\n"
        rf"&\boxed{{Q(h,\mathbf{{q}})=\operatorname{{round}}_{{\mathrm{{even}}}}\left("
        r"\begin{cases}"
        rf"0, & x(h,\mathbf{{q}})<{min_order_size}, \\"
        r"x(h,\mathbf{q}), & x(h,\mathbf{q})\ge "
        rf"{min_order_size}"
        r"\end{cases}\right)}}."
        "\n"
        "\\end{aligned}\n"
        "\\]"
    )


def policy_source_to_compact_math(
    source: str,
    function_name: str = "compute_order_amount",
) -> str:
    """Return a readable compact formula for a recognized inventory-policy family.

    Compact mathematical summaries require policy-specific reasoning.  This
    renderer is intentionally strict: it recognizes parameter variants of
    known policy families and raises an error for other program structures.
    """

    function = _find_policy_function(source, function_name=function_name)
    errors = []
    for parameter_reader, formula_renderer in (
        (_compact_reciprocal_pipeline_parameters, _compact_reciprocal_pipeline_formula),
        (_compact_pipeline_parameters, _compact_pipeline_formula),
        (_compact_bounded_base_stock_parameters, _compact_bounded_base_stock_formula),
    ):
        try:
            return formula_renderer(parameter_reader(function))
        except UnsupportedCompactPolicyError as error:
            errors.append(str(error))
    raise UnsupportedCompactPolicyError(
        "Compact rendering does not recognize this policy structure. "
        "Use policy_source_to_math() for the structured fallback. "
        f"Checked renderers: {'; '.join(errors)}"
    )


def _straight_line_formula(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str | None:
    if isinstance(function, ast.AsyncFunctionDef):
        return None
    if any(
        not isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Return))
        for statement in function.body
    ):
        return None

    aliases = dict(DEFAULT_SYMBOL_ALIASES)
    notes: set[str] = set()
    expression = _ExpressionRenderer(aliases, notes)
    returned_value: str | None = None
    for statement in function.body:
        if isinstance(statement, ast.Assign):
            if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
                return None
            aliases[statement.targets[0].id] = expression.render(statement.value)
            continue
        if isinstance(statement, ast.AnnAssign):
            if not isinstance(statement.target, ast.Name) or statement.value is None:
                return None
            aliases[statement.target.id] = expression.render(statement.value)
            continue
        if isinstance(statement, ast.AugAssign):
            if not isinstance(statement.target, ast.Name):
                return None
            aliases[statement.target.id] = expression.render(
                ast.BinOp(left=statement.target, op=statement.op, right=statement.value)
            )
            continue
        if isinstance(statement, ast.Return):
            returned_value = (
                r"\mathrm{None}"
                if statement.value is None
                else expression.render(statement.value)
            )

    if returned_value is None:
        return None
    return (
        "% Compact mathematical representation of a straight-line inventory policy.\n"
        "% Policy constants are rounded to one decimal place for readability.\n"
        "\\[\n"
        "\\begin{aligned}\n"
        r"&\text{Inputs: } h=\text{on-hand inventory},\quad "
        r"\mathbf{q}=(q_0,\ldots,q_{L-1})=\text{pipeline orders}. \\[3pt]"
        "\n"
        rf"&\boxed{{Q(h,\mathbf{{q}})={returned_value}}}."
        "\n"
        "\\end{aligned}\n"
        "\\]"
    )


def policy_source_to_math(
    source: str,
    function_name: str = "compute_order_amount",
) -> str:
    """Return structured mathematical LaTeX for a function in ``source``."""

    function = _find_policy_function(source, function_name=function_name)
    straight_line_formula = _straight_line_formula(function)
    if straight_line_formula is not None:
        return straight_line_formula
    return _PolicyRenderer(function, parameter_names=_opt_parameter_names(source)).render()


def policy_to_math(
    policy: Callable[..., Any] | str,
    function_name: str = "compute_order_amount",
) -> str:
    """Return structured mathematical LaTeX for a policy callable or source string."""

    if isinstance(policy, str):
        return policy_source_to_math(policy, function_name=function_name)
    if not callable(policy):
        raise TypeError("policy must be a callable or a source-code string")
    try:
        source = inspect.getsource(policy)
    except (OSError, TypeError) as error:
        raise ValueError(
            "Could not inspect the policy source. Pass the source code as a string instead."
        ) from error
    return policy_source_to_math(source, function_name=policy.__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a Python inventory policy as LaTeX mathematics."
    )
    parser.add_argument("policy_file", help="Python source file, or '-' to read from standard input")
    parser.add_argument(
        "--function",
        default="compute_order_amount",
        help="top-level function to translate (default: compute_order_amount)",
    )
    parser.add_argument(
        "--style",
        choices=("declarative", "compact"),
        default="declarative",
        help="output style (default: declarative)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    source = sys.stdin.read() if args.policy_file == "-" else Path(args.policy_file).read_text()
    if args.style == "compact":
        print(policy_source_to_compact_math(source, function_name=args.function))
    else:
        print(policy_source_to_math(source, function_name=args.function))


if __name__ == "__main__":
    main()
