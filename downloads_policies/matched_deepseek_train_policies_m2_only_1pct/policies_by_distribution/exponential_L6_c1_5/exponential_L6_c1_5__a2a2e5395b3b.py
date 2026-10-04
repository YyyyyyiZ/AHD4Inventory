# policy_hash: a2a2e5395b3b957fa43072424710766bdfdb93653d51b33450dba7a754e43f15
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 12743.88
# best_prompt_performance: 12743.86
# best_rel_error_pct: 0.000157
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_095951.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.88962380004034  # OPT_PARAM: {"initial": 449.88962380004034, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 45.90208406590735  # OPT_PARAM: {"initial": 45.90208406590735, "min": 0, "max": 500, "type": "float"}
    demand_estimate = 39.414870487356815  # OPT_PARAM: {"initial": 39.414870487356815, "min": 10, "max": 500, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on recent pipeline arrivals
    recent_arrivals = sum(pipeline_orders[:2])  # Next 2 periods' arrivals
    adjusted_base = base_stock + safety_stock - smoothing_factor * recent_arrivals

    # Calculate order-up-to level
    order_up_to = max(demand_estimate, adjusted_base - inventory_position)

    # Ensure non-negative order
    order_amount = max(0, order_up_to)

    return order_amount
