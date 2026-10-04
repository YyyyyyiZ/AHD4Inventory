# policy_hash: b5c6cf733491fb3edb1704e32939177584f7e5532680ed8edf89af27c97ff4df
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 12138.47
# best_prompt_performance: 12108.71
# best_rel_error_pct: 0.245171
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_071934.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 295.83200520977243  # OPT_PARAM: {"initial": 295.83200520977243, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 27.965903023625234  # OPT_PARAM: {"initial": 27.965903023625234, "min": 0, "max": 200, "type": "float"}
    demand_multiplier = 0.7926084408534432  # OPT_PARAM: {"initial": 0.7926084408534432, "min": 0.5, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:1] if pipeline_orders else [0]
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)

    # Adjust base stock based on demand pattern
    adjusted_base = base_stock * demand_multiplier

    # Calculate target inventory position
    target_inventory = max(adjusted_base, safety_stock + avg_recent_demand * 2)

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Round to integer as required
    return order_amount
