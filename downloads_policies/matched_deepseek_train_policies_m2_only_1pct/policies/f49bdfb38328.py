# policy_hash: f49bdfb38328d86eda904274f606dc007990f7422b58fdced311bffd0338b97b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 10167.65
# best_prompt_performance: 10167.65
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_233036.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 441.95559698654597  # OPT_PARAM: {"initial": 441.95559698654597, "min": 300, "max": 600, "type": "float"}
    safety_stock = 16.955596986544236  # OPT_PARAM: {"initial": 16.955596986544236, "min": 0, "max": 100, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 1.0, "type": "float"}
    smoothing = 0.3026082017354123  # OPT_PARAM: {"initial": 0.3026082017354123, "min": 0.1, "max": 1.0, "type": "float"}
    demand_anticipation = 0.48673775510034106  # OPT_PARAM: {"initial": 0.48673775510034106, "min": 0.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline for demand anticipation
    weighted_pipeline = 0
    if len(pipeline_orders) > 0:
        for i, q in enumerate(pipeline_orders):
            weight = pipeline_weight ** i  # More weight to recent orders
            weighted_pipeline += q * weight

    # Simple demand anticipation based on recent pipeline
    anticipated_demand = demand_anticipation * weighted_pipeline if len(pipeline_orders) > 0 else 0

    # Dynamic target adjustment
    target = base_stock + safety_stock + anticipated_demand

    # Calculate order needed
    order_needed = max(0, target - inventory_position)

    # Apply smoothing
    if order_needed > 0:
        order_amount = smoothing * order_needed
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
