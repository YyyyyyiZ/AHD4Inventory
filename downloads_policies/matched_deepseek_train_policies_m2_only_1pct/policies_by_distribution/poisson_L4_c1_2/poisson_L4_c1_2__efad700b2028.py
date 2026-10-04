# policy_hash: efad700b20289fefceb4d3724294ded0a47277f3964d6ceae7d9307eab43e3c2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 737.41
# best_prompt_performance: 737.41
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_034928.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 479.86868730507103  # OPT_PARAM: {"initial": 479.86868730507103, "min": 400, "max": 550, "type": "float"}
    safety_stock = 43.71756344423181  # OPT_PARAM: {"initial": 43.71756344423181, "min": 30, "max": 70, "type": "float"}
    demand_forecast = 96.43847688660351  # OPT_PARAM: {"initial": 96.43847688660351, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.9155466066305659  # OPT_PARAM: {"initial": 0.9155466066305659, "min": 0.5, "max": 1.0, "type": "float"}
    order_threshold = 0.3478183968421231  # OPT_PARAM: {"initial": 0.3478183968421231, "min": 0.1, "max": 0.5, "type": "float"}
    max_order_multiplier = 1.2178611936495078  # OPT_PARAM: {"initial": 1.2178611936495078, "min": 1.0, "max": 2.0, "type": "float"}
    pipeline_correction = 1.0215688475104703  # OPT_PARAM: {"initial": 1.0215688475104703, "min": 0.7, "max": 1.1, "type": "float"}

    # Calculate weighted pipeline inventory
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Calculate inventory position with pipeline correction
    inventory_position = on_hand_inventory + pipeline_correction * weighted_pipeline

    # Calculate target inventory level
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)
    target_inventory = expected_lead_time_demand + safety_stock

    # Use base_stock as primary target, adjusted by safety stock
    order_up_to = 0.8 * base_stock + 0.2 * target_inventory

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply maximum order cap
    capped_order = min(raw_order, max_order_multiplier * demand_forecast)

    # Apply smoothing only for significant orders
    if capped_order > demand_forecast * order_threshold:
        order_amount = smoothing_factor * capped_order + (1 - smoothing_factor) * demand_forecast
    else:
        order_amount = capped_order

    # Ensure non-negative integer order
    return order_amount
