# policy_hash: 6cfe8aaefda17f4aa82f6b5875387f558340558f923282ade717bd743c26ac65
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 47
# source_prompt_files: 1
# best_target_performance: 6301.86
# best_prompt_performance: 6301.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_104303.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 207.98976981790145  # OPT_PARAM: {"initial": 207.98976981790145, "min": 100, "max": 500, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 50, "max": 300, "type": "float"}
    safety_factor = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 0.5, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory position based on lead time demand with safety factor
    lead_time = len(pipeline_orders)
    target_position = demand_estimate * lead_time * safety_factor

    # Calculate order-up-to level as max of base_stock and target_position
    order_up_to = max(base_stock, target_position)

    # Order amount to bring inventory position up to order_up_to level
    order_amount = max(0, order_up_to - inventory_position)

    return order_amount
