# policy_hash: ce89399813d0c0fd6b7666447526c06081eac1e4519c07f4066de1df851e84f9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1535.36
# best_prompt_performance: 1535.36
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_230344.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 246.76002953294065  # OPT_PARAM: {"initial": 246.76002953294065, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.32799266753707  # OPT_PARAM: {"initial": 20.32799266753707, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 70.32799266753705  # OPT_PARAM: {"initial": 70.32799266753705, "min": 50, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand coverage
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_estimate * lead_time

    # Adjust base stock based on pipeline status
    # Give more weight to incoming orders that arrive sooner
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = (lead_time - i) / lead_time  # Higher weight for orders arriving sooner
        weighted_pipeline += order * weight

    # Calculate target inventory position
    target = base_stock + safety_stock + expected_demand_during_lead_time - 0.3 * weighted_pipeline

    # Calculate order amount
    order_amount = max(0, target - inventory_position)

    # Round to nearest integer since order amount should be integer
    order_amount = int(round(order_amount))

    return order_amount
