# policy_hash: da623782155cfed7ac24bf27b310aab91d19452579c5cc9257db44273c5d204b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1179.18
# best_prompt_performance: 1178.66
# best_rel_error_pct: 0.044098
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_052248.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 297.4181695810949  # OPT_PARAM: {"initial": 297.4181695810949, "min": 250, "max": 320, "type": "float"}
    safety_factor = 0.8503367472991941  # OPT_PARAM: {"initial": 0.8503367472991941, "min": 0.8, "max": 1.3, "type": "float"}
    demand_estimate = 104.04054305398263  # OPT_PARAM: {"initial": 104.04054305398263, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.0, "max": 0.3, "type": "float"}
    smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 0.4, "type": "float"}

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
