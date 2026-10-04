# policy_hash: ae0b7194b853e78aff57ebffa98be55b2358868d103e28212b726ebcbb6cde24
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 1022.12
# best_prompt_performance: 1020.98
# best_rel_error_pct: 0.111533
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_235006.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 482.9217190211206  # OPT_PARAM: {"initial": 482.9217190211206, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 101.34320712955834  # OPT_PARAM: {"initial": 101.34320712955834, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 101.90602057554038  # OPT_PARAM: {"initial": 101.90602057554038, "min": 50, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = lead_time_demand + safety_stock

    # Order up to target, but ensure non-negative
    order_amount = max(0, target_position - inventory_position)

    # Apply a smoothing factor to avoid large order fluctuations
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
