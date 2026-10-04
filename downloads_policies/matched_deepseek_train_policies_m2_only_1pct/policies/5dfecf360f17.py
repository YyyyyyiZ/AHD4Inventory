# policy_hash: 5dfecf360f17dc345daa14fa24f88661a2e2f8abd5e9dd80d5591046eaded765
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 5885.16
# best_prompt_performance: 5885.18
# best_rel_error_pct: 0.000340
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_070304.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 209.74733480229827  # OPT_PARAM: {"initial": 209.74733480229827, "min": 150, "max": 300, "type": "float"}
    safety_stock = 84.53029564899556  # OPT_PARAM: {"initial": 84.53029564899556, "min": 50, "max": 150, "type": "float"}
    pipeline_weight = 0.9361218428016187  # OPT_PARAM: {"initial": 0.9361218428016187, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.8, "type": "float"}
    demand_buffer = 1.1248782872167546  # OPT_PARAM: {"initial": 1.1248782872167546, "min": 1.0, "max": 1.4, "type": "float"}
    min_order_threshold = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.1, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Target inventory with demand buffer
    target_inventory = base_stock * demand_buffer + safety_stock

    # Calculate order needed
    order_needed = max(0, target_inventory - inventory_position)

    # Apply smoothing with minimum order threshold
    if order_needed > base_stock * min_order_threshold:
        smoothed_order = order_needed * smoothing_factor + (base_stock * 0.05) * (1 - smoothing_factor)
        order_amount = int(round(smoothed_order))
    else:
        order_amount = 0

    return order_amount
