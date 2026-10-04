# policy_hash: d4753bc0b1ce6fa5e104b64711ff5f4d3ec1fe374365d8f010766aea35476ebf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 91
# source_prompt_files: 1
# best_target_performance: 6319.68
# best_prompt_performance: 6319.72
# best_rel_error_pct: 0.000633
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_092603.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 1110.9317825511641  # OPT_PARAM: {"initial": 1110.9317825511641, "min": 700, "max": 1200, "type": "float"}
    safety_stock = 297.6592509817097  # OPT_PARAM: {"initial": 297.6592509817097, "min": 100, "max": 300, "type": "float"}
    demand_forecast = 130.64179040516765  # OPT_PARAM: {"initial": 130.64179040516765, "min": 90, "max": 140, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    min_order_quantity = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 0, "max": 50, "type": "float"}
    max_order_quantity = 300.0  # OPT_PARAM: {"initial": 300.0, "min": 100, "max": 400, "type": "float"}
    lost_sales_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Dynamic safety stock adjustment based on pipeline variability
    pipeline_std = 0.0
    if len(pipeline_orders) > 1:
        mean_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_std = (sum((q - mean_pipeline) ** 2 for q in pipeline_orders) / len(pipeline_orders)) ** 0.5

    # Adjust target based on lost sales weight (higher weight = more inventory)
    adjusted_safety = safety_stock * (1 + lost_sales_weight * pipeline_std / 100)

    # Calculate target inventory level
    target_inventory = base_stock + adjusted_safety

    # Calculate raw order quantity with demand forecast consideration
    raw_order = max(0, target_inventory - inventory_position + demand_forecast * 0.2)

    # Apply smoothing with demand-responsive adjustment
    if raw_order > 0:
        order_amount = max(min_order_quantity, raw_order * smoothing_factor)
    else:
        order_amount = 0

    # Cap maximum order size
    order_amount = min(order_amount, max_order_quantity)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
