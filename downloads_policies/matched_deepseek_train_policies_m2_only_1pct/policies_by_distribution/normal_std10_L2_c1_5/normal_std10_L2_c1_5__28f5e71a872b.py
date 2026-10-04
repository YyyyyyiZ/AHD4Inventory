# policy_hash: 28f5e71a872b85f1728c30a7805380f044fb20a5db39cc81a18967028a61a684
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 1175.96
# best_prompt_performance: 1177.68
# best_rel_error_pct: 0.146263
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_053845.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 298.35925238803395  # OPT_PARAM: {"initial": 298.35925238803395, "min": 250, "max": 320, "type": "float"}
    demand_estimate = 102.28473638004417  # OPT_PARAM: {"initial": 102.28473638004417, "min": 95, "max": 105, "type": "float"}
    safety_factor = 1.284199638742427  # OPT_PARAM: {"initial": 1.284199638742427, "min": 0.8, "max": 1.5, "type": "float"}
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

    # Apply exponential smoothing
    if hasattr(compute_order_amount, 'last_order'):
        final_order = (1 - smoothing_factor) * smoothed_order + smoothing_factor * compute_order_amount.last_order
    else:
        final_order = smoothed_order

    # Update last order
    compute_order_amount.last_order = final_order

    # Round to nearest integer
    order_amount = int(round(final_order))

    return order_amount
