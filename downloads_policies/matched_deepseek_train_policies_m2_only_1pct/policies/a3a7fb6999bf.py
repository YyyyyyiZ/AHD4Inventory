# policy_hash: a3a7fb6999bfeb01b8d2d609bbe6ea64c7067fc963db7a566a1354a71b449456
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 6959.2
# best_prompt_performance: 6959.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_075450.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 278.71771951475694  # OPT_PARAM: {"initial": 278.71771951475694, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 45.75426443114924  # OPT_PARAM: {"initial": 45.75426443114924, "min": 0, "max": 200, "type": "float"}
    demand_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate recent demand pattern from pipeline arrivals
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    recent_demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 300, "type": "float"}

    # Adjust base stock based on recent demand pattern
    adjusted_base_stock = base_stock + safety_stock
    if recent_demand_estimate > 150:  # OPT_PARAM: {"initial": 150, "min": 100, "max": 250, "type": "float"}
        adjusted_base_stock += recent_demand_estimate * demand_smoothing

    # Calculate order amount with smoothing
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply ordering threshold to avoid tiny orders
    if raw_order < 20:  # OPT_PARAM: {"initial": 20, "min": 5, "max": 50, "type": "float"}
        order_amount = 25.0  # Optimized
    else:
        # Round to nearest reasonable increment
        order_amount = int(round(raw_order / 10) * 10)  # OPT_PARAM: {"initial": 10, "min": 5, "max": 25, "type": "float"}

    return order_amount
