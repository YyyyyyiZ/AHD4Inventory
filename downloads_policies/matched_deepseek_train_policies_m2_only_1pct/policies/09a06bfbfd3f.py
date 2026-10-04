# policy_hash: 09a06bfbfd3f46dfdae434f51e26df988edf11700e63ab1c788f83b2fd14cab1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 1032.26
# best_prompt_performance: 1032.26
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223251.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 270.98490905860024  # OPT_PARAM: {"initial": 270.98490905860024, "min": 200, "max": 350, "type": "float"}
    safety_stock = 22.014092800815284  # OPT_PARAM: {"initial": 22.014092800815284, "min": 10, "max": 60, "type": "float"}
    demand_smoothing = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of recent pipeline arrivals
    # More weight to recent arrivals
    if len(pipeline_orders) >= 2:
        recent_avg = (pipeline_orders[0] * 0.6 + pipeline_orders[1] * 0.4) if len(pipeline_orders) >= 2 else 100
    else:
        recent_avg = 100

    # Adjust base stock based on smoothed demand estimate
    demand_adjustment = demand_smoothing * (recent_avg - 100)

    # Adjust for pipeline variability
    if len(pipeline_orders) >= 2:
        pipeline_variability = abs(pipeline_orders[0] - pipeline_orders[1]) * pipeline_weight
    else:
        pipeline_variability = 0

    # Calculate target inventory position
    target_inventory_position = base_stock + demand_adjustment + safety_stock + pipeline_variability

    # Calculate order amount
    order_amount = max(0, target_inventory_position - inventory_position)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
