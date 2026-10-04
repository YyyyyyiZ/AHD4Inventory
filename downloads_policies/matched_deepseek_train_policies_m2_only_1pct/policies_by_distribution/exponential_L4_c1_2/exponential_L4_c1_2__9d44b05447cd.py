# policy_hash: 9d44b05447cddb9d3ae73f3fc2939fe9988dd7dd3ce26be2c54b4fea85f16050
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 6881.47
# best_prompt_performance: 6869.45
# best_rel_error_pct: 0.174672
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_075402.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 282.96320741051414  # OPT_PARAM: {"initial": 282.96320741051414, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.58012195678134  # OPT_PARAM: {"initial": 49.58012195678134, "min": 0, "max": 200, "type": "float"}
    adjustment_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time (using recent pipeline orders as proxy)
    recent_orders = pipeline_orders[-2:] if len(pipeline_orders) >= 2 else pipeline_orders
    avg_recent = sum(recent_orders) / len(recent_orders) if recent_orders else 0
    expected_lead_time_demand = avg_recent * len(pipeline_orders) * adjustment_factor

    # Dynamic target based on expected demand and safety stock
    dynamic_target = expected_lead_time_demand + safety_stock

    # Use the maximum of base_stock and dynamic_target
    target = max(base_stock, dynamic_target)

    # Order up to target
    order_amount = max(0, target - inventory_position)

    return order_amount
