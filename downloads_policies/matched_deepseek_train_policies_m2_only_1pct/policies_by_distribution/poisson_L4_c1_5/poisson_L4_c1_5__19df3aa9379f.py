# policy_hash: 19df3aa9379fd94d585e87c207f46a954453fc384893c2616c74d8ced304ed50
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 1228.36
# best_prompt_performance: 1228.36
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_004915.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 474.17984103534354  # OPT_PARAM: {"initial": 474.17984103534354, "min": 400, "max": 550, "type": "float"}
    safety_stock = 34.17984103534361  # OPT_PARAM: {"initial": 34.17984103534361, "min": 20, "max": 60, "type": "float"}
    demand_forecast = 96.08661652362358  # OPT_PARAM: {"initial": 96.08661652362358, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.2, "type": "float"}
    pipeline_weight = 0.8491725259086083  # OPT_PARAM: {"initial": 0.8491725259086083, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Dynamic order-up-to level based on pipeline status
    pipeline_total = sum(pipeline_orders)
    pipeline_factor = max(0.7, min(1.3, 1.0 - (pipeline_total - 4*demand_forecast)/(20*demand_forecast)))
    order_up_to = base_stock + safety_stock * pipeline_factor

    # Calculate order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Smooth ordering with tighter bounds
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Apply ceiling rounding to ensure adequate coverage
    order_amount = max(0, int(smoothed_order + 0.5))

    return order_amount
