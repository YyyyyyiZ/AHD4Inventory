# policy_hash: b2e11468a9dfcb0dc57612401ea99b1ef3f4f2de70cbb66616c23c1ebdcb4154
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 20
# source_prompt_files: 1
# best_target_performance: 4378.0
# best_prompt_performance: 4368.32
# best_rel_error_pct: 0.221106
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_013659.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 670.7802872116035  # OPT_PARAM: {"initial": 670.7802872116035, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 128.77529145010934  # OPT_PARAM: {"initial": 128.77529145010934, "min": 0, "max": 500, "type": "float"}
    forecast_horizon = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 6, "type": "int"}
    demand_adj_factor = 0.9582002333762262  # OPT_PARAM: {"initial": 0.9582002333762262, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate pipeline sum
    pipeline_sum = sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of last few pipeline arrivals as demand proxy
    recent_arrivals = pipeline_orders[:forecast_horizon]
    if len(recent_arrivals) > 0:
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
        forecast_demand = avg_recent_demand * demand_adj_factor
    else:
        forecast_demand = 0

    # Calculate adjusted base stock level
    adjusted_base = base_stock + safety_stock + forecast_demand

    # Calculate order-up-to level
    order_up_to = max(0, adjusted_base - on_hand_inventory - pipeline_sum)

    # Apply smoothing to avoid extreme order variations
    smoothing_factor = 0.2517842984215196  # OPT_PARAM: {"initial": 0.2517842984215196, "min": 0.1, "max": 1.0, "type": "float"}
    min_order_threshold = 10  # OPT_PARAM: {"initial": 10, "min": 0, "max": 100, "type": "int"}

    if order_up_to < min_order_threshold:
        order_amount = 0
    else:
        # Smooth the order amount
        order_amount = int(order_up_to * smoothing_factor)

    return order_amount
