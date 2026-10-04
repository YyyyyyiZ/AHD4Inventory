# policy_hash: a9a6666eabdaaf01cac415fa78dc3d1f989b381eb3e4443b0e84e9018c1b4f41
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 7085.42
# best_prompt_performance: 7091.83
# best_rel_error_pct: 0.090467
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_034342.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 356.9601574426319  # OPT_PARAM: {"initial": 356.9601574426319, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.1  # OPT_PARAM: {"initial": 50.1, "min": 0, "max": 200, "type": "float"}
    demand_window = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 10, "type": "int"}
    forecast_weight = 0.29999999999999993  # OPT_PARAM: {"initial": 0.29999999999999993, "min": 0, "max": 1, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast (using recent pipeline arrivals as proxy for recent demand)
    recent_arrivals = pipeline_orders[:demand_window]
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand pattern
    adjusted_base_stock = base_stock * (1 - forecast_weight) + avg_recent_demand * forecast_weight * 2

    # Add safety stock
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer since order amounts should be integers
    return order_amount
