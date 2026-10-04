# policy_hash: 184f5547c3f168b010cb1feaa52cef7ac52c10906ac384ff9053fd21afa6336f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 959.62
# best_prompt_performance: 959.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_222922.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 294.0000013139217  # OPT_PARAM: {"initial": 294.0000013139217, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline composition
    pipeline_imbalance = pipeline_orders[1] - pipeline_orders[0] if len(pipeline_orders) > 1 else 0
    adjusted_base = base_stock + 0.3 * pipeline_imbalance  # OPT_PARAM: {"initial": 0.3, "min": -1.0, "max": 1.0, "type": "float"}

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base, demand_forecast + safety_stock)

    # Calculate order amount with smoothing
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = 0.7 * raw_order + 0.3 * demand_forecast  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.0, "type": "float"}

    # Round to nearest integer (as required by output type)
    order_amount = int(round(smoothed_order))

    return order_amount
