# policy_hash: ef87b0721b7e38b778d0dc3c4d1facf85a02c3c4c1cc3ed1cfcfd8b96b744936
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 6562.86
# best_prompt_performance: 6562.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_235038.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 320.0  # OPT_PARAM: {"initial": 320.0, "min": 200, "max": 500, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 30, "max": 150, "type": "float"}
    demand_smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted average of recent pipeline arrivals
    # More weight to recent arrivals
    if len(pipeline_orders) >= 3:
        # Use last 3 pipeline orders with weights [0.5, 0.3, 0.2]
        weights = [0.5, 0.3, 0.2]
        recent_arrivals = pipeline_orders[-3:]
        weighted_avg = sum(w * d for w, d in zip(weights, recent_arrivals))
    else:
        weighted_avg = sum(pipeline_orders) / max(1, len(pipeline_orders))

    # Adjust base stock based on demand forecast
    # More aggressive adjustment when demand is high
    adjustment = demand_smoothing_factor * weighted_avg
    adjusted_base_stock = base_stock + adjustment

    # Ensure minimum safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate order amount with smoother adjustment
    order_amount = max(0, order_up_to - inventory_position)

    # Apply ordering limits based on demand forecast
    max_order = min(500.0, 2.5 * weighted_avg)  # OPT_PARAM: {"initial": 500.0, "min": 300, "max": 700, "type": "float"}
    min_order = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 50, "type": "float"}

    if order_amount > 0:
        order_amount = max(min_order, min(order_amount, max_order))

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
