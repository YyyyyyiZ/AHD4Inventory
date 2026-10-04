# policy_hash: 89050d918950c0a9294a6cc241c1455f61167a4294c35892c2e87697d566496b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 5668.0
# best_prompt_performance: 5664.82
# best_rel_error_pct: 0.056104
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_232610.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 525.5521701420682  # OPT_PARAM: {"initial": 525.5521701420682, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 41.70000000010626  # OPT_PARAM: {"initial": 41.70000000010626, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand from pipeline (average of recent orders)
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        expected_demand = sum(recent_orders) / len(recent_orders)
    else:
        expected_demand = 0

    # Adjust base stock based on expected demand
    adjusted_base_stock = base_stock + safety_stock + (expected_demand * smoothing_factor)

    # Calculate order amount with smoothing
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply rounding to nearest integer
    order_amount = int(round(raw_order))

    return order_amount
