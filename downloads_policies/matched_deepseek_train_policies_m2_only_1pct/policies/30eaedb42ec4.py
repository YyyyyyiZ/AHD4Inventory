# policy_hash: 30eaedb42ec4bb12e83d3168dcdec325d3803a7b04f812be27d655db6111f7cd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2684.06
# best_prompt_performance: 2684.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_050619.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.0  # OPT_PARAM: {"initial": 550.0, "min": 300, "max": 800, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 0, "max": 100, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Cap the order amount based on demand forecast
    max_order = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 200, "type": "float"}
    order_amount = min(order_amount, max_order)

    # Round to nearest integer since order amount must be integer
    order_amount = int(round(order_amount))

    return order_amount
