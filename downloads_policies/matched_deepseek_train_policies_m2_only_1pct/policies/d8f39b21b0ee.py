# policy_hash: d8f39b21b0eeb18140f03f8eff371143011fbba3ff0c4abbed7e3f75d3e09d10
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 6025.07
# best_prompt_performance: 6025.07
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_035821.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 283.9621241684033  # OPT_PARAM: {"initial": 283.9621241684033, "min": 200, "max": 350, "type": "float"}
    pipeline_weight = 0.9469811677948318  # OPT_PARAM: {"initial": 0.9469811677948318, "min": 0.8, "max": 1.0, "type": "float"}
    demand_buffer = 1.0793676124062461  # OPT_PARAM: {"initial": 1.0793676124062461, "min": 1.0, "max": 1.25, "type": "float"}
    smoothing_factor = 0.18864005008026036  # OPT_PARAM: {"initial": 0.18864005008026036, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock = 33.98403934168254  # OPT_PARAM: {"initial": 33.98403934168254, "min": 20, "max": 50, "type": "float"}
    pipeline_decay = 0.8630319408185534  # OPT_PARAM: {"initial": 0.8630319408185534, "min": 0.7, "max": 1.0, "type": "float"}
    recent_weight = 0.7534745581944987  # OPT_PARAM: {"initial": 0.7534745581944987, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate weighted pipeline with exponential decay
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_decay ** i
        weighted_pipeline += order * weight
    weighted_pipeline *= pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate target inventory
    target_inventory = base_stock * demand_buffer + safety_stock

    # Base order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing with weighted recent pipeline
    if len(pipeline_orders) > 0:
        if len(pipeline_orders) >= 2:
            recent_pipeline = recent_weight * pipeline_orders[0] + (1 - recent_weight) * pipeline_orders[1]
        else:
            recent_pipeline = pipeline_orders[0]

        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_pipeline
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    return order_amount
