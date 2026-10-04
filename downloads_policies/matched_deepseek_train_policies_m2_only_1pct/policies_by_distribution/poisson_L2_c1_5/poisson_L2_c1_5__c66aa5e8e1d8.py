# policy_hash: c66aa5e8e1d8d6da424d840fbf39b7ddd185d05bc07dc48d9c1d02554d933b47
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 3932.46
# best_prompt_performance: 3932.46
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_230424.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 313.28720660206926  # OPT_PARAM: {"initial": 313.28720660206926, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 54.30572512058948  # OPT_PARAM: {"initial": 54.30572512058948, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 101.31510621540386  # OPT_PARAM: {"initial": 101.31510621540386, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.3297784947778332  # OPT_PARAM: {"initial": 0.3297784947778332, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline status
    if pipeline_orders[0] > 0:  # Arrival happening this period
        adjusted_base = base_stock - safety_stock
    else:
        adjusted_base = base_stock + safety_stock

    # Calculate order-up-to level
    order_up_to = adjusted_base + smoothing_factor * (demand_estimate - pipeline_orders[-1])

    # Determine order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Round to nearest integer since order amounts should be integers
    return order_amount
