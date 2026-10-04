# policy_hash: 230a65ad4a785bedb4f3f45ed1d399bca0cd325898b01b590148456be712e1a4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 2709.94
# best_prompt_performance: 2705.4
# best_rel_error_pct: 0.167531
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_014031.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 638.8878739848152  # OPT_PARAM: {"initial": 638.8878739848152, "min": 550, "max": 700, "type": "float"}
    safety_stock = 78.88787055986593  # OPT_PARAM: {"initial": 78.88787055986593, "min": 40, "max": 80, "type": "float"}
    adjustment_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Calculate order amount with adjustment factor
    order_amount = max(0, (target_inventory - inventory_position) * adjustment_factor)

    # Round to nearest integer
    return order_amount
