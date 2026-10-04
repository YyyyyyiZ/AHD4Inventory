# policy_hash: 5b4ef4903133a961385d746d8aa68570041737357ee7079b32bafbbef4f7cd63
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 2
# best_target_performance: 1920.12
# best_prompt_performance: 1920.12
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_021606.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 294.0000013139217  # OPT_PARAM: {"initial": 294.0000013139217, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 100, "type": "float"}
    demand_adjustment = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[:2]  # Oldest two (recently arrived)
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0
    else:
        avg_recent_demand = 0

    # Adjust base stock based on recent demand pattern
    adjusted_base_stock = base_stock + (avg_recent_demand * demand_adjustment - 100) * 0.5

    # Calculate order amount with safety stock consideration
    target_inventory = max(adjusted_base_stock, safety_stock * 2)
    order_amount = max(0, target_inventory - net_inventory)

    # Round to nearest integer (practical ordering constraint)
    order_amount = int(round(order_amount))

    return order_amount
