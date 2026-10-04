# policy_hash: 2d66a12a03cb3895f38bd8e3552b44058f3e77fd9704bf67b0bcbfc994df5632
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 6786.42
# best_prompt_performance: 6787.03
# best_rel_error_pct: 0.008989
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_040431.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 316.986692243208  # OPT_PARAM: {"initial": 316.986692243208, "min": 250, "max": 450, "type": "float"}
    safety_stock = 37.37967084109577  # OPT_PARAM: {"initial": 37.37967084109577, "min": 20, "max": 80, "type": "float"}
    pipeline_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.25, "type": "float"}
    demand_forecast_factor = 0.5450572742823269  # OPT_PARAM: {"initial": 0.5450572742823269, "min": 0.5, "max": 1.2, "type": "float"}
    max_order_multiplier = 2.1409309748998178  # OPT_PARAM: {"initial": 2.1409309748998178, "min": 1.5, "max": 4.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Demand forecast using weighted average of pipeline orders
    # Give more weight to recent orders
    if len(pipeline_orders) >= 3:
        weights = [0.5, 0.3, 0.2]  # Decreasing weights for older orders
        recent_arrivals = pipeline_orders[:3]
        forecast_demand = sum(w * d for w, d in zip(weights, recent_arrivals)) * demand_forecast_factor
    else:
        forecast_demand = 0

    # Adjust base stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_avg = pipeline_sum / len(pipeline_orders)
        pipeline_variability = sum(abs(p - pipeline_avg) for p in pipeline_orders) / pipeline_sum
        # Moderate adjustment for variability
        adjusted_base = base_stock * (1 + pipeline_variability * pipeline_factor)
    else:
        adjusted_base = base_stock

    # Target inventory with safety stock and forecast
    target_inventory = adjusted_base + safety_stock + forecast_demand

    # Calculate order amount with cap to prevent excessive ordering
    order_amount = max(0, target_inventory - inventory_position)

    # Cap order amount to reasonable multiple of recent demand
    if len(pipeline_orders) > 0:
        avg_recent = sum(pipeline_orders[:min(3, len(pipeline_orders))]) / min(3, len(pipeline_orders))
        max_order = avg_recent * max_order_multiplier if avg_recent > 0 else target_inventory
        order_amount = min(order_amount, max_order)

    # Round to nearest integer
    return order_amount
