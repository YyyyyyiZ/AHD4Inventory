# policy_hash: cde9807250075ddc5b83e72a2d98ba8a86d1e7e5896f6ed6202cd06e69d5bf53
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 6467.08
# best_prompt_performance: 6467.08
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223058.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 250.0  # OPT_PARAM: {"initial": 250.0, "min": 100, "max": 500, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 10, "max": 150, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 50, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected shortfall
    expected_shortfall = max(0, base_stock - inventory_position)

    # Adjust for pipeline variability - order more if pipeline is low
    pipeline_sum = sum(pipeline_orders)
    pipeline_adjustment = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.8, "type": "float"}

    # Safety stock adjustment
    safety_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.2, "max": 1.0, "type": "float"}

    # Combine components
    order_amount = expected_shortfall + pipeline_adjustment + safety_adjustment

    # Round to nearest integer and ensure non-negative
    order_amount = max(0, int(round(order_amount)))

    return order_amount
