# policy_hash: 8238ace20b55c50fef3c821a4a823cfc59c2ff726d0e5ba148dd1c00119682cc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 39
# source_prompt_files: 1
# best_target_performance: 1124.11
# best_prompt_performance: 1124.11
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_231431.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 502.9988103123368  # OPT_PARAM: {"initial": 502.9988103123368, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 103.57514896634329  # OPT_PARAM: {"initial": 103.57514896634329, "min": 50, "max": 150, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Cap order amount to avoid excessive ordering
    max_order = 99.42114235260455  # OPT_PARAM: {"initial": 99.42114235260455, "min": 50, "max": 500, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
