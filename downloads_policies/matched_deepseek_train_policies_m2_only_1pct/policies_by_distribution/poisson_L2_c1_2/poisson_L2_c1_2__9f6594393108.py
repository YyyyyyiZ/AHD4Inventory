# policy_hash: 9f6594393108f14ae290bc7c6b6ec5387891cb955dc5aac1c2eeac55b196fac8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1956.08
# best_prompt_performance: 1956.08
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_021628.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 147.25952461251987  # OPT_PARAM: {"initial": 147.25952461251987, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 89.04811581684228  # OPT_PARAM: {"initial": 89.04811581684228, "min": 0, "max": 100, "type": "float"}
    demand_buffer = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate effective inventory position
    effective_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    if len(pipeline_orders) > 0:
        # Use average of recent pipeline orders as demand proxy
        recent_avg = sum(pipeline_orders) / len(pipeline_orders)
        demand_estimate = recent_avg * demand_buffer
    else:
        demand_estimate = 100.0  # fallback

    # Adjust base stock based on pipeline status
    if len(pipeline_orders) > 0:
        # If we have low pipeline, increase order slightly
        pipeline_ratio = sum(pipeline_orders) / (len(pipeline_orders) * 100)
        adjusted_base = base_stock * (0.9 + 0.2 * pipeline_ratio)
    else:
        adjusted_base = base_stock

    # Calculate target inventory position
    target_position = adjusted_base + safety_stock + demand_estimate

    # Calculate order amount
    order_amount = max(0, target_position - effective_inventory)

    # Round to nearest integer (as order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
