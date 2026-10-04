# policy_hash: 2621c32ac0e653eac9645c6713bdb91ac90109d9f46e4167d6735a639529702a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 48
# source_prompt_files: 1
# best_target_performance: 738.52
# best_prompt_performance: 738.52
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r9/prompt_for_code/m2_20260129_213914.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 280.0  # OPT_PARAM: {"initial": 280.0, "min": 200, "max": 350, "type": "float"}
    demand_forecast = 94.85009789495761  # OPT_PARAM: {"initial": 94.85009789495761, "min": 90, "max": 110, "type": "float"}
    safety_factor = 1.1780050528876775  # OPT_PARAM: {"initial": 1.1780050528876775, "min": 1.0, "max": 2.5, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.5, "max": 0.9, "type": "float"}
    order_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight ** i for i, p in enumerate(reversed(pipeline_orders)))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time plus one period
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_forecast * (lead_time + 1)

    # Calculate safety stock based on demand variability
    safety_stock = safety_factor * demand_forecast * (lead_time ** 0.5)

    # Calculate target inventory level
    target_inventory = lead_time_demand + safety_stock

    # Calculate base order amount
    base_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = order_smoothing * base_order + (1 - order_smoothing) * demand_forecast

    # Apply base stock as upper bound
    order_amount = min(smoothed_order, base_stock)

    # Round to nearest integer for practical ordering
    return order_amount
