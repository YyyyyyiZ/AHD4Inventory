# policy_hash: 8001baa0bbfaef28259493ba5c4c1099cad7c12f8dc8a7cd0d6b0485bfee3b25
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1925.56
# best_prompt_performance: 1911.34
# best_rel_error_pct: 0.738486
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_025049.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 283.47886574074334  # OPT_PARAM: {"initial": 283.47886574074334, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 24.497384259255128  # OPT_PARAM: {"initial": 24.497384259255128, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 50, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock

    # Calculate order-up-to level
    order_up_to = max(0, target_inventory - inventory_position)

    # Add demand forecast adjustment
    demand_adjustment = max(0, demand_estimate - pipeline_orders[0] if pipeline_orders else 0)

    # Final order amount
    order_amount = max(0, order_up_to + demand_adjustment)

    return order_amount
