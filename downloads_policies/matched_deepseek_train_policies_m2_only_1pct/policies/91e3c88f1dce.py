# policy_hash: 91e3c88f1dce15df74f3be5e161942ea91fce1ed330176ee95f14f6c6beede0d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 4686.68
# best_prompt_performance: 4682.07
# best_rel_error_pct: 0.098364
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_120856.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 694.2653099658278  # OPT_PARAM: {"initial": 694.2653099658278, "min": 400, "max": 900, "type": "float"}
    safety_stock = 154.1749128386518  # OPT_PARAM: {"initial": 154.1749128386518, "min": 50, "max": 200, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    demand_forecast_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline to account for future arrivals
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Adjust base stock based on pipeline composition
    adjusted_base = base_stock * (1 + demand_forecast_factor * (1 - weighted_pipeline / (base_stock + 1e-6)))

    # Calculate desired order-up-to level
    desired_level = adjusted_base + safety_stock

    # Calculate order amount with smoothing
    raw_order = desired_level - inventory_position
    order_amount = max(0, smoothing_factor * raw_order)

    # Round to nearest integer
    return order_amount
