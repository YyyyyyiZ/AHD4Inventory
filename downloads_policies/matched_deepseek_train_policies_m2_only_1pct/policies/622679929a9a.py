# policy_hash: 622679929a9ac8a6c5e7b3cabce7bde24d250a2219f1c27e7ed96e40d685a619
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 11627.47
# best_prompt_performance: 11627.47
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_022027.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 483.21574091819093  # OPT_PARAM: {"initial": 483.21574091819093, "min": 350, "max": 500, "type": "float"}
    safety_stock = 130.0  # OPT_PARAM: {"initial": 130.0, "min": 70, "max": 130, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.9, "max": 1.0, "type": "float"}
    demand_estimate = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 180, "type": "float"}
    order_cap_multiplier = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.5, "max": 2.5, "type": "float"}
    pipeline_discount_power = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.3, "max": 0.8, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    holding_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.5, "type": "float"}

    # Calculate weighted pipeline with discount
    weighted_pipeline = sum(p * (pipeline_weight ** (i * pipeline_discount_power))
                          for i, p in enumerate(pipeline_orders))

    # Inventory position with full weight on on-hand inventory
    inventory_position = on_hand_inventory * holding_weight + weighted_pipeline

    # Dynamic safety stock adjustment based on lost sales cost
    adjusted_safety_stock = safety_stock * lost_sales_weight

    # Target inventory level
    target_inventory = base_stock + adjusted_safety_stock

    # Order up to target
    order_amount = max(0, target_inventory - inventory_position)

    # Cap order by demand estimate with multiplier
    order_amount = min(order_amount, demand_estimate * order_cap_multiplier)

    # Ensure integer order amount
    return order_amount
