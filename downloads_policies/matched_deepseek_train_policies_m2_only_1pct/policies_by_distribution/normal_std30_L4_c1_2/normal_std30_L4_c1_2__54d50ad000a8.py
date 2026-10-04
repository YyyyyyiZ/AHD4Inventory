# policy_hash: 54d50ad000a83e113d4ac21e4b84fbd86b740979ee840f49dfa3658b8a0af0f5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_2
# matched_train_cells: 18
# source_prompt_files: 1
# best_target_performance: 2145.29
# best_prompt_performance: 2145.29
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_015313.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 472.33178004530794  # OPT_PARAM: {"initial": 472.33178004530794, "min": 300, "max": 600, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 20, "max": 80, "type": "float"}
    demand_alpha = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 0.4, "type": "float"}
    max_order = 88.37750462093294  # OPT_PARAM: {"initial": 88.37750462093294, "min": 80, "max": 200, "type": "float"}
    min_order = 42.566346276172325  # OPT_PARAM: {"initial": 42.566346276172325, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from recent arrivals (more stable than single period)
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    if recent_arrivals > 0:
        # Smoother demand estimation with less aggressive adjustment
        estimated_demand = recent_arrivals * (1 + demand_alpha)
    else:
        # Default to conservative estimate when no recent arrivals
        estimated_demand = 100.0

    # Calculate order-up-to level
    # Base stock adjusted by demand estimate (less sensitive than historical)
    adjusted_base = base_stock * (0.7 + 0.3 * (estimated_demand / 100))

    # Order-up-to level with safety stock
    order_up_to = max(adjusted_base, safety_stock + estimated_demand * 2.5)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply order limits
    order_amount = max(min_order, min(order_amount, max_order))

    # Round to integer for practical ordering
    return order_amount
