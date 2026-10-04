# policy_hash: 12920182243afa1c7b7d43ab7be4719c026d3e36c683eb60e5fa75bf58ece552
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 4141.72
# best_prompt_performance: 4145.57
# best_rel_error_pct: 0.092957
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_024713.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 523.2813467569165  # OPT_PARAM: {"initial": 523.2813467569165, "min": 400, "max": 700, "type": "float"}
    safety_stock = 53.28134675690889  # OPT_PARAM: {"initial": 53.28134675690889, "min": 20, "max": 150, "type": "float"}
    pipeline_coverage = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock adjustment
    target_level = base_stock + safety_stock

    # Calculate order amount with pipeline coverage consideration
    order_amount = max(0, target_level - inventory_position * pipeline_coverage)

    # Round to nearest integer (orders must be integer quantities)
    return order_amount
