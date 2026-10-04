# policy_hash: 0d3eb5e14b9603c6292dfc05129d7aba947ccaea12e6fe6989ab8bec51434faf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 3347.42
# best_prompt_performance: 3346.68
# best_rel_error_pct: 0.022107
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_014422.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 672.9725290973008  # OPT_PARAM: {"initial": 672.9725290973008, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 24.972803573699366  # OPT_PARAM: {"initial": 24.972803573699366, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 1, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate demand forecast based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand pattern
    adjusted_base = base_stock + (avg_recent_demand - 100) * smoothing_factor

    # Calculate order amount with safety stock consideration
    target_inventory = adjusted_base + safety_stock
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer (as order amounts should be integers)
    return order_amount
