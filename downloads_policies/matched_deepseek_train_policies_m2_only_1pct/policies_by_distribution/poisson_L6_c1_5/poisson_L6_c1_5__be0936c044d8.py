# policy_hash: be0936c044d818dc1c3a4b0ed2981eadf1ba151e6b320bee80bcbed69ceb2df9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 3163.28
# best_prompt_performance: 3164.26
# best_rel_error_pct: 0.030981
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_044259.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 698.0003950792877  # OPT_PARAM: {"initial": 698.0003950792877, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.00066955569079  # OPT_PARAM: {"initial": 50.00066955569079, "min": 0, "max": 200, "type": "float"}
    adjustment_factor = 0.6208091108379084  # OPT_PARAM: {"initial": 0.6208091108379084, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock adjustment
    target_inventory = base_stock + safety_stock

    # Calculate order amount with adjustment factor
    order_amount = max(0, (target_inventory - net_inventory) * adjustment_factor)

    # Round to nearest integer (since order amount should be integer)
    order_amount = int(round(order_amount))

    return order_amount
