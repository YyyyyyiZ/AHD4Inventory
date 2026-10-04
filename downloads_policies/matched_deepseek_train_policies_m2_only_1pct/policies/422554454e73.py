# policy_hash: 422554454e7368730d53a1c17940bfc64b8c5601cddaf49074b665ed7b14a376
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 25
# source_prompt_files: 1
# best_target_performance: 10160.88
# best_prompt_performance: 10160.87
# best_rel_error_pct: 0.000098
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_233357.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 376.15484811253526  # OPT_PARAM: {"initial": 376.15484811253526, "min": 100, "max": 800, "type": "float"}
    safety_stock = 94.89813883499004  # OPT_PARAM: {"initial": 94.89813883499004, "min": 20, "max": 200, "type": "float"}
    smoothing_factor = 0.350426788516652  # OPT_PARAM: {"initial": 0.350426788516652, "min": 0.3, "max": 1.0, "type": "float"}
    demand_anticipation_factor = 0.14177633913231813  # OPT_PARAM: {"initial": 0.14177633913231813, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    # (pipeline_orders[0] arrives now, pipeline_orders[1] arrives next period)
    upcoming_arrivals = pipeline_orders[0] + pipeline_orders[1] if len(pipeline_orders) > 1 else pipeline_orders[0]

    # Adjust target based on upcoming arrivals to anticipate demand
    adjusted_target = base_stock + safety_stock - demand_anticipation_factor * upcoming_arrivals

    # Calculate raw order amount
    raw_order = max(0, adjusted_target - inventory_position)

    # Apply smoothing to avoid extreme fluctuations
    if raw_order > 0:
        order_amount = smoothing_factor * raw_order
    else:
        order_amount = 0.0

    # Round to nearest integer
    return order_amount
