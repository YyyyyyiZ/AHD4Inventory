# policy_hash: 48f5a0fcefbfe954234dbc4b98ec9bb2a277595b8a8745821cba090853018ce4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 5884.32
# best_prompt_performance: 5883.92
# best_rel_error_pct: 0.006798
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_070137.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 336.4710819262584  # OPT_PARAM: {"initial": 336.4710819262584, "min": 250, "max": 450, "type": "float"}
    safety_stock = 46.471081926255536  # OPT_PARAM: {"initial": 46.471081926255536, "min": 30, "max": 120, "type": "float"}
    pipeline_factor = 0.9763099199158675  # OPT_PARAM: {"initial": 0.9763099199158675, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing = 0.3198598599662232  # OPT_PARAM: {"initial": 0.3198598599662232, "min": 0.3, "max": 1.0, "type": "float"}
    demand_estimate = 113.04762774820068  # OPT_PARAM: {"initial": 113.04762774820068, "min": 80, "max": 180, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline coverage
    pipeline_coverage = sum(pipeline_orders) * pipeline_factor

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock - pipeline_coverage

    # Ensure minimum target covers lead time demand
    min_target = demand_estimate * 2.5
    target_inventory = max(target_inventory, min_target)

    # Calculate order needed
    order_needed = target_inventory - inventory_position

    # Apply smoothing with reasonable capping
    if order_needed > 0:
        # Cap order to avoid overordering
        max_order = demand_estimate * 3.0
        capped_order = min(order_needed, max_order)
        smoothed_order = capped_order * smoothing
        order_amount = int(round(smoothed_order))
    else:
        order_amount = 0

    return order_amount
