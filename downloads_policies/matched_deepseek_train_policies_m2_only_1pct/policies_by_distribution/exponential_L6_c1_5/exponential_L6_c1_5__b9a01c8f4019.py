# policy_hash: b9a01c8f4019e25f818488b1ef2306ec8db08d87dc732da7a6c3489db627a088
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 8
# source_prompt_files: 2
# best_target_performance: 13058.33
# best_prompt_performance: 13058.33
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_100153.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 489.02101690818034  # OPT_PARAM: {"initial": 489.02101690818034, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 85.03347717404273  # OPT_PARAM: {"initial": 85.03347717404273, "min": 50, "max": 300, "type": "float"}
    demand_forecast_factor = 0.292720236650108  # OPT_PARAM: {"initial": 0.292720236650108, "min": 0.1, "max": 0.8, "type": "float"}
    pipeline_weight = 0.7411558145057462  # OPT_PARAM: {"initial": 0.7411558145057462, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate dynamic base stock based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_arrivals = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock dynamically
    dynamic_base_stock = base_stock + demand_forecast_factor * avg_recent_arrivals

    # Calculate order-up-to level with safety stock
    order_up_to = dynamic_base_stock + safety_stock

    # Calculate order amount with pipeline consideration
    pipeline_adjustment = pipeline_weight * (sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0)
    target_inventory = order_up_to - pipeline_adjustment

    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer (as required by output specification)
    return order_amount
