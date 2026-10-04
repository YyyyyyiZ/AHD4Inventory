# policy_hash: 66d148a5deb964292fae3435d24cfc80e10384b31cade9f3b5e2a332120957ee
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 942.56
# best_prompt_performance: 942.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_100810.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 260.85152332846985  # OPT_PARAM: {"initial": 260.85152332846985, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 84.15376388389524  # OPT_PARAM: {"initial": 84.15376388389524, "min": 50, "max": 150, "type": "float"}
    pipeline_weight = 0.6422595259158722  # OPT_PARAM: {"initial": 0.6422595259158722, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_inventory = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on demand forecast
    adjusted_base = base_stock * (demand_forecast / 100.0)

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base, demand_forecast + safety_stock)

    # Calculate order amount with pipeline consideration
    order_amount = max(0, order_up_to - effective_inventory * pipeline_weight)

    # Round to nearest integer (since order amount should be integer)
    order_amount = int(round(order_amount))

    return order_amount
