# policy_hash: cc18bdad7475afbb559f99247dd4e3bb4f6c66f28e7e44cea5a6d341edec5325
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 810.73
# best_prompt_performance: 810.73
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_201156.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 663.9895492381544  # OPT_PARAM: {"initial": 663.9895492381544, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 58.23790006433689  # OPT_PARAM: {"initial": 58.23790006433689, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 124.54477560935176  # OPT_PARAM: {"initial": 124.54477560935176, "min": 50, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Cap the order amount to avoid excessive ordering
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 500, "type": "float"}
    order_amount = min(order_amount, max_order)

    # Add dynamic adjustment based on pipeline variability
    pipeline_std_factor = 0.1375974616446901  # OPT_PARAM: {"initial": 0.1375974616446901, "min": 0.0, "max": 2.0, "type": "float"}
    if len(pipeline_orders) > 1:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_variance = sum((x - pipeline_mean) ** 2 for x in pipeline_orders) / len(pipeline_orders)
        pipeline_std = pipeline_variance ** 0.5
        safety_adjustment = pipeline_std_factor * pipeline_std
        target_position += safety_adjustment
        order_amount = max(0, target_position - inventory_position)
        order_amount = min(order_amount, max_order)

    # Add minimum order quantity to maintain pipeline flow
    min_order = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 50, "type": "float"}
    if order_amount > 0 and order_amount < min_order:
        order_amount = min_order

    # Round to nearest integer as required
    return order_amount
