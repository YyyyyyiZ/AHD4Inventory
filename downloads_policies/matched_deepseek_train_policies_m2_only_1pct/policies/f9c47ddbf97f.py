# policy_hash: f9c47ddbf97f6af54f59e51027192afea25cbb125ad8cdc705863ab26b1450ea
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_2
# matched_train_cells: 34
# source_prompt_files: 1
# best_target_performance: 2753.61
# best_prompt_performance: 2753.61
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_062209.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 639.97934591949  # OPT_PARAM: {"initial": 639.97934591949, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 25.003279886148434  # OPT_PARAM: {"initial": 25.003279886148434, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate order-up-to level with safety stock adjustment
    target_level = base_stock + safety_stock

    # Order amount calculation
    order_amount = max(0, target_level - inventory_position)

    # Round to nearest integer since order amounts should be integers
    return order_amount
