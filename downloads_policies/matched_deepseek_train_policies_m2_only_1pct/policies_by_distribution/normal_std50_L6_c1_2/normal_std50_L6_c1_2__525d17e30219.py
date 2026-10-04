# policy_hash: 525d17e30219e9023beb12cb32f7895a446e9e8542838ef697ab31e001c4e3c4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 4042.42
# best_prompt_performance: 4043.78
# best_rel_error_pct: 0.033643
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_004726.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 350.0  # OPT_PARAM: {"initial": 350.0, "min": 250, "max": 450, "type": "float"}
    demand_forecast = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 90, "max": 130, "type": "float"}
    pipeline_coverage_factor = 0.9000000000000457  # OPT_PARAM: {"initial": 0.9000000000000457, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.29999999999995436  # OPT_PARAM: {"initial": 0.29999999999995436, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 20, "max": 100, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_forecast * lead_time

    # Calculate pipeline coverage ratio
    pipeline_coverage = sum(pipeline_orders) / max(1, expected_demand_during_lead_time)

    # Adjust base stock based on pipeline coverage
    adjusted_base_stock = base_stock * (1 - pipeline_coverage_factor * min(1, pipeline_coverage))

    # Add safety stock
    target_inventory_position = adjusted_base_stock + safety_stock

    # Calculate base order
    base_order = max(0, target_inventory_position - inventory_position)

    # Smooth with demand forecast
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative and integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
