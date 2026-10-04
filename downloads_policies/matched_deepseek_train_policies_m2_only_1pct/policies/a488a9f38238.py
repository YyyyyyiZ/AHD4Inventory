# policy_hash: a488a9f38238e3363cdf55d1d80fc6b8d0b25664bacbe8e45a97268476d40f7f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 6112.26
# best_prompt_performance: 6111.92
# best_rel_error_pct: 0.005563
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223751.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 159.96071553174525  # OPT_PARAM: {"initial": 159.96071553174525, "min": 100, "max": 300, "type": "float"}
    safety_stock = 39.81181488472294  # OPT_PARAM: {"initial": 39.81181488472294, "min": 20, "max": 100, "type": "float"}
    pipeline_weight = 0.814779698816101  # OPT_PARAM: {"initial": 0.814779698816101, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 1.1835101463814743  # OPT_PARAM: {"initial": 1.1835101463814743, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on upcoming arrivals
    next_arrival = pipeline_orders[0] if pipeline_orders else 0
    adjusted_base = base_stock * demand_buffer - next_arrival * 0.3

    # Calculate target with dynamic safety stock
    target = adjusted_base + safety_stock

    # Calculate order amount
    order_amount = max(0, target - inventory_position)

    # Add smoothing to avoid extreme orders
    if order_amount > 0:
        order_amount = min(order_amount, base_stock * 0.7)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
