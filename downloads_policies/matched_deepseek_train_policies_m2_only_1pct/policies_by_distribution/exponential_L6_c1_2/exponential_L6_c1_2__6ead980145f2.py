# policy_hash: 6ead980145f21fded6e21127efcebe00fe96be12a92974e9b41967bded64ff6c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 6032.76
# best_prompt_performance: 6032.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_035327.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 311.3464006895589  # OPT_PARAM: {"initial": 311.3464006895589, "min": 250, "max": 400, "type": "float"}
    pipeline_weight = 0.9887010307790011  # OPT_PARAM: {"initial": 0.9887010307790011, "min": 0.85, "max": 1.0, "type": "float"}
    demand_buffer = 1.177876493276143  # OPT_PARAM: {"initial": 1.177876493276143, "min": 1.05, "max": 1.3, "type": "float"}
    smoothing_factor = 0.15880929509659023  # OPT_PARAM: {"initial": 0.15880929509659023, "min": 0.15, "max": 0.4, "type": "float"}
    safety_stock = 27.242723229973308  # OPT_PARAM: {"initial": 27.242723229973308, "min": 20, "max": 60, "type": "float"}
    pipeline_decay = 0.9566085387780652  # OPT_PARAM: {"initial": 0.9566085387780652, "min": 0.7, "max": 1.0, "type": "float"}

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

    # Apply smoothing with pipeline consideration
    if len(pipeline_orders) > 0:
        recent_pipeline = sum(pipeline_orders[:2]) / 2 if len(pipeline_orders) >= 2 else pipeline_orders[0]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_pipeline
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    return order_amount
