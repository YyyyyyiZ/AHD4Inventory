# policy_hash: df84d341258ac085d79748f042589305e7f81dff4854d787b552e5492b826434
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1560.02
# best_prompt_performance: 1562.58
# best_rel_error_pct: 0.164100
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_202919.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 620.3061713544452  # OPT_PARAM: {"initial": 620.3061713544452, "min": 550, "max": 700, "type": "float"}
    safety_stock = 24.37547517141253  # OPT_PARAM: {"initial": 24.37547517141253, "min": 15, "max": 40, "type": "float"}
    demand_forecast = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate order-up-to level
    order_up_to = base_stock + safety_stock - inventory_position

    # Apply smoothing with demand forecast adjustment
    if order_up_to > 0:
        smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Round to nearest integer and ensure non-negative
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
