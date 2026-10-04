# policy_hash: c660450ab0b77227fabbca741890b5b9d22523aed7863fc13ba69c9d4b1c8f02
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2572.56
# best_prompt_performance: 2576.38
# best_rel_error_pct: 0.148490
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_041632.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 480.0  # OPT_PARAM: {"initial": 480.0, "min": 400, "max": 550, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 20, "max": 100, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 80, "max": 120, "type": "float"}

    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline status
    incoming_soon = sum(pipeline_orders[:2])  # next 2 periods arrivals
    if incoming_soon < demand_estimate * 1.5:
        adjusted_base = base_stock + safety_stock
    else:
        adjusted_base = base_stock

    order_amount = max(0, adjusted_base - inventory_position)

    # Smooth ordering to avoid extreme fluctuations
    if order_amount > demand_estimate * 3:
        order_amount = demand_estimate * 2.5  # OPT_PARAM: {"initial": 2.5, "min": 2.0, "max": 3.5, "type": "float"}

    return order_amount
