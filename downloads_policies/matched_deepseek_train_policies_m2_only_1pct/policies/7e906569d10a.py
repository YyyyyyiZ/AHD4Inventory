# policy_hash: 7e906569d10a770eea995335d115c8aca708ea4fad6e6fc937371d1777205595
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 954.04
# best_prompt_performance: 954.04
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_000728.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.0  # OPT_PARAM: {"initial": 550.0, "min": 350, "max": 550, "type": "float"}
    safety_stock = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 20, "max": 100, "type": "float"}
    demand_forecast = 95.51617358590451  # OPT_PARAM: {"initial": 95.51617358590451, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.5904833338736188  # OPT_PARAM: {"initial": 0.5904833338736188, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    order_threshold = 20.1  # OPT_PARAM: {"initial": 20.1, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock - pipeline_weight * expected_lead_time_demand

    # Calculate order-up-to quantity
    order_up_to = target_inventory - inventory_position

    # Apply smoothing with demand forecast as baseline
    if order_up_to > order_threshold:
        smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = max(0, smoothing_factor * order_up_to)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
