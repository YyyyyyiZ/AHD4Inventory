# policy_hash: afc30c92845f69eb5d93bb38eebd8ad63c92616d5d1222f1320a4511b77bc9ad
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 5893.3
# best_prompt_performance: 5893.22
# best_rel_error_pct: 0.001357
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_030008.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 161.44283562332865  # OPT_PARAM: {"initial": 161.44283562332865, "min": 100, "max": 300, "type": "float"}
    safety_factor = 1.4342266566763202  # OPT_PARAM: {"initial": 1.4342266566763202, "min": 1.0, "max": 3.0, "type": "float"}
    demand_estimate = 124.17888982841735  # OPT_PARAM: {"initial": 124.17888982841735, "min": 80, "max": 200, "type": "float"}
    pipeline_weight = 0.42141004218974387  # OPT_PARAM: {"initial": 0.42141004218974387, "min": 0.1, "max": 0.8, "type": "float"}
    smoothing = 0.5864206482716005  # OPT_PARAM: {"initial": 0.5864206482716005, "min": 0.1, "max": 0.9, "type": "float"}
    demand_floor_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_estimate * lead_time

    # Calculate safety stock
    safety_stock = safety_factor * (lead_time_demand ** 0.5)
    target_inventory = base_stock + safety_stock

    # Adjust for pipeline with moderate weight
    pipeline_adjustment = pipeline_weight * sum(pipeline_orders)
    adjusted_target = max(target_inventory - pipeline_adjustment, lead_time_demand)

    # Calculate raw order
    raw_order = max(0, adjusted_target - inventory_position)

    # Apply smoothing with demand-based adjustment
    smoothed_order = smoothing * raw_order + (1 - smoothing) * demand_estimate

    # Ensure order covers expected demand with flexible floor
    incoming_order = pipeline_orders[0] if pipeline_orders else 0
    demand_floor = demand_floor_weight * max(0, demand_estimate - on_hand_inventory - incoming_order)
    final_order = max(smoothed_order, demand_floor)

    # Round to nearest integer
    order_amount = int(round(final_order))

    return order_amount
