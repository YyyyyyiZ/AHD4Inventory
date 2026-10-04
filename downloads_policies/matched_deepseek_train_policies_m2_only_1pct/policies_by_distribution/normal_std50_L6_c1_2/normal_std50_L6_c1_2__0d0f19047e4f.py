# policy_hash: 0d0f19047e4f8ecb98f953bfdad07c2f2c691bfccbed2d48073f34c62d3eabb9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 4299.55
# best_prompt_performance: 4297.7
# best_rel_error_pct: 0.043028
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_003928.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 407.2681182597732  # OPT_PARAM: {"initial": 407.2681182597732, "min": 300, "max": 600, "type": "float"}
    safety_stock = 7.268118259764031  # OPT_PARAM: {"initial": 7.268118259764031, "min": 0, "max": 150, "type": "float"}
    demand_forecast = 82.27314409030498  # OPT_PARAM: {"initial": 82.27314409030498, "min": 80, "max": 140, "type": "float"}
    pipeline_weight = 0.9715186610801283  # OPT_PARAM: {"initial": 0.9715186610801283, "min": 0.5, "max": 1.0, "type": "float"}
    order_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_inventory = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate base order amount
    base_order = max(0, target_inventory - effective_inventory + demand_forecast)

    # Apply smoothing to reduce order volatility
    smoothed_order = order_smoothing * base_order + (1 - order_smoothing) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
