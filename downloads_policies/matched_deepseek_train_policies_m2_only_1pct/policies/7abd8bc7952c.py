# policy_hash: 7abd8bc7952c5be1c79093c4488c1d500a6a8fa35e4dd0891a4d621993a4788b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2865.38
# best_prompt_performance: 2855.72
# best_rel_error_pct: 0.337128
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_085202.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 638.8476495387448  # OPT_PARAM: {"initial": 638.8476495387448, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 24.993586154809275  # OPT_PARAM: {"initial": 24.993586154809275, "min": 0, "max": 200, "type": "float"}
    demand_adjustment_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline orders (recent orders reflect recent demand)
    recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_order = sum(recent_orders) / len(recent_orders) if recent_orders else 0

    # Adjust base stock based on recent demand pattern
    adjusted_base_stock = base_stock + (avg_recent_order - 100) * demand_adjustment_factor

    # Calculate target inventory position
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - net_inventory)

    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
