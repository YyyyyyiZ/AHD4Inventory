# policy_hash: e6e8d9a5e8fbba4771470386c696a479aab2eb1b1be2520ea4512063d4181120
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 36
# source_prompt_files: 1
# best_target_performance: 5365.4
# best_prompt_performance: 5365.4
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_062942.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 697.2370356305343  # OPT_PARAM: {"initial": 697.2370356305343, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 147.20942699658474  # OPT_PARAM: {"initial": 147.20942699658474, "min": 0, "max": 300, "type": "float"}
    demand_estimate = 87.34114340357323  # OPT_PARAM: {"initial": 87.34114340357323, "min": 50, "max": 200, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline composition
    # Give more weight to near-term arrivals
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    pipeline_adjustment = weighted_pipeline / (sum(pipeline_orders) + 1e-6) if sum(pipeline_orders) > 0 else 1.0

    # Dynamic base stock calculation
    dynamic_base = base_stock * pipeline_adjustment + safety_stock

    # Calculate order amount
    order_amount = max(0, dynamic_base - inventory_position)

    # Smooth ordering: don't order more than expected demand + safety stock
    max_order = demand_estimate + safety_stock
    order_amount = min(order_amount, max_order)

    # Ensure integer order amount
    return order_amount
