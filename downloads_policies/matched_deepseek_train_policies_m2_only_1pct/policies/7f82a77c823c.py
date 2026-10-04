# policy_hash: 7f82a77c823c09545c446a37f001eb157780c283809a97999228897b5c315676
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 10165.17
# best_prompt_performance: 10165.17
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_234032.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 346.6897595758282  # OPT_PARAM: {"initial": 346.6897595758282, "min": 200, "max": 500, "type": "float"}
    safety_stock = 21.689759575827406  # OPT_PARAM: {"initial": 21.689759575827406, "min": 10, "max": 60, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing = 0.3182849615721879  # OPT_PARAM: {"initial": 0.3182849615721879, "min": 0.2, "max": 0.8, "type": "float"}
    demand_anticipation = 0.30948807574636017  # OPT_PARAM: {"initial": 0.30948807574636017, "min": 0.1, "max": 0.8, "type": "float"}
    lost_sales_weight = 1.2226655718495267  # OPT_PARAM: {"initial": 1.2226655718495267, "min": 0.8, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline for demand anticipation
    weighted_pipeline = 0
    if len(pipeline_orders) > 0:
        for i, q in enumerate(pipeline_orders):
            weight = pipeline_weight ** i
            weighted_pipeline += q * weight

    # Adjusted demand anticipation
    anticipated_demand = demand_anticipation * weighted_pipeline if len(pipeline_orders) > 0 else 0

    # Dynamic target with lost-sales adjustment
    target = base_stock + safety_stock + anticipated_demand

    # Adjust for lost-sales cost ratio (p=5, h=1)
    cost_adjusted_target = target * lost_sales_weight

    # Calculate order needed
    order_needed = max(0, cost_adjusted_target - inventory_position)

    # Apply smoothing with threshold
    if order_needed > 0:
        order_amount = smoothing * order_needed
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
