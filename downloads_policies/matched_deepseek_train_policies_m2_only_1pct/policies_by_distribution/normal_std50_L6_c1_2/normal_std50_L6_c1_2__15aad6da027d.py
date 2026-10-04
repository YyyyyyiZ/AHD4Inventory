# policy_hash: 15aad6da027d077b80941fe3f6638ec0a7b2acaf76410e762f4b9ffa290b4004
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 3916.12
# best_prompt_performance: 3916.02
# best_rel_error_pct: 0.002554
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_003807.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 313.4000000000168  # OPT_PARAM: {"initial": 313.4000000000168, "min": 300, "max": 500, "type": "float"}
    demand_forecast = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 140, "type": "float"}
    pipeline_coverage_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_forecast * lead_time

    # Add safety stock based on demand variability
    safety_stock = safety_stock_factor * demand_forecast

    # Calculate target inventory position
    target_inventory_position = base_stock + safety_stock

    # Adjust for pipeline coverage more conservatively
    pipeline_coverage = sum(pipeline_orders) / max(1, expected_demand_during_lead_time)
    adjustment = pipeline_coverage_factor * min(1.0, pipeline_coverage)
    adjusted_target = target_inventory_position * (1 - adjustment)

    # Calculate base order
    base_order = max(0, adjusted_target - inventory_position)

    # Smooth with demand forecast
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative and integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
