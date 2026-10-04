# policy_hash: ddd29a466ea535c04d670669b987fd5ccafbb2f39352dca629764ad0a0bd1b72
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 6068.9
# best_prompt_performance: 6068.9
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_054703.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.30814257452215  # OPT_PARAM: {"initial": 449.30814257452215, "min": 200, "max": 600, "type": "float"}
    pipeline_weight = 0.7071356560728405  # OPT_PARAM: {"initial": 0.7071356560728405, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.13819633738534298  # OPT_PARAM: {"initial": 0.13819633738534298, "min": 0.1, "max": 1.0, "type": "float"}
    safety_stock = 176.37035217390527  # OPT_PARAM: {"initial": 176.37035217390527, "min": 50, "max": 300, "type": "float"}
    demand_anticipation = 0.03688537349437826  # OPT_PARAM: {"initial": 0.03688537349437826, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate effective pipeline with weighted adjustment
    effective_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on upcoming pipeline arrivals
    upcoming_arrivals = sum(pipeline_orders[:3]) if len(pipeline_orders) >= 3 else sum(pipeline_orders)
    adjusted_base = base_stock + safety_stock - demand_anticipation * upcoming_arrivals

    # Calculate target order
    target = max(0, adjusted_base - inventory_position)

    # Apply smoothing with threshold
    if target > 10:  # Small threshold to avoid tiny orders
        order_amount = smoothing_factor * target
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
