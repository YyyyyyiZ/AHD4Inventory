# policy_hash: 5acdab76c7e1b8a1df08086e40612934c4862ffaa3fb77d099c05c0435ddcfd6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2555.86
# best_prompt_performance: 2555.12
# best_rel_error_pct: 0.028953
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_041715.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 454.7402851357525  # OPT_PARAM: {"initial": 454.7402851357525, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 1.7468731508559467  # OPT_PARAM: {"initial": 1.7468731508559467, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on pipeline orders (as proxy for recent demand)
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-min(3, len(pipeline_orders)):]  # Last 3 orders
        avg_recent_order = sum(recent_orders) / len(recent_orders) if recent_orders else 0
        expected_demand = avg_recent_order * demand_forecast_factor
    else:
        expected_demand = 0

    # Adjust base stock based on expected demand and safety stock
    adjusted_base_stock = base_stock + safety_stock + expected_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Round to nearest integer (as order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
