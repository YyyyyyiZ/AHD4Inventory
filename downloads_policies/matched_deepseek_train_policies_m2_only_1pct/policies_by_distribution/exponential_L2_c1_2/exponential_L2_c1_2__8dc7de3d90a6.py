# policy_hash: 8dc7de3d90a603fbdf02fa297c56c2342172bc5ce01365c1f35ae7686f53ee72
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 6631.54
# best_prompt_performance: 6631.54
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_064033.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 207.94635405795194  # OPT_PARAM: {"initial": 207.94635405795194, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.99999999997912  # OPT_PARAM: {"initial": 49.99999999997912, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on recent pipeline arrivals
    # Use average of recent pipeline arrivals as demand proxy
    if len(pipeline_orders) > 0:
        recent_demand_estimate = sum(pipeline_orders) / len(pipeline_orders)
    else:
        recent_demand_estimate = 0

    # Adjust base stock based on demand pattern
    adjusted_base_stock = base_stock + safety_stock + demand_forecast_factor * recent_demand_estimate

    # Calculate order amount with smoothing
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Round to nearest integer for practical ordering
    order_amount = int(round(raw_order))

    return order_amount
