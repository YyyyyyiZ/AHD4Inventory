# policy_hash: 1597357353b21b69582bf2ba7bf7260167bb025bb0031d9b78db53141730ebcb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 69
# source_prompt_files: 1
# best_target_performance: 4080.86
# best_prompt_performance: 4080.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_015614.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 651.7641191152344  # OPT_PARAM: {"initial": 651.7641191152344, "min": 500, "max": 800, "type": "float"}
    safety_stock = 121.764119115235  # OPT_PARAM: {"initial": 121.764119115235, "min": 80, "max": 180, "type": "float"}
    forecast_horizon = 3  # OPT_PARAM: {"initial": 3, "min": 2, "max": 6, "type": "int"}
    demand_adj_factor = 1.2909912326164656  # OPT_PARAM: {"initial": 1.2909912326164656, "min": 0.9, "max": 1.3, "type": "float"}

    # Calculate pipeline sum
    pipeline_sum = sum(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + pipeline_sum

    # Simple demand forecast based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:forecast_horizon]
    if len(recent_arrivals) > 0:
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
        forecast_demand = avg_recent_demand * demand_adj_factor
    else:
        forecast_demand = 0

    # Calculate adjusted base stock level
    adjusted_base = base_stock + safety_stock + forecast_demand

    # Calculate order-up-to level
    order_up_to = max(0, adjusted_base - inventory_position)

    # Apply smoothing with dynamic factor based on order size
    smoothing_factor = 0.41521458159410396  # OPT_PARAM: {"initial": 0.41521458159410396, "min": 0.2, "max": 0.6, "type": "float"}
    min_order_threshold = 8  # OPT_PARAM: {"initial": 8, "min": 0, "max": 20, "type": "int"}

    if order_up_to < min_order_threshold:
        order_amount = 0
    else:
        # Dynamic smoothing: larger orders get less smoothing
        dynamic_factor = smoothing_factor * (1.0 - min(0.5, order_up_to / 1000.0))
        order_amount = int(order_up_to * dynamic_factor)

    return order_amount
