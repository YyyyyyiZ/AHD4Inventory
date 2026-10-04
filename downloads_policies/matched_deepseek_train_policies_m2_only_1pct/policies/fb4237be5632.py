# policy_hash: fb4237be563234ea3db555fe0be193801f1601f52045907d6cd6c5b75ada0182
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2494.5
# best_prompt_performance: 2494.26
# best_rel_error_pct: 0.009621
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_014514.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 653.9732288409273  # OPT_PARAM: {"initial": 653.9732288409273, "min": 500, "max": 750, "type": "float"}
    safety_stock = 93.97322884093818  # OPT_PARAM: {"initial": 93.97322884093818, "min": 20, "max": 100, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Calculate order amount with adjustment factor
    order_amount = max(0, (target_inventory - inventory_position) * adjustment_factor)

    # Round to nearest integer
    return order_amount
