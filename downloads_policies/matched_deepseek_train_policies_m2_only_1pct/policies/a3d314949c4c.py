# policy_hash: a3d314949c4c14b24627b9b6363a29f1ea3c4e045aa82e00503bb1577af521f4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 887.04
# best_prompt_performance: 887.04
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_224417.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 434.2799062610298  # OPT_PARAM: {"initial": 434.2799062610298, "min": 300, "max": 600, "type": "float"}
    safety_stock = 40.1  # OPT_PARAM: {"initial": 40.1, "min": 20, "max": 80, "type": "float"}
    demand_estimate = 87.29101242914156  # OPT_PARAM: {"initial": 87.29101242914156, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.5643455584809454  # OPT_PARAM: {"initial": 0.5643455584809454, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(len(pipeline_orders)-i-1)
                          for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Dynamic safety stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_std = (sum((p - pipeline_sum/len(pipeline_orders))**2 for p in pipeline_orders) /
                       len(pipeline_orders))**0.5
        adjusted_safety = safety_stock * (1 + min(1.0, pipeline_std / demand_estimate))
    else:
        adjusted_safety = safety_stock

    # Calculate target inventory position
    target_position = lead_time_demand + adjusted_safety

    # Use the maximum of base_stock and dynamic target
    order_up_to = max(base_stock, target_position)

    # Calculate order amount with smoothing
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
