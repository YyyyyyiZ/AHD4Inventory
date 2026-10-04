# policy_hash: 1fa61d7f206f213f0eea77f9b0d1268903d18788004624289cd5aca8153a5d2d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2660.72
# best_prompt_performance: 2642.44
# best_rel_error_pct: 0.687032
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_065928.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 677.5623753729567  # OPT_PARAM: {"initial": 677.5623753729567, "min": 500, "max": 850, "type": "float"}
    safety_stock = 117.6623753729558  # OPT_PARAM: {"initial": 117.6623753729558, "min": 80, "max": 180, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Simple order-up-to policy without complex adjustments
    order_up_to = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply moderate smoothing
    if order_amount > 0:
        smoothing_exponent = 0.726730076592403  # OPT_PARAM: {"initial": 0.726730076592403, "min": 0.7, "max": 1.0, "type": "float"}
        order_amount = order_amount ** smoothing_exponent

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
