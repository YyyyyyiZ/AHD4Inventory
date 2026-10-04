# policy_hash: 6dde9a518b7387aab79ef23bef615e59d91871d132d65ccb531648112aa12144
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 6234.28
# best_prompt_performance: 6234.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_014140.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 440.7519304976423  # OPT_PARAM: {"initial": 440.7519304976423, "min": 100, "max": 800, "type": "float"}
    pipeline_weight = 0.8815374896487681  # OPT_PARAM: {"initial": 0.8815374896487681, "min": 0.5, "max": 1.2, "type": "float"}
    demand_buffer = 40.75193049764045  # OPT_PARAM: {"initial": 40.75193049764045, "min": 10, "max": 150, "type": "float"}

    # Calculate inventory position with weighted pipeline
    inventory_position = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + demand_buffer

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order smoothing
    smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    order_amount = order_amount * smoothing

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
