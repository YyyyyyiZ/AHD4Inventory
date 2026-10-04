# policy_hash: db4e7d29edfea449b463f3e6cb819e8c704aef127aae29f8cb0cbb936ad20250
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 5881.4
# best_prompt_performance: 5881.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_070949.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 282.9456370870799  # OPT_PARAM: {"initial": 282.9456370870799, "min": 200, "max": 350, "type": "float"}
    safety_stock = 82.94563708707932  # OPT_PARAM: {"initial": 82.94563708707932, "min": 60, "max": 120, "type": "float"}
    pipeline_factor = 0.8312261031365031  # OPT_PARAM: {"initial": 0.8312261031365031, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing = 0.37428274738609557  # OPT_PARAM: {"initial": 0.37428274738609557, "min": 0.3, "max": 0.7, "type": "float"}
    demand_estimate = 125.0  # OPT_PARAM: {"initial": 125.0, "min": 100, "max": 160, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline with discount factor
    effective_pipeline = sum(pipeline_orders) * pipeline_factor

    # Target inventory position: base + safety - effective pipeline
    target_position = base_stock + safety_stock - effective_pipeline

    # Ensure minimum target based on demand variability
    min_target = demand_estimate * 1.8
    target_position = max(target_position, min_target)

    # Order needed to reach target
    order_needed = target_position - inventory_position

    # Apply smoothing with reasonable bounds
    if order_needed > 0:
        # Cap order to avoid overordering
        max_order = demand_estimate * 2.2
        capped_order = min(order_needed, max_order)
        smoothed_order = capped_order * smoothing
        order_amount = int(round(smoothed_order))
    else:
        order_amount = 0

    return order_amount
