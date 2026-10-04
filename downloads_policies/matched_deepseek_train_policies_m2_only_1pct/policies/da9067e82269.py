# policy_hash: da9067e822699a35a1263bcd77457cb2f7d9de5d4660cceeb33100ad78289045
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 6120.74
# best_prompt_performance: 6120.74
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_042359.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 349.6275438954149  # OPT_PARAM: {"initial": 349.6275438954149, "min": 250, "max": 450, "type": "float"}
    safety_factor = 2.687660021513578  # OPT_PARAM: {"initial": 2.687660021513578, "min": 1.5, "max": 3.5, "type": "float"}
    smoothing_factor = 0.10277895224444576  # OPT_PARAM: {"initial": 0.10277895224444576, "min": 0.05, "max": 0.5, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 20, "type": "int"}
    max_order = 600  # OPT_PARAM: {"initial": 600, "min": 400, "max": 800, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use recent pipeline arrivals as demand proxy (last 4 periods)
    recent_arrivals = pipeline_orders[:4] if len(pipeline_orders) >= 4 else pipeline_orders

    # Simple demand forecast using average of recent arrivals
    if recent_arrivals:
        forecast = sum(recent_arrivals) / len(recent_arrivals)
    else:
        forecast = base_stock * 0.2

    # Calculate safety stock based on forecast variability
    if len(recent_arrivals) >= 2:
        demand_variance = sum((r - forecast) ** 2 for r in recent_arrivals) / len(recent_arrivals)
        safety_stock = safety_factor * (demand_variance ** 0.5) if demand_variance > 0 else safety_factor * forecast * 0.3
    else:
        safety_stock = safety_factor * forecast * 0.3

    # Adjust base stock with safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Consider pipeline content in target calculation
    pipeline_content = sum(pipeline_orders)
    pipeline_adjustment = pipeline_weight * pipeline_content

    # Calculate target inventory position
    target_inventory_position = adjusted_base_stock - pipeline_adjustment

    # Calculate order needed
    order_needed = target_inventory_position - inventory_position

    # Apply smoothing
    smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * forecast

    # Apply bounds and ensure non-negative
    order_amount = int(round(max(min_order, min(max_order, smoothed_order))))

    return order_amount
