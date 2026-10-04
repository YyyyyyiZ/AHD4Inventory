# policy_hash: f8ebd33d1f2a200dba5c4b0872965690b2f3ac7e25efa7cbf10044c37eb9adc0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 52
# source_prompt_files: 1
# best_target_performance: 10174.28
# best_prompt_performance: 10174.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_033257.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 277.2779232300016  # OPT_PARAM: {"initial": 277.2779232300016, "min": 200, "max": 400, "type": "float"}
    safety_stock = 77.27792322999949  # OPT_PARAM: {"initial": 77.27792322999949, "min": 50, "max": 120, "type": "float"}
    demand_forecast_weight = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast using recent pipeline arrivals
    if pipeline_orders:
        # Use weighted average with more weight to recent orders
        weights = [0.8, 0.2] if len(pipeline_orders) > 1 else [1.0]
        weighted_sum = sum(w * p for w, p in zip(weights, pipeline_orders[:len(weights)]))
        avg_weight = sum(weights[:len(pipeline_orders)])
        forecast_demand = weighted_sum / avg_weight if avg_weight > 0 else 0
    else:
        forecast_demand = 0

    # Adjust base stock with forecast
    adjusted_base_stock = base_stock + safety_stock + forecast_demand * demand_forecast_weight

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply order smoothing
    max_order_jump = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 200, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}

    if order_amount > max_order_jump:
        order_amount = max_order_jump + (order_amount - max_order_jump) * smoothing_factor

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
