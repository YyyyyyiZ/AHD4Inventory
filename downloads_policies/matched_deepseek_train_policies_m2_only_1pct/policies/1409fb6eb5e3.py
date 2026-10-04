# policy_hash: 1409fb6eb5e3f02036203aa8ba2983cfdf1ae69686af5b784dc9c4447d320aa6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 10798.44
# best_prompt_performance: 10798.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_072213.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 310.37405516143  # OPT_PARAM: {"initial": 310.37405516143, "min": 100, "max": 600, "type": "float"}
    safety_stock = 45.0520771380122  # OPT_PARAM: {"initial": 45.0520771380122, "min": 0, "max": 150, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use weighted average of recent pipeline arrivals for demand forecast
    # Give more weight to more recent arrivals
    forecast_demand = 0
    if pipeline_orders:
        weights = [0.6, 0.4] if len(pipeline_orders) >= 2 else [1.0]
        weighted_sum = 0
        for i, w in enumerate(weights):
            if i < len(pipeline_orders):
                weighted_sum += pipeline_orders[i] * w
        forecast_demand = weighted_sum * demand_forecast_factor

    # Adjust base stock based on forecast and pipeline status
    pipeline_avg = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_adjustment = pipeline_avg * pipeline_weight

    adjusted_base_stock = base_stock * (1 - smoothing_factor) + (forecast_demand + pipeline_adjustment) * smoothing_factor

    # Calculate target inventory position with safety stock
    target_position = adjusted_base_stock + safety_stock

    # Calculate order amount with smoother adjustment
    gap = target_position - inventory_position
    if gap > 0:
        # Order the full gap but apply small smoothing
        order_amount = max(0, gap)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
