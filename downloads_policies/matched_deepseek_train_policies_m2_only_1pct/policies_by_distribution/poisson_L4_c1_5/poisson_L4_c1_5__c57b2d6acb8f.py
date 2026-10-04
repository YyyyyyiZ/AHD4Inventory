# policy_hash: c57b2d6acb8fc5129db138d5f379ac7e43488841fe35647fd629cb00cbe1ff9d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 2190.62
# best_prompt_performance: 2190.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_081323.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 428.3665082040553  # OPT_PARAM: {"initial": 428.3665082040553, "min": 300, "max": 700, "type": "float"}
    safety_stock = 77.65098821518885  # OPT_PARAM: {"initial": 77.65098821518885, "min": 50, "max": 300, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate order-up-to level with safety stock adjustment
    target_level = base_stock + safety_stock

    # Place order to reach target level
    order_amount = max(0, target_level - inventory_position)

    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
