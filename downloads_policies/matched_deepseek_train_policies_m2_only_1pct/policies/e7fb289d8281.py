# policy_hash: e7fb289d8281b9a0d60a840f2da93463661702254a359117d8cfec2e97a2ad56
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 14
# source_prompt_files: 3
# best_target_performance: 1735.63
# best_prompt_performance: 1735.63
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_234620.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 475.28159400663725  # OPT_PARAM: {"initial": 475.28159400663725, "min": 300, "max": 600, "type": "float"}
    safety_stock = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 10, "max": 150, "type": "float"}
    demand_estimate = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected shortfall considering lead time
    expected_shortfall = max(0, base_stock - inventory_position)

    # Adjust for safety stock based on current pipeline status
    pipeline_coverage = sum(pipeline_orders) / (4 * demand_estimate) if demand_estimate > 0 else 1.0
    safety_adjustment = safety_stock * (1.0 - min(1.0, pipeline_coverage))

    # Calculate order amount
    order_amount = max(0, expected_shortfall + safety_adjustment)

    # Round to nearest integer (as order amounts should be integers)
    return order_amount
