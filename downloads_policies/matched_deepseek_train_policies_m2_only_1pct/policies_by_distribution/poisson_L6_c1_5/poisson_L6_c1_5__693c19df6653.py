# policy_hash: 693c19df6653e2f7068436212693f65460caf82a9435555a0a1afa3872c53642
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 3123.96
# best_prompt_performance: 3120.86
# best_rel_error_pct: 0.099233
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_045630.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 650.5354705871234  # OPT_PARAM: {"initial": 650.5354705871234, "min": 400, "max": 900, "type": "float"}
    safety_stock = 79.72731490857149  # OPT_PARAM: {"initial": 79.72731490857149, "min": 20, "max": 150, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on pipeline orders (as proxy for recent demand)
    recent_demand_estimate = sum(pipeline_orders[-3:]) / 3 if len(pipeline_orders) >= 3 else 100.0

    # Dynamic target that adjusts to recent demand patterns
    dynamic_target = base_stock + safety_stock * demand_buffer

    # Order amount calculation with smoother adjustment
    order_amount = max(0, (dynamic_target - net_inventory) * adjustment_factor)

    # Add small buffer based on recent demand estimate
    if order_amount > 0:
        order_amount += recent_demand_estimate * 0.1

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
