# policy_hash: 2b8a3e33e66d5525f2dba12913ee2ac797f60567fc304b14133108e6947676ff
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 31
# source_prompt_files: 1
# best_target_performance: 1176.48
# best_prompt_performance: 1176.45
# best_rel_error_pct: 0.002550
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232506.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 283.4132366355824  # OPT_PARAM: {"initial": 283.4132366355824, "min": 250, "max": 400, "type": "float"}
    safety_stock = 26.50250410515792  # OPT_PARAM: {"initial": 26.50250410515792, "min": 20, "max": 60, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Better demand estimation using pipeline arrivals
    if len(pipeline_orders) >= 2:
        # Use weighted average giving more weight to recent arrivals
        recent_demand_estimate = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.3, "max": 0.8, "type": "float"}
    else:
        recent_demand_estimate = 100.0

    # Dynamic base stock adjustment based on demand trend
    adjusted_base_stock = base_stock + safety_stock

    # More aggressive adjustment for high demand
    if recent_demand_estimate > 115:
        adjusted_base_stock += 30.0  # OPT_PARAM: {"initial": 30.0, "min": 15, "max": 45, "type": "float"}
    elif recent_demand_estimate > 105:
        adjusted_base_stock += 12.0  # OPT_PARAM: {"initial": 12.0, "min": 5, "max": 25, "type": "float"}
    elif recent_demand_estimate < 85:
        adjusted_base_stock -= 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 35, "type": "float"}
    elif recent_demand_estimate < 95:
        adjusted_base_stock -= 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 20, "type": "float"}

    # Calculate order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Adaptive smoothing based on order size
    if raw_order > 250:
        smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.2, "max": 0.6, "type": "float"}
        order_amount = raw_order * smoothing_factor
    elif raw_order > 150:
        smoothing_factor = 0.65  # OPT_PARAM: {"initial": 0.65, "min": 0.4, "max": 0.8, "type": "float"}
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = raw_order

    # Round to nearest integer
    return order_amount
