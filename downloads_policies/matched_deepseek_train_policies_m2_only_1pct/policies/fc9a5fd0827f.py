# policy_hash: fc9a5fd0827f04f0b7364dd046e1968e84e07186d35145c154a04936138c8ebd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 11387.46
# best_prompt_performance: 11384.86
# best_rel_error_pct: 0.022832
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_021045.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 451.5779791183043  # OPT_PARAM: {"initial": 451.5779791183043, "min": 300, "max": 600, "type": "float"}
    safety_stock = 81.57797911830444  # OPT_PARAM: {"initial": 81.57797911830444, "min": 50, "max": 150, "type": "float"}
    pipeline_weight = 0.9776565582488594  # OPT_PARAM: {"initial": 0.9776565582488594, "min": 0.8, "max": 1.0, "type": "float"}
    inventory_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    demand_estimate = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 50, "max": 200, "type": "float"}

    # Calculate total pipeline with discount for future arrivals
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Inventory position
    inventory_position = on_hand_inventory * inventory_weight + weighted_pipeline

    # Simple base stock policy with safety stock
    target_inventory = base_stock + safety_stock

    # Order up to target, but don't order more than expected demand plus safety
    order_amount = max(0, target_inventory - inventory_position)

    # Cap order by reasonable demand estimate to avoid overordering
    order_amount = min(order_amount, demand_estimate * 2)

    return order_amount
