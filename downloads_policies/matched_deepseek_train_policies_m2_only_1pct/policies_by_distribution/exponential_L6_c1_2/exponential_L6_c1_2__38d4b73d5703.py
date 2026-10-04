# policy_hash: 38d4b73d5703ef3622fd68806f3a2f9e59a43d3eb660aef167c39eca733ffd88
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 6572.42
# best_prompt_performance: 6572.42
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_093232.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 357.0619768718896  # OPT_PARAM: {"initial": 357.0619768718896, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 10, "max": 500, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = 3.0  # OPT_PARAM: {"initial": 3.0, "min": 1.0, "max": 6.0, "type": "float"}

    # Use the larger of base_stock policy or demand-based policy
    base_order = max(0, base_stock - inventory_position)
    demand_order = max(0, target_inventory - inventory_position)

    # Blend both policies with weights
    weight_base = 0.3925171135246547  # OPT_PARAM: {"initial": 0.3925171135246547, "min": 0.0, "max": 1.0, "type": "float"}
    order_amount = weight_base * base_order + (1 - weight_base) * demand_order

    # Round to nearest integer (orders must be integer quantities)
    order_amount = int(round(order_amount))

    return order_amount
