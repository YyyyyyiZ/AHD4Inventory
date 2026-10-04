# policy_hash: d7029f25b14bf76d8fb1c3f714126a012567881c630f5305f4a462b2b89c3d7d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 6263.09
# best_prompt_performance: 6257.71
# best_rel_error_pct: 0.085900
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_075529.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 279.08985420892907  # OPT_PARAM: {"initial": 279.08985420892907, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.2933907951894718  # OPT_PARAM: {"initial": 0.2933907951894718, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on recent pipeline arrivals
    # Use average of recent arrivals as demand proxy
    recent_arrivals = pipeline_orders[:2] if len(pipeline_orders) >= 2 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme order sizes
    smoothing_factor = 0.24487758697248752  # OPT_PARAM: {"initial": 0.24487758697248752, "min": 0.1, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_recent_demand

    return order_amount
