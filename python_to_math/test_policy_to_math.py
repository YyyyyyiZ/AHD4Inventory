import unittest

from python_to_math.policy_to_math import (
    _COMPACT_BOUNDED_BASE_STOCK_POLICY_TEMPLATE,
    _COMPACT_PIPELINE_POLICY_TEMPLATE,
    _COMPACT_RECIPROCAL_PIPELINE_POLICY_TEMPLATE,
    UnsupportedCompactPolicyError,
    UnsupportedSyntaxError,
    policy_source_to_compact_math,
    policy_source_to_math,
    policy_to_math,
)


def simple_policy(on_hand_inventory, pipeline_orders):
    base_stock = 100
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount


class PolicyToMathTests(unittest.TestCase):
    def test_translates_callable(self):
        latex = policy_to_math(simple_policy)

        self.assertIn(r"Q(h,\mathbf{q})", latex)
        self.assertIn(r"\max\left(0", latex)
        self.assertIn(r"\sum_{i=0}^{L-1} q_i", latex)

    def test_translates_control_flow_loop_and_generator(self):
        source = """
        def compute_order_amount(on_hand_inventory, pipeline_orders):
            total = 0
            for i, q in enumerate(pipeline_orders):
                total += q * i
            if total > 10:
                target = sum((q - 1) ** 2 for q in pipeline_orders)
            else:
                target = 5
            return int(round(max(0, target - on_hand_inventory)))
        """

        latex = policy_source_to_math(source)

        self.assertIn(r"\mathrm{total} = \sum_{i=0}^{L-1}", latex)
        self.assertIn(r"\sum_{q \in \mathbf{q}}", latex)
        self.assertIn(r"\mathrm{target} = \begin{cases}", latex)
        self.assertIn(r"\operatorname{round}_{\mathrm{even}}", latex)
        self.assertNotIn(r"\text{for }", latex)

    def test_translates_slice_and_conditional_expression(self):
        source = """
        def compute_order_amount(on_hand_inventory, pipeline_orders):
            L = len(pipeline_orders)
            near = sum(pipeline_orders[:min(2, L)])
            return near if L > 0 else on_hand_inventory
        """

        latex = policy_source_to_math(source)

        self.assertIn(r"\sum_{i=0}^{\left(\min\left(2, L\right)\right)-1} q_i", latex)
        self.assertIn(r"\begin{cases}", latex)

    def test_rejects_unsupported_statement(self):
        source = """
        def compute_order_amount(on_hand_inventory, pipeline_orders):
            try:
                return 1
            except Exception:
                return 0
        """

        with self.assertRaisesRegex(UnsupportedSyntaxError, "Try"):
            policy_source_to_math(source)

    def test_compact_renderer_produces_readable_formula_for_recognized_policy(self):
        source = _COMPACT_PIPELINE_POLICY_TEMPLATE.replace(
            "base_stock = 0",
            "base_stock = 583.5806013968356",
        )

        latex = policy_source_to_compact_math(source)

        self.assertIn(r"\bar d =", latex)
        self.assertIn(r"s=\sum_{i=1}^{L-1}\operatorname{sgn}", latex)
        self.assertIn(r"B=u(n)\left[583.6", latex)
        self.assertNotIn("583.5806013968356", latex)
        self.assertIn(r"\boxed{Q(h,\mathbf{q})=", latex)
        self.assertNotIn(r"\textbf{for }", latex)

    def test_compact_renderer_rejects_changed_policy_structure(self):
        source = _COMPACT_PIPELINE_POLICY_TEMPLATE.replace(
            "inventory_position = on_hand_inventory + sum(pipeline_orders)",
            "inventory_position = on_hand_inventory - sum(pipeline_orders)",
        )

        with self.assertRaisesRegex(UnsupportedCompactPolicyError, "structure"):
            policy_source_to_compact_math(source)

    def test_compact_renderer_simplifies_bounded_base_stock_policy(self):
        source = (
            _COMPACT_BOUNDED_BASE_STOCK_POLICY_TEMPLATE
            .replace("base_stock = 0", "base_stock = 697.9997255235969")
            .replace("safety_stock = 0", "safety_stock = 79.3000000000116")
            .replace("demand_forecast = 0", "demand_forecast = 149.9")
        )

        latex = policy_source_to_compact_math(source)

        self.assertIn(r"T(L)=149.9L+79.3", latex)
        self.assertIn(r"[x]^+=\max(0,x)", latex)
        self.assertIn(
            r"\boxed{Q(h,\mathbf{q})=\left[\min\left(698.0,T(L)\right)"
            r"-I(h,\mathbf{q})\right]^+}",
            latex,
        )
        self.assertNotIn("697.9997255235969", latex)
        self.assertNotIn(r"\text{for }", latex)

    def test_compact_renderer_simplifies_reciprocal_pipeline_policy(self):
        source = (
            _COMPACT_RECIPROCAL_PIPELINE_POLICY_TEMPLATE
            .replace("base_stock = 0", "base_stock = 852.0694799766587")
            .replace("demand_anticipation_factor = 0", "demand_anticipation_factor = 0.1")
            .replace("recent_demand_weight = 0", "recent_demand_weight = 0.6")
            .replace("pipeline_urgency_factor = 0", "pipeline_urgency_factor = 0.5795120417177109")
            .replace("holding_cost_weight = 0", "holding_cost_weight = 0.8138365213306138")
            .replace("lost_sales_cost_weight = 0", "lost_sales_cost_weight = 1.4091129587809088")
            .replace("smoothing_factor = 0", "smoothing_factor = 0.13063463854289023")
            .replace("min_order_size = 0", "min_order_size = 10.0")
            .replace("safety_stock = 0", "safety_stock = 220.0")
            .replace("safety_adjustment_factor = 0", "safety_adjustment_factor = 0.3038678010386268")
            .replace("lost_sales_multiplier = 0", "lost_sales_multiplier = 1.5")
        )

        latex = policy_source_to_compact_math(source)

        self.assertIn(r"H_L=\sum_{i=1}^{L}\frac{1}{i}", latex)
        self.assertIn(r"D_0(\mathbf{q})=852.1", latex)
        self.assertIn(r"x(h,\mathbf{q})=0.1", latex)
        self.assertIn(r"x(h,\mathbf{q})<10.0", latex)
        self.assertNotIn("852.0694799766587", latex)
        self.assertNotIn(r"\text{for }", latex)


if __name__ == "__main__":
    unittest.main()
