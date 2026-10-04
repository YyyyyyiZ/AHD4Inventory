# policy_hash: 320b7478615de1f3a36448020d866143ff16b2acfa39c3dbebfbf3a570549e6f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 9
# source_prompt_files: 2
# best_target_performance: 2840.97
# best_prompt_performance: 2840.97
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_015512.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 639.0535879746576  # OPT_PARAM: {"initial": 639.0535879746576, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 25.064038736498528  # OPT_PARAM: {"initial": 25.064038736498528, "min": 0, "max": 200, "type": "float"}
    pipeline_adjustment = 0.9970266232966137  # OPT_PARAM: {"initial": 0.9970266232966137, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate effective pipeline considering lead time
    effective_pipeline = sum(pipeline_orders) * pipeline_adjustment

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate order amount with smoothing
    inventory_position = on_hand_inventory + effective_pipeline
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer (since demand is integer)
    return order_amount
