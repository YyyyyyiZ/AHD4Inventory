# policy_hash: a996bacb4e1a5ad1d17682b4258fbb8e0e3ecc93a651cf03732a0f994f689127
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 754.96
# best_prompt_performance: 754.79
# best_rel_error_pct: 0.022518
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_075126.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 487.0185579788431  # OPT_PARAM: {"initial": 487.0185579788431, "min": 300, "max": 600, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 20, "max": 100, "type": "float"}
    demand_forecast = 97.28616632713182  # OPT_PARAM: {"initial": 97.28616632713182, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.8, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(i+1) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Dynamic safety stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_ratio = weighted_pipeline / pipeline_sum
        adjusted_safety = safety_stock * (1.0 + 0.2 * (1.0 - pipeline_ratio))
    else:
        adjusted_safety = safety_stock

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + adjusted_safety

    # Use the maximum of base_stock and target_inventory
    order_up_to = max(base_stock, target_inventory)

    # Calculate order quantity
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand forecast adjustment
    if order_amount > 0:
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast
        order_amount = min(order_amount, smoothed_order)

    return order_amount
