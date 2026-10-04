# policy_hash: 139f2cd37c03d397837f4a7c4846a6a4d12b69e7e835e81783d980af4b709001
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1219.78
# best_prompt_performance: 1219.78
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_005830.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 465.98230879148053  # OPT_PARAM: {"initial": 465.98230879148053, "min": 450, "max": 520, "type": "float"}
    safety_stock = 19.62458034183876  # OPT_PARAM: {"initial": 19.62458034183876, "min": 15, "max": 35, "type": "float"}
    demand_forecast = 97.81822752773326  # OPT_PARAM: {"initial": 97.81822752773326, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.02  # OPT_PARAM: {"initial": 0.02, "min": 0.02, "max": 0.1, "type": "float"}

    # Calculate total pipeline inventory (simple sum, no weighting)
    total_pipeline = sum(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + total_pipeline

    # Order-up-to level
    order_up_to = base_stock + safety_stock

    # Order-up-to policy with smoothing
    gap = order_up_to - inventory_position
    raw_order = max(0, gap)

    # Apply smoothing
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
