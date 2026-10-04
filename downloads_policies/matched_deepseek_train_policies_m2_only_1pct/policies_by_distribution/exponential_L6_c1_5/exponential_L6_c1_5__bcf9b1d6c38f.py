# policy_hash: bcf9b1d6c38fb7aa89cc881de11674fa440f96861603146aba0c0da1cf760575
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 12591.19
# best_prompt_performance: 12591.24
# best_rel_error_pct: 0.000397
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_100927.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 523.1349251552256  # OPT_PARAM: {"initial": 523.1349251552256, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 105.92460056101974  # OPT_PARAM: {"initial": 105.92460056101974, "min": 50, "max": 300, "type": "float"}
    demand_forecast_window = 5  # OPT_PARAM: {"initial": 5, "min": 3, "max": 10, "type": "int"}
    forecast_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate forecast adjustment based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:min(demand_forecast_window, len(pipeline_orders))]
    avg_recent = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand patterns
    adjusted_base = base_stock * forecast_weight + avg_recent * (1 - forecast_weight)

    # Calculate order-up-to level with safety stock
    order_up_to = adjusted_base + safety_stock

    # Calculate order amount with pipeline consideration
    order_amount = max(0, order_up_to - inventory_position * pipeline_weight)

    return order_amount
