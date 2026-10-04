# policy_hash: e33d0d3e62f0b1439ae947fb343a0e55212addb4295fe53b8978d0078c80c964
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 31
# source_prompt_files: 1
# best_target_performance: 11355.52
# best_prompt_performance: 11353.96
# best_rel_error_pct: 0.013738
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_044120.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 480.00938872611147  # OPT_PARAM: {"initial": 480.00938872611147, "min": 300, "max": 700, "type": "float"}
    safety_stock = 163.97952484847013  # OPT_PARAM: {"initial": 163.97952484847013, "min": 100, "max": 300, "type": "float"}
    demand_estimate = 60.0  # OPT_PARAM: {"initial": 60.0, "min": 60, "max": 150, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}
    pipeline_weight = 0.5467839895903585  # OPT_PARAM: {"initial": 0.5467839895903585, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Dynamic safety stock based on pipeline variability
    pipeline_mean = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_variance = sum((p - pipeline_mean) ** 2 for p in pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    dynamic_safety = safety_stock * (1 + 0.1 * pipeline_variance / (demand_estimate ** 2 + 1))

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + dynamic_safety

    # Use the maximum of base_stock and dynamic target
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount with smoothing and minimum order threshold
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_estimate

    # Apply minimum order quantity to reduce small orders
    if smoothed_order < demand_estimate * 0.3:
        smoothed_order = 0

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
