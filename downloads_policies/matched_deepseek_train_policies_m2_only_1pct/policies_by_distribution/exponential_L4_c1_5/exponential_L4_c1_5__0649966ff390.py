# policy_hash: 0649966ff390e8eac9795bfa4274b1693f0d03b86fffc90a104543bc78a0319b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 11396.96
# best_prompt_performance: 11396.96
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_043352.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 416.55658251970243  # OPT_PARAM: {"initial": 416.55658251970243, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 67.55664873992389  # OPT_PARAM: {"initial": 67.55664873992389, "min": 0, "max": 300, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    if len(pipeline_orders) > 0:
        recent_arrivals = pipeline_orders[:min(3, len(pipeline_orders))]
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = 0

    # Adjust base stock level based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate target inventory position
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Smooth ordering by considering previous orders in pipeline
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        smoothing_factor = 0.8065671038147629  # OPT_PARAM: {"initial": 0.8065671038147629, "min": 0, "max": 1, "type": "float"}
        order_amount = smoothing_factor * avg_pipeline + (1 - smoothing_factor) * order_amount

    # Round to nearest integer since order amounts should be integers
    order_amount = int(round(order_amount))

    return order_amount
