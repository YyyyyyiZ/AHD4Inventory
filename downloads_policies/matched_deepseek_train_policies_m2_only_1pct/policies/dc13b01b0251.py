# policy_hash: dc13b01b0251a7858a308808c7dcddc310bd6ad92133a75644f7cf2f574af0e5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 6127.99
# best_prompt_performance: 6127.99
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_054239.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 440.81726721050444  # OPT_PARAM: {"initial": 440.81726721050444, "min": 200, "max": 800, "type": "float"}
    safety_stock = 90.81726721050183  # OPT_PARAM: {"initial": 90.81726721050183, "min": 50, "max": 300, "type": "float"}
    pipeline_weight = 0.8248207315186193  # OPT_PARAM: {"initial": 0.8248207315186193, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.20205039149753676  # OPT_PARAM: {"initial": 0.20205039149753676, "min": 0.1, "max": 1.0, "type": "float"}
    min_order_threshold = 20  # OPT_PARAM: {"initial": 20, "min": 0, "max": 50, "type": "int"}

    # Calculate inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target order with safety stock
    target_inventory = base_stock + safety_stock
    net_requirement = target_inventory - inventory_position

    # Apply smoothing to order quantity
    if net_requirement > 0:
        order_amount = max(0, smoothing_factor * net_requirement)
    else:
        order_amount = 0

    # Apply minimum order threshold
    if order_amount < min_order_threshold:
        order_amount = 0

    return order_amount
