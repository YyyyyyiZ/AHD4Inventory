# policy_hash: 119480f0a3927aaad51a6079db9387c349214c8660dd8f3d192fbfef946ffc9a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 784.85
# best_prompt_performance: 784.88
# best_rel_error_pct: 0.003822
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_235757.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 364.0059469535102  # OPT_PARAM: {"initial": 364.0059469535102, "min": 350, "max": 500, "type": "float"}
    demand_estimate = 87.09722680000094  # OPT_PARAM: {"initial": 87.09722680000094, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock = 18.446378559554464  # OPT_PARAM: {"initial": 18.446378559554464, "min": 10, "max": 60, "type": "float"}
    pipeline_weight = 0.33121042005465684  # OPT_PARAM: {"initial": 0.33121042005465684, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(i+1) for i, p in enumerate(pipeline_orders))
    effective_position = on_hand_inventory + weighted_pipeline

    # Dynamic target based on safety stock
    target_position = base_stock + safety_stock

    # Order amount calculation
    order_amount = max(0, target_position - effective_position)

    # Apply smoothing with demand-based floor
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Ensure minimum order is at least demand estimate when inventory is low
    if effective_position < base_stock * 0.8:
        order_amount = max(order_amount, demand_estimate * 0.5)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
