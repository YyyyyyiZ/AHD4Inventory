# policy_hash: 11c597cafcdaf893c37548cafc0c7e46443087a597433e16deb2ad8cd39bd8ea
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 4181.39
# best_prompt_performance: 4180.7
# best_rel_error_pct: 0.016502
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_024751.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 475.37005793637326  # OPT_PARAM: {"initial": 475.37005793637326, "min": 400, "max": 700, "type": "float"}
    safety_stock = 118.75113286766775  # OPT_PARAM: {"initial": 118.75113286766775, "min": 20, "max": 150, "type": "float"}
    pipeline_lead_time = 6
    demand_estimate = 70.82695424041903  # OPT_PARAM: {"initial": 70.82695424041903, "min": 70, "max": 130, "type": "float"}
    smoothing_factor = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * pipeline_lead_time

    # Dynamic adjustment based on pipeline coverage
    pipeline_coverage = sum(pipeline_orders) / (expected_lead_time_demand + 1e-6)
    adjustment_factor = 1.0 - smoothing_factor * max(0, pipeline_coverage - 1.0)

    # Dynamic base stock level
    dynamic_base_stock = base_stock + safety_stock * adjustment_factor

    # Calculate order amount
    order_amount = max(0, dynamic_base_stock - inventory_position)

    # Round to nearest integer
    return order_amount
