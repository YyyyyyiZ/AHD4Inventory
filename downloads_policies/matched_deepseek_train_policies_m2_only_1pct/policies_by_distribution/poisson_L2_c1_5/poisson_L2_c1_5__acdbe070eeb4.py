# policy_hash: acdbe070eeb47aa23da287bce2e8fed03e5a4ef283c113c65f2acdeddd3b0d28
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 28
# source_prompt_files: 2
# best_target_performance: 1253.8
# best_prompt_performance: 1253.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031240.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 250.0  # OPT_PARAM: {"initial": 250.0, "min": 250, "max": 350, "type": "float"}
    safety_stock = 17.36848011801581  # OPT_PARAM: {"initial": 17.36848011801581, "min": 15, "max": 40, "type": "float"}
    demand_estimate = 98.85462213829011  # OPT_PARAM: {"initial": 98.85462213829011, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.4, "type": "float"}
    lost_sales_multiplier = 2.5  # OPT_PARAM: {"initial": 2.5, "min": 1.2, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with lost-sales adjustment
    # Higher lost-sales cost (p=5 vs h=1) suggests we should carry more inventory
    target_level = base_stock + safety_stock * lost_sales_multiplier

    # Base order amount
    base_order = max(0, target_level - inventory_position)

    # Pipeline adjustment with stronger emphasis
    if len(pipeline_orders) > 0:
        expected_pipeline = demand_estimate * len(pipeline_orders)
        current_pipeline = sum(pipeline_orders)
        pipeline_deficit = max(0, expected_pipeline - current_pipeline)
        base_order += pipeline_weight * pipeline_deficit

    # Apply smoothing with demand forecast
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_estimate

    # Ensure non-negative integer order
    order_amount = max(0, int(round(order_amount)))

    return order_amount
