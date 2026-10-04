# policy_hash: dab8ff7378de9a5827dcec0a174bca2893f5545e3afdf17d83361f5bdf74e52c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 11691.4
# best_prompt_performance: 11691.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_101528.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 379.92984090550215  # OPT_PARAM: {"initial": 379.92984090550215, "min": 200, "max": 600, "type": "float"}
    safety_factor = 1.0464418077430384  # OPT_PARAM: {"initial": 1.0464418077430384, "min": 0.8, "max": 1.5, "type": "float"}
    smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    lead_time = 6

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust target based on pipeline composition
    near_term_arrivals = sum(pipeline_orders[:2])  # next 2 periods
    far_term_arrivals = sum(pipeline_orders[2:])   # periods 3-6

    # Dynamic adjustment: if we have little coming soon, increase target slightly
    pipeline_factor = 1.3  # Optimized
    if near_term_arrivals < 0.3 * base_stock:
        pipeline_factor = 1.15  # OPT_PARAM: {"initial": 1.15, "min": 1.0, "max": 1.3, "type": "float"}

    target_inventory = base_stock * safety_factor * pipeline_factor

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing based on recent orders
    if pipeline_orders:
        recent_orders = pipeline_orders[-2:] if len(pipeline_orders) >= 2 else [pipeline_orders[-1]]
        avg_recent = sum(recent_orders) / len(recent_orders)
        smoothed_order = smoothing * order_amount + (1 - smoothing) * avg_recent
        order_amount = max(0, smoothed_order)

    # Round to integer
    order_amount = int(round(order_amount))

    return order_amount
