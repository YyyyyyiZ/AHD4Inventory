# policy_hash: 46a3b5304adf1deccb50cb349ca024863667aae56e68417085fbe3847f397e4f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 2548.78
# best_prompt_performance: 2549.45
# best_rel_error_pct: 0.026287
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_014201.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 637.6629609092664  # OPT_PARAM: {"initial": 637.6629609092664, "min": 500, "max": 750, "type": "float"}
    safety_stock = 92.66296090926866  # OPT_PARAM: {"initial": 92.66296090926866, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.8, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate net inventory position with weighted pipeline
    # Give less weight to distant pipeline orders
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = 1.0 - (pipeline_weight * i / len(pipeline_orders))
        weighted_pipeline += order * weight

    net_inventory = on_hand_inventory + weighted_pipeline

    # Calculate target level with safety stock
    target_level = base_stock + safety_stock

    # Apply smoothing to order quantity
    order_amount = max(0, smoothing_factor * (target_level - net_inventory))

    # Round to nearest integer
    return order_amount
