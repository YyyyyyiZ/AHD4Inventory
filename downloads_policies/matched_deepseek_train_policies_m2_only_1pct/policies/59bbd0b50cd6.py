# policy_hash: 59bbd0b50cd63ae7704de96fa3d9c68d4c08395f49510d5a97114b7edafa1799
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 6307.42
# best_prompt_performance: 6308.68
# best_rel_error_pct: 0.019976
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_040350.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 362.22619023190407  # OPT_PARAM: {"initial": 362.22619023190407, "min": 300, "max": 500, "type": "float"}
    safety_stock = 2.2261902318992037  # OPT_PARAM: {"initial": 2.2261902318992037, "min": 0, "max": 80, "type": "float"}
    pipeline_coeff = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    demand_smoothing = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.2, "max": 0.6, "type": "float"}
    order_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate effective inventory position with discounted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_coeff
    inventory_position = on_hand_inventory + effective_pipeline

    # Estimate upcoming demand from recent pipeline arrivals
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    demand_estimate = recent_arrivals * demand_smoothing

    # Adjust base stock dynamically based on demand estimate
    adjusted_base_stock = base_stock + safety_stock + demand_estimate

    # Calculate raw order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = raw_order * order_smoothing + (1 - order_smoothing) * pipeline_orders[-1] if pipeline_orders else raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
