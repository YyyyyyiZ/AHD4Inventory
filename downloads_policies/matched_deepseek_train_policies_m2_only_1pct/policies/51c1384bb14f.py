# policy_hash: 51c1384bb14f50fc1a6d353af629c78a542cc12124d23df16f7667fa42710eef
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1418.76
# best_prompt_performance: 1418.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_235404.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 419.8425174783473  # OPT_PARAM: {"initial": 419.8425174783473, "min": 300, "max": 600, "type": "float"}
    safety_stock = 34.842517478347276  # OPT_PARAM: {"initial": 34.842517478347276, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 99.78954792977757  # OPT_PARAM: {"initial": 99.78954792977757, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock - pipeline_weight * expected_lead_time_demand

    # Calculate order-up-to quantity
    order_up_to = target_inventory - inventory_position

    # Apply smoothing to avoid extreme fluctuations
    smoothed_order = max(0, smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast)

    # Round to nearest integer (practical ordering constraint)
    order_amount = int(round(smoothed_order))

    return order_amount
