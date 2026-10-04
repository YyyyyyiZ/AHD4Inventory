# policy_hash: b727c6a2db5c9d78458663ecf576e4b15ea7f5e5bc675528d8496599606566f9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 11
# source_prompt_files: 2
# best_target_performance: 1650.69
# best_prompt_performance: 1650.69
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_073624.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.1231725050024  # OPT_PARAM: {"initial": 450.1231725050024, "min": 300, "max": 600, "type": "float"}
    safety_stock = 50.22317250500243  # OPT_PARAM: {"initial": 50.22317250500243, "min": 20, "max": 150, "type": "float"}
    pipeline_coef = 0.7794792039251529  # OPT_PARAM: {"initial": 0.7794792039251529, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock adjustment
    target_level = base_stock + safety_stock

    # Calculate order amount with pipeline consideration
    order_amount = max(0, target_level - inventory_position)

    # Apply pipeline coefficient to smooth orders
    order_amount = pipeline_coef * order_amount

    # Round to nearest integer
    return order_amount
