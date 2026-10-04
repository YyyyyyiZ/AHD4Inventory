# policy_hash: 46f6704e351add819b8993f8196462c800be7544bf41639be0ca37af09379e58
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 11249.02
# best_prompt_performance: 11249.02
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031231.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 211.59818073443125  # OPT_PARAM: {"initial": 211.59818073443125, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 16.434597726477385  # OPT_PARAM: {"initial": 16.434597726477385, "min": 0, "max": 200, "type": "float"}
    demand_multiplier = 0.7316236258870649  # OPT_PARAM: {"initial": 0.7316236258870649, "min": 0.5, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    recent_arrivals = [p for p in pipeline_orders if p > 0]
    if recent_arrivals:
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = 100.0  # Default estimate

    # Adjust base stock based on demand pattern
    adjusted_base = base_stock + demand_multiplier * avg_recent_demand

    # Calculate target inventory position
    target_position = adjusted_base + safety_stock

    # Order amount
    order_amount = max(0, target_position - inventory_position)

    # Round to integer for practical ordering
    return order_amount
