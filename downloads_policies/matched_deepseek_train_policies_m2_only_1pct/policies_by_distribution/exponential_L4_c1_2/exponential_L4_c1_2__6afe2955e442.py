# policy_hash: 6afe2955e4420507eda90f6141ef361a2551d44349ee3167bcb916aa4284f477
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 6955.95
# best_prompt_performance: 6955.95
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_034808.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 252.9873682852875  # OPT_PARAM: {"initial": 252.9873682852875, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.023913201674375  # OPT_PARAM: {"initial": 20.023913201674375, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:2] if len(pipeline_orders) >= 2 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate order-up-to level with safety stock
    order_up_to = adjusted_base_stock + safety_stock

    # Calculate order amount with pipeline consideration
    pipeline_adjustment = pipeline_weight * (sum(pipeline_orders) - inventory_position * 0.5)
    target_inventory = order_up_to + pipeline_adjustment

    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer since order amounts should be integers
    return order_amount
