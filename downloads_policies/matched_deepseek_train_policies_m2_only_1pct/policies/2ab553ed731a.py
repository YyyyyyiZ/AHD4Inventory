# policy_hash: 2ab553ed731a47d2e94b2f201ce4a3e35b4f0ae2cd4e23d7f80a2c7d4a99ec31
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 1681.64
# best_prompt_performance: 1676.72
# best_rel_error_pct: 0.292572
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_022824.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 482.9126571145125  # OPT_PARAM: {"initial": 482.9126571145125, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.1  # OPT_PARAM: {"initial": 50.1, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.7150940584610543  # OPT_PARAM: {"initial": 0.7150940584610543, "min": 0.1, "max": 2.0, "type": "float"}
    pipeline_weight = 0.7352831500975854  # OPT_PARAM: {"initial": 0.7352831500975854, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline status
    adjusted_base_stock = base_stock + safety_stock * (1 - pipeline_weight * len(pipeline_orders) / 4)

    # Calculate order amount with smoothing
    raw_order = max(0, adjusted_base_stock - inventory_position)
    smoothed_order = demand_forecast_factor * raw_order

    # Round to nearest integer (as required by output type)
    order_amount = int(round(smoothed_order))

    return order_amount
