# policy_hash: 83c979d95fc0759bdee2e1357c390f268a64bab8ada34f632de8155bb033da2e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 7029.07
# best_prompt_performance: 7029.07
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_011602.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 356.97846705398155  # OPT_PARAM: {"initial": 356.97846705398155, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 99.9233022964845  # OPT_PARAM: {"initial": 99.9233022964845, "min": 10, "max": 500, "type": "float"}
    smoothing_factor = 0.42927267605633934  # OPT_PARAM: {"initial": 0.42927267605633934, "min": 0.01, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on recent demand pattern
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    if recent_arrivals > 0:
        adjusted_base = base_stock + (recent_arrivals - demand_forecast) * smoothing_factor
    else:
        adjusted_base = base_stock

    # Ensure minimum safety stock
    target_inventory = max(adjusted_base, safety_stock)

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    return order_amount
