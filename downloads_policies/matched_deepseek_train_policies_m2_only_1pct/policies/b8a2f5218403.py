# policy_hash: b8a2f5218403a4edf65dbd3d767a0718184b449a694cec6b33cce7beace4467f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 1257.74
# best_prompt_performance: 1259.16
# best_rel_error_pct: 0.112901
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_051114.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 307.8137526091114  # OPT_PARAM: {"initial": 307.8137526091114, "min": 200, "max": 400, "type": "float"}
    safety_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.5, "type": "float"}
    demand_estimate = 103.46287835676885  # OPT_PARAM: {"initial": 103.46287835676885, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.3158274288294702  # OPT_PARAM: {"initial": 0.3158274288294702, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus one period
    lead_time = len(pipeline_orders)
    expected_lead_time_demand = demand_estimate * (lead_time + 1)

    # Adjust base stock based on expected demand and safety factor
    adjusted_base_stock = base_stock + safety_factor * (expected_lead_time_demand - 100 * (lead_time + 1))

    # Calculate order amount with pipeline consideration
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply pipeline weighting to smooth orders
    if order_amount > 0 and pipeline_orders:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        order_amount = pipeline_weight * order_amount + (1 - pipeline_weight) * avg_pipeline

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
