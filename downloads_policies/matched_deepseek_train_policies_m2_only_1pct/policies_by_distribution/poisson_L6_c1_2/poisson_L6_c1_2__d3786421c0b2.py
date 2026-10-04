# policy_hash: d3786421c0b287988214425693c55d40e96afeeee8af9c2151bf136a1c738b87
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 3372.08
# best_prompt_performance: 3372.08
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_015341.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 663.9895492381544  # OPT_PARAM: {"initial": 663.9895492381544, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    pipeline_lead_time = 6  # Fixed lead time
    pipeline_sum = sum(pipeline_orders)

    # Calculate net inventory position
    net_inventory = on_hand_inventory + pipeline_sum

    # Calculate order-up-to level with safety stock adjustment
    order_up_to = base_stock + safety_stock

    # Calculate order amount with non-negativity constraint
    order_amount = max(0, order_up_to - net_inventory)

    # Round to nearest integer since order amounts should be integers
    order_amount = int(round(order_amount))

    return order_amount
