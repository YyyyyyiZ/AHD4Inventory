# policy_hash: 50e340ebad0765ae989e2c05dcaeaba83392099103d0d08555ac95f7db948ec0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 740.09
# best_prompt_performance: 739.97
# best_rel_error_pct: 0.016214
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_080945.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.480126482879  # OPT_PARAM: {"initial": 449.480126482879, "min": 400, "max": 550, "type": "float"}
    safety_stock = 75.0  # OPT_PARAM: {"initial": 75.0, "min": 40, "max": 100, "type": "float"}
    demand_forecast = 95.74354041851063  # OPT_PARAM: {"initial": 95.74354041851063, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    lead_time = 4

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus one period
    expected_lead_time_demand = (lead_time + 1) * demand_forecast

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Use the minimum of base_stock and target_position to balance costs
    order_up_to = min(base_stock, target_position)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing more consistently
    if raw_order > 0:
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
