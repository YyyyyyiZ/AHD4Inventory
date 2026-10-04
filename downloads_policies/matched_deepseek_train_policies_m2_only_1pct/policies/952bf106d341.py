# policy_hash: 952bf106d3419bab1caee2541452968c2b58d5e6e358b1b53b1af0dc5a599921
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 5916.83
# best_prompt_performance: 5916.72
# best_rel_error_pct: 0.001859
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_224738.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 189.2181992398715  # OPT_PARAM: {"initial": 189.2181992398715, "min": 180.0, "max": 300.0, "type": "float"}
    safety_multiplier = 1.3131018915895172  # OPT_PARAM: {"initial": 1.3131018915895172, "min": 1.2, "max": 2.5, "type": "float"}
    pipeline_coverage = 0.614862032616992  # OPT_PARAM: {"initial": 0.614862032616992, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.4012320770367011  # OPT_PARAM: {"initial": 0.4012320770367011, "min": 0.3, "max": 0.8, "type": "float"}
    min_order_threshold = 15.4770994281692  # OPT_PARAM: {"initial": 15.4770994281692, "min": 5.0, "max": 30.0, "type": "float"}
    demand_estimate_factor = 0.7008283003238222  # OPT_PARAM: {"initial": 0.7008283003238222, "min": 0.7, "max": 1.2, "type": "float"}
    lost_sales_weight = 1.0886942837055458  # OPT_PARAM: {"initial": 1.0886942837055458, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate covered pipeline (orders arriving within lead time)
    covered_pipeline = sum(pipeline_orders) * pipeline_coverage

    # Estimate expected demand based on base stock and pipeline
    expected_demand = demand_estimate_factor * (base_stock * 0.4 + covered_pipeline * 0.6)

    # Adjust safety stock based on cost ratio (p/h = 2)
    adjusted_safety = safety_multiplier * expected_demand * lost_sales_weight

    # Target inventory position
    target_inventory = base_stock + adjusted_safety

    # Calculate raw order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing
    smoothed_order = order_needed * smoothing_factor

    # Apply minimum order threshold
    if 0 < smoothed_order < min_order_threshold:
        smoothed_order = 0

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
