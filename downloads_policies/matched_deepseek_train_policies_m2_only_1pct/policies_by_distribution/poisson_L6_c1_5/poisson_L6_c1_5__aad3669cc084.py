# policy_hash: aad3669cc0840b0e4ed14bd317b3c3c99bc913b4d292d37431ce97c89594f8a4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 33
# source_prompt_files: 1
# best_target_performance: 1189.94
# best_prompt_performance: 1190.22
# best_rel_error_pct: 0.023531
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_020657.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 750.0  # OPT_PARAM: {"initial": 750.0, "min": 600, "max": 900, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    safety_factor = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 1.0, "max": 2.5, "type": "float"}
    max_order_cap = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 200, "type": "float"}
    min_order_cap = 14.38840919144308  # OPT_PARAM: {"initial": 14.38840919144308, "min": 10, "max": 50, "type": "float"}
    demand_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust demand estimate using weighted pipeline information
    if len(pipeline_orders) >= 3:
        recent_orders = sum(pipeline_orders[-3:]) / 3
    else:
        recent_orders = sum(pipeline_orders) / max(len(pipeline_orders), 1)

    # More aggressive smoothing towards recent pipeline activity
    adjusted_demand = demand_estimate * (1 - demand_smoothing) + recent_orders * demand_smoothing

    # Calculate expected demand during lead time
    expected_lead_time_demand = adjusted_demand * len(pipeline_orders)

    # Calculate safety stock with adjusted factor
    safety_stock = safety_factor * adjusted_demand

    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply pipeline-weighted adjustment
    if order_amount > 0:
        pipeline_ratio = sum(pipeline_orders[-2:]) / (2 * adjusted_demand) if len(pipeline_orders) >= 2 else 1.0
        order_amount *= (1 - pipeline_weight) + pipeline_weight * pipeline_ratio

    # Apply order caps
    order_amount = min(order_amount, max_order_cap)

    # Apply minimum order threshold
    if order_amount > 0 and order_amount < min_order_cap:
        order_amount = min_order_cap

    # Ensure integer output
    return order_amount
