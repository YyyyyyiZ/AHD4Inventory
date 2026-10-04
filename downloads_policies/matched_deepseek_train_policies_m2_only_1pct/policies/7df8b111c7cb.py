# policy_hash: 7df8b111c7cbf10d40d4ad513c30bdf9b92c1fddb9baa39d9f5c18a2ac2b289c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 4218.24
# best_prompt_performance: 4220.12
# best_rel_error_pct: 0.044568
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_024117.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 520.7999999999726  # OPT_PARAM: {"initial": 520.7999999999726, "min": 400, "max": 700, "type": "float"}
    safety_stock = 50.79999999996428  # OPT_PARAM: {"initial": 50.79999999996428, "min": 30, "max": 150, "type": "float"}
    pipeline_coverage = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_coverage
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target order-up-to level with safety stock adjustment
    target_level = base_stock + safety_stock

    # Order amount with smoothing to avoid extreme fluctuations
    raw_order = max(0, target_level - inventory_position)

    # Apply rounding to nearest integer
    order_amount = int(round(raw_order))

    return order_amount
