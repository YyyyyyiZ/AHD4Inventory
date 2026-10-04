# policy_hash: e252b8697d3808a6d45389c59ebfff7e4519a7b391b8d6dfc66a4816e787662d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 3908.96
# best_prompt_performance: 3909.62
# best_rel_error_pct: 0.016884
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_004145.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 300, "max": 600, "type": "float"}
    demand_forecast = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 150, "type": "float"}
    pipeline_coverage_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_forecast * lead_time

    # Adjust base stock based on pipeline coverage
    # If pipeline already covers significant demand, reduce order
    pipeline_coverage = sum(pipeline_orders) / max(1, expected_demand_during_lead_time)
    adjusted_base_stock = base_stock * (1 - pipeline_coverage_factor * min(1, pipeline_coverage))

    # Calculate base order
    base_order = max(0, adjusted_base_stock - inventory_position)

    # Smooth with demand forecast
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative and integer
    order_amount = max(0, int(round(order_amount)))

    return order_amount
