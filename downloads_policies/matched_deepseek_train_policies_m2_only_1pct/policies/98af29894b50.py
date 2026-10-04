# policy_hash: 98af29894b506aceb684ddc3c988058deb99c3abc79ae71bdad6d734ca8e1ecb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 3706.55
# best_prompt_performance: 3699.38
# best_rel_error_pct: 0.193441
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_053309.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 539.1843851733702  # OPT_PARAM: {"initial": 539.1843851733702, "min": 400, "max": 800, "type": "float"}
    safety_stock = 89.18438517336709  # OPT_PARAM: {"initial": 89.18438517336709, "min": 50, "max": 200, "type": "float"}
    pipeline_coverage = 0.8601015888879828  # OPT_PARAM: {"initial": 0.8601015888879828, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_coverage
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target order-up-to level with safety stock adjustment
    target_level = base_stock + safety_stock

    # Order amount is difference between target and current position
    order_amount = max(0, target_level - inventory_position)

    # Round to nearest integer since order amounts should be integers
    order_amount = int(round(order_amount))

    return order_amount
