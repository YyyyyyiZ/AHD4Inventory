# policy_hash: cbedc8d2336c3f4dd9b6f73cfec4b632a789a111c2f9b89a609a74cbcf981f65
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 44
# source_prompt_files: 1
# best_target_performance: 1636.06
# best_prompt_performance: 1636.48
# best_rel_error_pct: 0.025671
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_091319.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 642.7384124598258  # OPT_PARAM: {"initial": 642.7384124598258, "min": 500, "max": 900, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    order_threshold = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 40, "type": "float"}
    safety_stock = 92.32037063978144  # OPT_PARAM: {"initial": 92.32037063978144, "min": 50, "max": 200, "type": "float"}
    demand_adjustment = 0.9411677448016532  # OPT_PARAM: {"initial": 0.9411677448016532, "min": 0.9, "max": 1.2, "type": "float"}
    pipeline_lookback = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 6, "type": "int"}
    pipeline_threshold = 200  # OPT_PARAM: {"initial": 200, "min": 100, "max": 400, "type": "int"}
    max_order = 120  # OPT_PARAM: {"initial": 120, "min": 100, "max": 300, "type": "int"}
    min_order = 20  # OPT_PARAM: {"initial": 20, "min": 0, "max": 50, "type": "int"}

    # Calculate weighted pipeline inventory
    weighted_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust base stock based on recent pipeline pattern
    recent_pipeline = sum(pipeline_orders[:pipeline_lookback]) if len(pipeline_orders) >= pipeline_lookback else sum(pipeline_orders)
    if recent_pipeline < pipeline_threshold:
        adjusted_base_stock = base_stock * demand_adjustment
    else:
        adjusted_base_stock = base_stock * 0.95

    # Add safety stock component
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply minimum order quantity
    if 0 < order_amount < min_order:
        order_amount = min_order

    # Apply maximum order limit
    order_amount = min(order_amount, max_order)

    # Apply ordering threshold
    if order_amount < order_threshold:
        order_amount = 0

    return order_amount
