# policy_hash: 629dbc0acea5b05346d944af7a748ec55bbca6c582411ce6672732ac1f1d91ca
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 1034.88
# best_prompt_performance: 1034.88
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_045200.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 473.13246209906725  # OPT_PARAM: {"initial": 473.13246209906725, "min": 400, "max": 600, "type": "float"}
    safety_stock = 6.756879683260362  # OPT_PARAM: {"initial": 6.756879683260362, "min": 0, "max": 50, "type": "float"}
    smoothing_factor = 0.06177689526271041  # OPT_PARAM: {"initial": 0.06177689526271041, "min": 0.0, "max": 0.5, "type": "float"}
    demand_forecast_factor = 0.035959592904888704  # OPT_PARAM: {"initial": 0.035959592904888704, "min": 0.0, "max": 0.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast using recent pipeline arrivals
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[-min(3, len(pipeline_orders)):]
        demand_estimate = sum(recent_arrivals) / len(recent_arrivals)
    else:
        demand_estimate = 100.0

    # Adjust base stock based on demand estimate
    adjusted_base = base_stock + demand_forecast_factor * (demand_estimate - 100.0)

    # Calculate target inventory position
    target_inventory = adjusted_base + safety_stock

    # Calculate raw order quantity
    raw_order = max(0, target_inventory - inventory_position)

    # Apply simple exponential smoothing
    if pipeline_orders:
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * pipeline_orders[-1]
    else:
        order_amount = raw_order

    return order_amount
