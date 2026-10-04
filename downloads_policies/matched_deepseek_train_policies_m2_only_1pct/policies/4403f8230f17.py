# policy_hash: 4403f8230f17da780c44094d79ebda1625657b41d61ca1235e4dd95c28fb61a6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 6096.49
# best_prompt_performance: 6096.37
# best_rel_error_pct: 0.001968
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_053701.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 378.54867648621087  # OPT_PARAM: {"initial": 378.54867648621087, "min": 200, "max": 600, "type": "float"}
    safety_stock = 118.54867648621045  # OPT_PARAM: {"initial": 118.54867648621045, "min": 50, "max": 250, "type": "float"}
    pipeline_weight = 0.835175878095504  # OPT_PARAM: {"initial": 0.835175878095504, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2026260549263761  # OPT_PARAM: {"initial": 0.2026260549263761, "min": 0.1, "max": 0.8, "type": "float"}
    min_order_threshold = 10  # OPT_PARAM: {"initial": 10, "min": 0, "max": 30, "type": "int"}
    demand_forecast_factor = 0.13087431561490145  # OPT_PARAM: {"initial": 0.13087431561490145, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate effective pipeline with weight
    effective_pipeline = sum(pipeline_orders) * pipeline_weight

    # Simple demand forecast based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0
    demand_adjustment = avg_recent_demand * demand_forecast_factor

    # Dynamic target inventory: base + safety + demand adjustment
    target_inventory = base_stock + safety_stock + demand_adjustment

    # Inventory position calculation
    inventory_position = on_hand_inventory + effective_pipeline

    # Order gap calculation
    gap = target_inventory - inventory_position

    # Apply smoothing with more aggressive ordering
    if gap > 0:
        order_amount = max(0, smoothing_factor * gap)
    else:
        order_amount = 0

    # Apply minimum order threshold (lower than before for more responsiveness)
    if order_amount < min_order_threshold:
        order_amount = 0

    return order_amount
