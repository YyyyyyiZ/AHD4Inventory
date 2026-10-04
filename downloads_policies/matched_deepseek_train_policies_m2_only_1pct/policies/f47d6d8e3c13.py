# policy_hash: f47d6d8e3c1365818ff0f28d930c48c59a620a45063571c38eeb2ee0bec7844f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 993.2
# best_prompt_performance: 993.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_223838.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 474.986349117334  # OPT_PARAM: {"initial": 474.986349117334, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 93.12272886166139  # OPT_PARAM: {"initial": 93.12272886166139, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_position)

    # Calculate order amount with smoothing
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
