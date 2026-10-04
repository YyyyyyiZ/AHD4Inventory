# policy_hash: 5c9588bf8cdcaf58a98a7113e3dbbf9291f63309ffa8fd08dfaa2c3c3f12a540
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 799.61
# best_prompt_performance: 799.77
# best_rel_error_pct: 0.020010
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_052024.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 700.5999975333718  # OPT_PARAM: {"initial": 700.5999975333718, "min": 550, "max": 750, "type": "float"}
    safety_stock = 86.51206940537527  # OPT_PARAM: {"initial": 86.51206940537527, "min": 70, "max": 110, "type": "float"}
    demand_estimate = 102.10308257397361  # OPT_PARAM: {"initial": 102.10308257397361, "min": 95, "max": 105, "type": "float"}
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 140, "type": "float"}
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 10, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.4, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 0.9, "type": "float"}
    variance_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate pipeline-adjusted target
    pipeline_sum = sum(pipeline_orders)
    pipeline_adjustment = pipeline_weight * (pipeline_sum - expected_demand_during_leadtime)

    # Simple variance adjustment
    if pipeline_orders:
        avg_pipeline = pipeline_sum / len(pipeline_orders)
        variance = sum((q - avg_pipeline) ** 2 for q in pipeline_orders) / len(pipeline_orders)
        variance_adjustment = variance_factor * (variance ** 0.5)
    else:
        variance_adjustment = 0

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock - pipeline_adjustment + variance_adjustment

    # Calculate base order
    raw_order = target_position - inventory_position
    order_amount = max(0, raw_order)

    # Apply smoothing
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Apply base stock constraint
    if inventory_position + order_amount > base_stock:
        order_amount = max(0, base_stock - inventory_position)

    # Apply practical bounds
    order_amount = min(order_amount, max_order)
    order_amount = max(order_amount, min_order)

    return order_amount
