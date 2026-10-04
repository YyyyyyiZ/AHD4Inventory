# policy_hash: 2a57e8e77843fee3227a9f0eaa86cd96afd2a552a4b1d465e69929f1e31773bd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 25
# source_prompt_files: 1
# best_target_performance: 11609.64
# best_prompt_performance: 11609.64
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084634.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 451.9713241186332  # OPT_PARAM: {"initial": 451.9713241186332, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.999999999996746  # OPT_PARAM: {"initial": 49.999999999996746, "min": 0, "max": 300, "type": "float"}
    demand_forecast = 99.99999999999675  # OPT_PARAM: {"initial": 99.99999999999675, "min": 10, "max": 500, "type": "float"}
    adjustment_factor = 0.5645040609103124  # OPT_PARAM: {"initial": 0.5645040609103124, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level based on forecast and safety stock
    target_inventory = demand_forecast + safety_stock

    # Calculate order amount with adjustment factor for smoother ordering
    raw_order = max(0, base_stock - inventory_position)
    adjusted_order = raw_order * adjustment_factor + (1 - adjustment_factor) * max(0, target_inventory - inventory_position)

    # Round to nearest integer (orders must be integer quantities)
    order_amount = int(round(adjusted_order))

    return order_amount
