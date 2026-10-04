# policy_hash: 1cd57259189ad1a4ac4e3ef5811e363e89681b14ec877a227dba66c1d43ee93a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 11298.8
# best_prompt_performance: 11298.28
# best_rel_error_pct: 0.004602
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_062403.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 463.287269389181  # OPT_PARAM: {"initial": 463.287269389181, "min": 100, "max": 800, "type": "float"}
    safety_stock = 194.01571322605602  # OPT_PARAM: {"initial": 194.01571322605602, "min": 50, "max": 400, "type": "float"}
    pipeline_coverage_factor = 0.5206727878766391  # OPT_PARAM: {"initial": 0.5206727878766391, "min": 0.1, "max": 2.0, "type": "float"}
    smoothing_factor = 0.11466550379831704  # OPT_PARAM: {"initial": 0.11466550379831704, "min": 0.1, "max": 1.0, "type": "float"}
    lost_sales_weight = 2.819616071182075  # OPT_PARAM: {"initial": 2.819616071182075, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline coverage
    pipeline_total = sum(pipeline_orders)
    adjusted_base_stock = base_stock * (1 + pipeline_coverage_factor * (1 - pipeline_total / max(1, base_stock)))

    # Increase safety stock to reduce lost sales (given p=5 > h=1)
    target_inventory = adjusted_base_stock + safety_stock * lost_sales_weight

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme fluctuations
    if order_amount > 0:
        order_amount = order_amount * smoothing_factor

    return order_amount
