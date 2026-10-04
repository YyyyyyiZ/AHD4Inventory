# policy_hash: b5bb691099f4dcbede571be377575b4ddd157b4091bb4626fa1dbe34561dceef
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_2
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 796.11
# best_prompt_performance: 796.11
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_002044.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 512.4323385581537  # OPT_PARAM: {"initial": 512.4323385581537, "min": 300, "max": 800, "type": "float"}
    safety_stock = 36.40782619521588  # OPT_PARAM: {"initial": 36.40782619521588, "min": 30, "max": 150, "type": "float"}
    demand_forecast = 82.15061277619321  # OPT_PARAM: {"initial": 82.15061277619321, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.5, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    variability_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    order_threshold = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(i+1) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Dynamic safety stock based on pipeline variability
    if len(pipeline_orders) > 0:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_std = (sum((p - pipeline_mean)**2 for p in pipeline_orders) / len(pipeline_orders))**0.5
        dynamic_safety = safety_stock + variability_factor * pipeline_std
    else:
        dynamic_safety = safety_stock

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + dynamic_safety

    # Use the maximum of base_stock and target_inventory
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing only when order is significant
    if order_amount > demand_forecast * order_threshold:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    return order_amount
