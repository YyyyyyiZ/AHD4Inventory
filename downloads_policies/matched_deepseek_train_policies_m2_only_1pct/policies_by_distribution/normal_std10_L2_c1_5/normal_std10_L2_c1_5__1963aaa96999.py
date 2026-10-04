# policy_hash: 1963aaa96999461125e3254102649a1b64e22dc5d0d3dd4a094157f5c5f5a250
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1181.74
# best_prompt_performance: 1179.88
# best_rel_error_pct: 0.157395
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_051601.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 310.6991797723389  # OPT_PARAM: {"initial": 310.6991797723389, "min": 250, "max": 350, "type": "float"}
    safety_factor = 1.1821460734476437  # OPT_PARAM: {"initial": 1.1821460734476437, "min": 0.5, "max": 2.0, "type": "float"}
    demand_estimate = 97.37998831010779  # OPT_PARAM: {"initial": 97.37998831010779, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.29519953240431174  # OPT_PARAM: {"initial": 0.29519953240431174, "min": 0.0, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3213996493032338  # OPT_PARAM: {"initial": 0.3213996493032338, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus one period
    lead_time = len(pipeline_orders)
    expected_lead_time_demand = demand_estimate * (lead_time + 1)

    # Adjust base stock based on expected demand and safety factor
    adjusted_base_stock = base_stock + safety_factor * (expected_lead_time_demand - 100 * (lead_time + 1))

    # Calculate raw order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply pipeline smoothing
    if raw_order > 0 and pipeline_orders:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        smoothed_order = pipeline_weight * raw_order + (1 - pipeline_weight) * avg_pipeline
    else:
        smoothed_order = raw_order

    # Apply additional exponential smoothing to reduce volatility
    if hasattr(compute_order_amount, 'last_order'):
        final_order = (1 - smoothing_factor) * smoothed_order + smoothing_factor * compute_order_amount.last_order
    else:
        final_order = smoothed_order

    # Update last order (stationary through function attribute - allowed as it's just smoothing)
    compute_order_amount.last_order = final_order

    # Round to nearest integer
    order_amount = int(round(final_order))

    return order_amount
