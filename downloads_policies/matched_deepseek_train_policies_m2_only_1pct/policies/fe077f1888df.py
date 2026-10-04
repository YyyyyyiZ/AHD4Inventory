# policy_hash: fe077f1888df16f408ce412dc6cdc1391ba0331d0ddebb31e0e0c1366bfe162e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 36
# source_prompt_files: 1
# best_target_performance: 737.27
# best_prompt_performance: 737.2
# best_rel_error_pct: 0.009494
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_034319.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 513.2555214989369  # OPT_PARAM: {"initial": 513.2555214989369, "min": 450, "max": 650, "type": "float"}
    safety_stock = 32.11559420382139  # OPT_PARAM: {"initial": 32.11559420382139, "min": 20, "max": 60, "type": "float"}
    demand_forecast = 97.16226763574495  # OPT_PARAM: {"initial": 97.16226763574495, "min": 85, "max": 115, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    order_threshold = 0.19012346392153107  # OPT_PARAM: {"initial": 0.19012346392153107, "min": 0.1, "max": 0.5, "type": "float"}
    max_order_multiplier = 1.1060839082638139  # OPT_PARAM: {"initial": 1.1060839082638139, "min": 1.0, "max": 2.5, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(i+1) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level with adjusted safety stock
    target_inventory = expected_lead_time_demand + safety_stock

    # Use weighted combination of base_stock and target_inventory
    order_up_to = 0.7 * base_stock + 0.3 * target_inventory

    # Calculate raw order amount with cap
    raw_order = max(0, order_up_to - inventory_position)
    capped_order = min(raw_order, max_order_multiplier * demand_forecast)

    # Apply smoothing based on threshold
    if capped_order > demand_forecast * order_threshold:
        order_amount = smoothing_factor * capped_order + (1 - smoothing_factor) * demand_forecast
    else:
        order_amount = capped_order

    # Round to nearest integer for practical implementation
    return order_amount
