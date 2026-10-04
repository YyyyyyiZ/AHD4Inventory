# policy_hash: bf17adbbff51a800c6f80d8b82859b5ad3198714c8438ce04572e37bd480c1d0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 35
# source_prompt_files: 1
# best_target_performance: 4452.66
# best_prompt_performance: 4452.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_014519.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 741.868850830545  # OPT_PARAM: {"initial": 741.868850830545, "min": 400, "max": 900, "type": "float"}
    safety_stock = 171.96885083057091  # OPT_PARAM: {"initial": 171.96885083057091, "min": 0, "max": 200, "type": "float"}
    forecast_horizon = 4  # OPT_PARAM: {"initial": 4, "min": 1, "max": 6, "type": "int"}
    demand_adj_factor = 1.3  # OPT_PARAM: {"initial": 1.3, "min": 0.8, "max": 1.3, "type": "float"}

    # Calculate pipeline sum
    pipeline_sum = sum(pipeline_orders)

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
    order_up_to = max(0, adjusted_base - on_hand_inventory - pipeline_sum)

    # Apply smoothing to avoid extreme order variations
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    min_order_threshold = 5  # OPT_PARAM: {"initial": 5, "min": 0, "max": 20, "type": "int"}

    if order_up_to < min_order_threshold:
        order_amount = 0
    else:
        # Smooth the order amount
        order_amount = int(order_up_to * smoothing_factor)

    return order_amount
