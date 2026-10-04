# policy_hash: 6e8b3703faf5b04156d06ed7dab695707136c5cbb669a5bfbcfa5a978bf4b1b5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 760.91
# best_prompt_performance: 760.91
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_023143.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 580.0  # OPT_PARAM: {"initial": 580.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 89.54404982842802  # OPT_PARAM: {"initial": 89.54404982842802, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 119.9  # OPT_PARAM: {"initial": 119.9, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Order up to target, but ensure non-negative
    order_amount = max(0, target_position - inventory_position)

    # Cap order amount to avoid excessive ordering
    max_order = 96.00723092906131  # OPT_PARAM: {"initial": 96.00723092906131, "min": 80, "max": 200, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
