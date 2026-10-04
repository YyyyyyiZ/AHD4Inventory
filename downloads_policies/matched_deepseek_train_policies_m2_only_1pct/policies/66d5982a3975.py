# policy_hash: 66d5982a397572faafe84dde8ffdf9ada8421fcefeb0f0a8abb3ada227d77bb6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 1357.44
# best_prompt_performance: 1357.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_065727.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 306.93256077598073  # OPT_PARAM: {"initial": 306.93256077598073, "min": 200, "max": 350, "type": "float"}
    safety_stock = 43.46157246688976  # OPT_PARAM: {"initial": 43.46157246688976, "min": 20, "max": 60, "type": "float"}
    adjustment_factor = 0.7458705363263937  # OPT_PARAM: {"initial": 0.7458705363263937, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory with dynamic safety stock
    # Reduce safety stock when pipeline has significant incoming orders
    pipeline_coverage = sum(pipeline_orders[:1])  # Only consider immediate arrival
    adjusted_safety = max(5.0, safety_stock - smoothing_factor * pipeline_coverage)

    target_inventory = base_stock + adjusted_safety

    # Calculate order amount with adjustment factor
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid large order swings
    if raw_order > 0:
        order_amount = int(round(raw_order * adjustment_factor))
    else:
        order_amount = 0

    return order_amount
