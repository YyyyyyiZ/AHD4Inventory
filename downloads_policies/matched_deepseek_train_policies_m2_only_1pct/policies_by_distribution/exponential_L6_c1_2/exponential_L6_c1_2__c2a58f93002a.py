# policy_hash: c2a58f93002a5456f156437d8601a53aafa5bbf18aa8211d3dbf9949d3dfd8d4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 6226.34
# best_prompt_performance: 6226.34
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_012046.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 357.61364167364235  # OPT_PARAM: {"initial": 357.61364167364235, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.65348423101075  # OPT_PARAM: {"initial": 50.65348423101075, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 0.6106373404350328  # OPT_PARAM: {"initial": 0.6106373404350328, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock with safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to avoid large order fluctuations
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = int(order_amount * smoothing_factor)

    return order_amount
