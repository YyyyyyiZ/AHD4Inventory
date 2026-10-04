# policy_hash: feeb13bc74572ba5e4a75ae43a2369ca6a68863312861e222620bef74ec7cc01
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1119.86
# best_prompt_performance: 1119.62
# best_rel_error_pct: 0.021431
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_100135.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 304.3044626548093  # OPT_PARAM: {"initial": 304.3044626548093, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 100, "type": "float"}
    demand_adjustment = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline usage
    recent_orders = pipeline_orders[-2:] if len(pipeline_orders) >= 2 else pipeline_orders
    avg_recent_demand = sum(recent_orders) / len(recent_orders) if recent_orders else 0

    # Adjust base stock based on recent demand pattern
    adjusted_base_stock = base_stock + demand_adjustment * (avg_recent_demand - 100)

    # Calculate order amount with safety stock consideration
    target_inventory = max(adjusted_base_stock, safety_stock)
    order_amount = max(0, target_inventory - net_inventory)

    # Smooth ordering by rounding to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
